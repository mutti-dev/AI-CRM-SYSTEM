import logging
import re
from django.utils.timezone import now
from ..models import EmailQuery, EmailReply, Customer, EmailAttachment,EmailLog
from ai_integration.chat_history import client, MODEL_NAME
from ai_integration.prompts import generate_email_reply_prompt
from integrations.email_integration.gmail_client import GmailClient
from integrations.email_integration.outlook_client import OutlookClient

gmail_client = GmailClient()
outlook_client = OutlookClient()
logger = logging.getLogger(__name__)


def extract_email_from_markdown(markdown_email):
    """
    Extracts email address from markdown format: [email](mailto:email)
    """
    if not isinstance(markdown_email, str):
        return None
    match = re.match(r'\[([^\]]+)\]\(mailto:[^\)]+\)', markdown_email)
    if match:
        return match.group(1)
    return markdown_email  # fallback if not markdown format



def extract_sender(sender_str):
    match = re.search(r'<(.*?)>', sender_str)
    return match.group(1) if match else sender_str.strip()






def process_gmail_emails(emails):
    valid_emails = []
    count = 0

    for email in emails:
        if 'threadId' not in email:
            logging.error("Missing 'threadId' in email: %s", email)
            continue

        email['source'] = 'via gmail'

        sender_email = extract_sender(email.get('sender'))
        customer = Customer.objects.filter(email=sender_email).first()
        if not customer:
            continue

        existing_query = EmailQuery.objects.filter(gmail_thread_id=email['threadId']).first()
        if existing_query:
            continue

        email_query = EmailQuery.objects.create(
            customer=customer,
            subject=email.get('subject', 'No Subject'),
            content=email.get('body', ''),
            received_at=now(),
            gmail_thread_id=email['threadId'],
            email_source=email['source']
        )

        print(email_query)

        for attachment in email.get('attachments', []):
            EmailAttachment.objects.create(
                email_query=email_query,
                filename=attachment['filename'],
                mime_type=attachment['mimeType'],
                size=attachment['size'],
                download_url=attachment['download_url']
            )

        count += 1

        valid_emails.append(email)

        try:
            send_ai_reply(email, customer, email_query, thread_id=email['threadId'], source='gmail')
        except Exception as e:
            logging.error("Gmail AI Reply Failed: %s", e)

    return count, valid_emails








def process_outlook_emails(emails):
    valid_emails = []
    count = 0


    for email in emails:
        if not isinstance(email, dict):
            logging.warning(f"Invalid email format: {email}")
            continue

        email['source'] = 'via outlook'

        raw_sender = email.get('sender', '')
        sender_email = extract_email_from_markdown(raw_sender)

        if not sender_email:
            continue

        customer = Customer.objects.filter(email=sender_email).first()
        if not customer:
            continue

        # Avoid duplicates
        existing_query = EmailQuery.objects.filter(outlook_message_id=email.get('id')).first()
        if existing_query:
            continue

        email_query = EmailQuery.objects.create(
            customer=customer,
            subject=email.get('subject', 'No Subject'),
            content=email.get("bodyPreview", "No Preview"),
            received_at=email.get('receivedDateTime'),
            outlook_message_id=email.get('id'),
            email_source=email['source']
        )



        count += 1

        valid_emails.append(email)

        try:
            send_ai_reply(email, customer, email_query, thread_id=email.get('id'), source='outlook')
        except Exception as e:
            logging.error("Outlook AI Reply Failed: %s", e)

    return count, valid_emails





def send_ai_reply(email, customer, email_query, thread_id, source):
    try:
        previous_emails = EmailQuery.objects.filter(
            **{f'{source}_message_id': thread_id}
        ).values_list('content', flat=True)

        thread_context = "\n\n".join(previous_emails)
        prompt = generate_email_reply_prompt(thread_context, email.get('body', ''), customer.name)

        messages = [
            {"role": "system", "content": "You are an AI assistant helping with email replies."},
            {"role": "user", "content": prompt}
        ]
        response = client.chat.completions.create(model=MODEL_NAME, messages=messages)
        reply_content = response.choices[0].message.content.strip()

        # Send reply and record message_id based on source
        if source == 'gmail':
            gmail_message_id = gmail_client.send_reply(
                to_email=customer.email,
                subject=f"Re: {email.get('subject', 'No Subject')}",
                body=reply_content,
                thread_id=thread_id
            )
            EmailReply.objects.create(
                email_query=email_query,
                content=reply_content,
                sent_at=now(),
                # gmail_message_id=gmail_message_id,
                source='gmail',
            )



        elif source == 'outlook':
            outlook_message_id = outlook_client.send_email(
                subject=f"Re: {email.get('subject', 'No Subject')}",
                body=reply_content,
                to_emails=[customer.email],
            )
            outlook_client.mark_email_as_read(email_query.outlook_message_id)
            EmailReply.objects.create(
                email_query=email_query,
                content=reply_content,
                sent_at=now(),
                # outlook_message_id=outlook_message_id,
                source='outlook'
            )



        # ✅ Mark as replied
        email_query.is_replied = True
        email_query.save()

        # ✅ Log success
        EmailLog.objects.create(
            email_query=email_query,
            action='Replied',
            message='AI reply sent successfully.'
        )

    except Exception as e:
        # ❌ Log failure
        EmailLog.objects.create(
            email_query=email_query if 'email_query' in locals() else None,
            action='Failed',
            message=f"Error in send_ai_reply: {str(e)}"
        )
        raise  # Optional: you can log and continue instead of raising
