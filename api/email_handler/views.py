from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET
from django.shortcuts import get_object_or_404
from django.utils.timezone import now
from .models import EmailQuery, EmailReply, EmailLog, Customer, EmailAttachment
from faqs.models import FAQ
from integrations.email_integration.gmail_client import GmailClient
from integrations.email_integration.outlook_client import OutlookClient
from ai_integration.chat_history import client, MODEL_NAME  # Updated import for AI responses
from ai_integration.prompts import generate_email_reply_prompt
import json
import logging
import re
import base64
import time
import httpx


from .services.email_service import (
    process_gmail_emails,
    process_outlook_emails,
    send_ai_reply,
)

gmail_client = GmailClient()
outlook_client = OutlookClient()


logger = logging.getLogger(__name__)

@csrf_exempt
def fetch_unread_emails(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid request method'}, status=400)

    emails_fetched = 0
    valid_emails = []

    # Process Gmail
    gmail_emails = gmail_client.fetch_unread_emails()
    emails_fetched_gmail, valid_emails_gmail = process_gmail_emails(gmail_emails)
    emails_fetched += emails_fetched_gmail
    valid_emails += valid_emails_gmail

    # Process Outlook
    outlook_emails = outlook_client.fetch_unread_emails()
    emails_fetched_outlook, valid_emails_outlook = process_outlook_emails(outlook_emails)
    emails_fetched += emails_fetched_outlook
    valid_emails += valid_emails_outlook

    # print("Valid Emails=====================================", outlook_emails)

    return JsonResponse({
        'status': 'success',
        'emails_fetched': emails_fetched,
        'total_unread_emails_fetched': len(valid_emails),
        'emails': valid_emails
    })






















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
                    gmail_message_id=gmail_message_id,
                    source= "gmail"
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
            'received_at',
            'source'
        )
        return JsonResponse({'status': 'success', 'emails': list(unread_emails)})
    return JsonResponse({'error': 'Invalid request method'}, status=400)





@csrf_exempt
def reply_to_email(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid request method'}, status=400)

    try:
        data = json.loads(request.body)
        email_query = get_object_or_404(EmailQuery, id=data['email_query_id'])
        reply_content = data['content'].strip()
        message_id = data.get('message_id')
        email_source = email_query.source

        if not reply_content:
            return JsonResponse({'error': 'Reply content cannot be empty'}, status=400)

        # HTML-styled content
        formatted_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta name='viewport' content='width=device-width, initial-scale=1'>
            <style>
                body {{ font-family: 'Segoe UI', system-ui, sans-serif; line-height: 1.6; color: #2d3748; background: #f7fafc; margin: 0; }}
                .header {{ background: #fff; padding: 2rem 1rem; text-align: center; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
                .logo {{ height: 40px; max-width: 240px; }}
                .content {{ max-width: 800px; margin: 2rem auto; padding: 2rem; background: #fff; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }}
                .footer {{ text-align: center; padding: 2rem 1rem; color: #718096; font-size: 0.875rem; border-top: 1px solid #e2e8f0; margin-top: 2rem; }}
            </style>
        </head>
        <body>
            <div class='header'>
                <img src='https://maxremind.com/wp-content/uploads/2024/07/Maxremind-HD-Logo-min-1536x271.png' alt='MaxRemind Logo' class='logo'>
            </div>
            <div class='content'>
                {reply_content}
            </div>
            <div class='footer'>
                © 2024 MaxRemind. All rights reserved.<br>
                <span style='font-size: 0.75rem; color: #a0aec0;'>Need help? Contact our support team</span>
            </div>
        </body>
        </html>
        """

        # Send reply with retry mechanism
        max_retries = 3
        retry_count = 0
        reply = None

        while retry_count < max_retries:
            try:
                if email_source == 'gmail':
                    gmail_msg_id = gmail_client.reply_to_thread(
                        to_email=email_query.customer.email,
                        subject=f"Re: {email_query.subject}",
                        body=formatted_content,
                        thread_id=email_query.gmail_thread_id,
                        message_id=message_id
                    )
                    if not gmail_msg_id:
                        raise Exception("Gmail message ID not returned.")

                    reply = EmailReply.objects.create(
                        email_query=email_query,
                        content=formatted_content,
                        sent_at=now(),
                        gmail_message_id=gmail_msg_id,
                        source='gmail',
                    )
                    break

                elif email_source == 'outlook':
                    outlook_msg_id = outlook_client.send_email(
                        subject=f"Re: {email_query.subject}",
                        to_emails=email_query.customer.email,
                        body=formatted_content,
                        message_id=email_query.outlook_message_id
                    )
                    if not outlook_msg_id:
                        raise Exception("Outlook message ID not returned.")

                    outlook_client.mark_email_as_read(email_query.outlook_message_id)

                    reply = EmailReply.objects.create(
                        email_query=email_query,
                        content=formatted_content,
                        sent_at=now(),
                        outlook_message_id=outlook_msg_id,
                        source='outlook',
                    )
                    break

                else:
                    raise Exception(f"Unsupported email source: {email_source}")

            except Exception as e:
                logging.error(f"[{email_source}] Retry {retry_count + 1} failed: {str(e)}")
                retry_count += 1
                if retry_count == max_retries:
                    raise

        # ✅ Mark as replied
        email_query.is_replied = True
        email_query.save()

        # ✅ Log success
        EmailLog.objects.create(
            email_query=email_query,
            action='Replied',
            message=f"Reply sent successfully via {email_source}."
        )

        return JsonResponse({
            'status': 'success',
            'reply': {
                'id': reply.id,
                'content': reply.content,
                'sent_at': reply.sent_at.isoformat(),
                'message_id': reply.gmail_message_id or reply.outlook_message_id
            }
        })

    except Exception as e:
        logging.error(f"Error sending reply: {str(e)}")
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

        # Encode the attachment data in base64
        base64_data = base64.b64encode(attachment_data['data']).decode('utf-8')

        # Return the base64-encoded data in the JSON response
        return JsonResponse({
            'status': 'success',
            'filename': attachment_data['filename'],
            'mimeType': attachment_data['mimeType'],
            'base64': f"data:{attachment_data['mimeType']};base64,{base64_data}"
        })
    except Exception as e:
        logging.error(f"Error fetching attachment {attachment_id} for email {email_id}: {e}")
        return JsonResponse({'error': 'Failed to fetch attachment'}, status=500)


