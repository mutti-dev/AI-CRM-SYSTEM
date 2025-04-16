from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import get_object_or_404
from django.utils.timezone import now
from ..models import EmailQuery, EmailReply, EmailLog, FAQ, Customer
from ..gmail_integration.gmail_client import GmailClient
from ..genai import client
import json
import logging
import re

gmail_client = GmailClient()
logger = logging.getLogger(__name__)

@csrf_exempt
def fetch_unread_emails(request):
    if request.method == 'POST':
        emails = gmail_client.fetch_unread_emails()
        emails_fetched = 0
        valid_emails = []

        for email in emails:
            logging.debug("Processing email: %s", email)

            if 'threadId' not in email:
                logging.error("Missing 'threadId' in email: %s", email)
                continue

            # Extract the email address from the sender field
            sender_email = email.get('sender')
            match = re.search(r'<(.*?)>', sender_email)
            if match:
                sender_email = match.group(1)
            else:
                sender_email = sender_email.strip()

            logging.debug("Extracted sender email: %s", sender_email)

            # Check if the sender exists in the Customer table
            customer = Customer.objects.filter(email=sender_email).first()
            if customer:
                # Check if the email thread already exists
                existing_query = EmailQuery.objects.filter(gmail_thread_id=email['threadId']).first()
                if existing_query:
                    logging.info("Email thread already exists: %s", email['threadId'])
                    continue

                # Create a new EmailQuery
                EmailQuery.objects.create(
                    customer=customer,
                    subject=email.get('subject', 'No Subject'),
                    content=email.get('body', ''),
                    received_at=now(),
                    gmail_thread_id=email['threadId']
                )
                emails_fetched += 1
                valid_emails.append(email)

                # Automatically send a reply using GenAI
                try:
                    # Fetch previous email content in the thread for context
                    previous_emails = EmailQuery.objects.filter(gmail_thread_id=email['threadId']).values_list('content', flat=True)
                    thread_context = "\n\n".join(previous_emails)

                    # Generate a professional and friendly reply using GenAI
                    response = client.models.generate_content(
                        model="gemini-2.0-flash",
                        contents=f"""
                        You are AI Mutti, a friendly and professional assistant from MaxRemind. 
                        Your job is to generate well-written, polite, and helpful email replies.
                        Respond to the following email in a clear, concise, and respectful tone. 
                        Keep the language simple, professional, and approachable—neither too formal nor too casual. 
                        Always make the sender feel acknowledged, understood, and supported.
                        Make sure the reply sounds human, empathetic, and solution-oriented. 
                        Avoid robotic phrasing or overly complex language.
                        Here is the email thread context:
                        \"\"\"{thread_context}\"\"\" 
                        Here is the latest email content:
                        \"\"\"{email.get('body', '')}\"\"\" 
                        Write a well-formatted and thoughtful reply:
                        """
                    )
                    reply_content = response.text

                    gmail_message_id = gmail_client.send_reply(
                        to_email=sender_email,
                        subject=f"Re: {email.get('subject', 'No Subject')}",
                        body=reply_content,
                        thread_id=email['threadId']
                    )
                    logging.info("Auto-reply sent for email: %s", email['threadId'])

                    # Save the reply in EmailReply
                    EmailReply.objects.create(
                        email_query=EmailQuery.objects.get(gmail_thread_id=email['threadId']),
                        content=reply_content,
                        sent_at=now(),
                        gmail_message_id=gmail_message_id
                    )
                except Exception as e:
                    logging.error("Failed to send auto-reply for email %s: %s", email['threadId'], e)
            else:
                logging.debug("Sender not found in Customer table: %s", sender_email)

        return JsonResponse({
            'status': 'success',
            'emails_fetched': emails_fetched,
            'total_unread_emails_fetched': len(valid_emails),
            'emails': valid_emails
        })
    return JsonResponse({'error': 'Invalid request method'}, status=400)

@csrf_exempt
def process_queries(request):
    if request.method == 'POST':
        queries = EmailQuery.objects.filter(is_replied=False)
        processed_queries = []

        # Fetch predefined company information (FAQs or other data)
        company_info = FAQ.objects.values_list('keywords', 'answer')

        for query in queries:
            try:
                # Check if the query matches any predefined company information
                matched = False
                for keywords, answer in company_info:
                    keyword_list = [kw.strip().lower() for kw in keywords.split(',')]
                    if any(kw in query.content.lower() for kw in keyword_list):
                        # If a match is found, use the predefined answer
                        reply_content = answer
                        matched = True
                        break

                if not matched:
                    reply_content = (
                        "Thank you for reaching out to us. "
                        "We have received your query and will get back to you shortly."
                    )

                # Send the reply via Gmail
                gmail_message_id = gmail_client.send_reply(
                    to_email=query.customer.email,
                    subject=f"Re: {query.subject}",
                    body=reply_content,
                    thread_id=query.gmail_thread_id
                )

                # Save the reply in the database
                EmailReply.objects.create(
                    email_query=query,
                    content=reply_content,
                    sent_at=now(),
                    gmail_message_id=gmail_message_id
                )

                query.is_replied = True
                query.save()

                processed_queries.append({
                    'id': query.id,
                    'subject': query.subject,
                    'is_replied': query.is_replied,
                })
            except Exception as e:
                logger.error(f"Error processing query {query.id}: {e}")

        return JsonResponse({'status': 'success', 'processed_queries': processed_queries})
    return JsonResponse({'error': 'Invalid request method'}, status=400)

