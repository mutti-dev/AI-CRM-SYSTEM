from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET
from django.shortcuts import get_object_or_404
from django.utils.timezone import now
from ..models import EmailQuery, EmailReply, EmailLog, FAQ, Customer, EmailAttachment
from ..email_integration.gmail_client import GmailClient
from ..ai.chat_history import client, MODEL_NAME  # Updated import for AI responses
from ..prompts import generate_email_reply_prompt
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
            # logging.debug("Processing email: %s", email)

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

            # logging.debug("Extracted sender email: %s", sender_email)

            # Check if the sender exists in the Customer table
            customer = Customer.objects.filter(email=sender_email).first()
            if customer:
                # Check if the email thread already exists
                existing_query = EmailQuery.objects.filter(gmail_thread_id=email['threadId']).first()
                if existing_query:
                    logging.info("Email thread already exists: %s", email['threadId'])
                    continue  # Skip creating a new EmailQuery

                # Create a new EmailQuery
                email_query = EmailQuery.objects.create(
                    customer=customer,
                    subject=email.get('subject', 'No Subject'),
                    content=email.get('body', ''),
                    received_at=now(),
                    gmail_thread_id=email['threadId']
                )

                # Save attachments in the database
                for attachment in email.get('attachments', []):
                    EmailAttachment.objects.create(
                        email_query=email_query,
                        filename=attachment['filename'],
                        mime_type=attachment['mimeType'],
                        size=attachment['size'],
                        download_url=attachment['download_url']
                    )

                emails_fetched += 1
                valid_emails.append(email)

                # Automatically send a reply using GenAI
                try:
                    # Fetch previous email content in the thread for context
                    previous_emails = EmailQuery.objects.filter(gmail_thread_id=email['threadId']).values_list('content', flat=True)
                    thread_context = "\n\n".join(previous_emails)
                    prompt = generate_email_reply_prompt(thread_context, email.get('body', ''), customer.name)
                    
                    # Use the correct 'messages' format for the OpenAI client
                    messages = [
                        {"role": "system", "content": "You are an AI assistant helping with email replies."},
                        {"role": "user", "content": prompt}
                    ]
                    response = client.chat.completions.create(
                        model=MODEL_NAME,
                        messages=messages
                    )
                    # Correctly access the content of the response
                    reply_content = response.choices[0].message.content.strip()

                    logging.debug("Generated reply content: %s", reply_content)

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
                # logging.debug("Sender not found in Customer table: %s", sender_email)
                print("Not found email")

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
                    prompt = generate_email_reply_prompt(query.content, "")
                    response = client.models.generate_content(
                        model=MODEL_NAME,
                        contents=prompt
                    )
                    reply_content = response.text.strip()

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
                'thread_messages': thread_messages,
                'attachments': [
                    {
                        'filename': attachment.get('filename'),
                        'mimeType': attachment.get('mimeType'),
                        'size': attachment.get('size'),
                        'download_url': attachment.get('download_url')
                    }
                    for attachment in thread_messages[-1].get('attachments', [])
                ] if thread_messages else []
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

@require_GET
def download_attachment(request, email_id, attachment_id):
    try:
        # Fetch the attachment data from Gmail
        attachment_data = gmail_client.get_attachment(email_id, attachment_id)
        if not attachment_data:
            return JsonResponse({'error': 'Attachment not found'}, status=404)

        # Prepare the response
        response = HttpResponse(attachment_data['data'], content_type=attachment_data['mimeType'])
        response['Content-Disposition'] = f'attachment; filename="{attachment_data["filename"]}"'
        return response
    except Exception as e:
        logging.error(f"Error downloading attachment {attachment_id} for email {email_id}: {e}")
        return JsonResponse({'error': 'Failed to download attachment'}, status=500)