@csrf_exempt
def fetch_unread_emails_from_db(request):
    if request.method == 'GET':
        unread_emails = EmailQuery.objects.filter(is_replied=False).values(
            'id', 
            'subject', 
            'customer__email', 
            'customer__name',
            'received_at'
        )
        return JsonResponse({'status': 'success', 'emails': list(unread_emails)})
    return JsonResponse({'error': 'Invalid request method'}, status=400)

@csrf_exempt
def reply_to_email(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            email_query = get_object_or_404(EmailQuery, id=data['email_query_id'])
            reply_content = data['content'].strip()
            message_id = data.get('message_id')
            
            if not reply_content:
                return JsonResponse({'error': 'Reply content cannot be empty'}, status=400)

            # Add email signature and format content
            formatted_content = f"{reply_content}\n\nBest regards,\nMaxRemind Team"
            
            # Retry mechanism for Gmail API
            max_retries = 3
            retry_count = 0
            while retry_count < max_retries:
                try:
                    gmail_message_id = gmail_client.reply_to_thread(
                        to_email=email_query.customer.email,
                        subject=f"Re: {email_query.subject}",
                        body=formatted_content,
                        thread_id=email_query.gmail_thread_id,
                        message_id=message_id
                    )
                    
                    if gmail_message_id:
                        break
                    retry_count += 1
                except Exception as e:
                    logging.error(f"Retry {retry_count + 1} failed: {str(e)}")
                    retry_count += 1
                    if retry_count == max_retries:
                        raise

            if not gmail_message_id:
                raise Exception("Failed to send email after multiple retries")

            reply = EmailReply.objects.create(
                email_query=email_query,
                content=formatted_content,
                sent_at=now(),
                gmail_message_id=gmail_message_id
            )
            
            email_query.is_replied = True
            email_query.save()
            
            # Create success log
            EmailLog.objects.create(
                email_query=email_query,
                action='Replied',
                message=f"Reply sent successfully. Message ID: {gmail_message_id}"
            )
            
            return JsonResponse({
                'status': 'success',
                'reply': {
                    'id': reply.id,
                    'content': reply.content,
                    'sent_at': reply.sent_at.isoformat(),
                    'gmail_message_id': gmail_message_id
                }
            })
            
        except Exception as e:
            logging.error(f"Error sending reply: {str(e)}")
            # Create error log
            EmailLog.objects.create(
                email_query=email_query if 'email_query' in locals() else None,
                action='Failed',
                message=f"Reply failed: {str(e)}"
            )
            return JsonResponse({
                'status': 'error',
                'message': 'Failed to send reply. Please try again.',
                'error': str(e)
            }, status=500)
    
    return JsonResponse({'error': 'Invalid request method'}, status=400)

@csrf_exempt
def fetch_email_details(request, id):
    if request.method == 'GET':
        try:
            email = EmailQuery.objects.get(id=id)
            # Fetch the complete thread from Gmail
            thread_messages = gmail_client.get_thread(email.gmail_thread_id)
            
            email_details = {
                'id': email.id,
                'subject': email.subject,
                'sender': email.customer.email,
                'body': email.content,
                'received_at': email.received_at,
                'thread_id': email.gmail_thread_id,
                'thread_messages': thread_messages
            }
            return JsonResponse({'status': 'success', 'email': email_details})
        except EmailQuery.DoesNotExist:
            return JsonResponse({'error': 'Email not found'}, status=404)
    return JsonResponse({'error': 'Invalid request method'}, status=400)

@csrf_exempt
def fetch_email_replies(request, id):
    if request.method == 'GET':
        try:
            email_query = EmailQuery.objects.get(id=id)
            replies = EmailReply.objects.filter(email_query=email_query).values('id', 'content', 'sent_at')
            return JsonResponse({'status': 'success', 'replies': list(replies)})
        except EmailQuery.DoesNotExist:
            return JsonResponse({'error': 'Email not found'}, status=404)
    return JsonResponse({'error': 'Invalid request method'}, status=400)