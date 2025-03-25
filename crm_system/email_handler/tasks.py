from celery import shared_task
from .gmail_integration.gmail_client import GmailClient
from email_handler.models import EmailQuery, Customer

@shared_task
def fetch_and_process_emails():
    gmail = GmailClient()
    emails = gmail.fetch_unread_emails()

    for email in emails:
        customer, created = Customer.objects.get_or_create(
            email=email['sender'],
            defaults={'name': email['sender'].split('@')[0]}
        )

        query, created = EmailQuery.objects.get_or_create(
            customer=customer,
            subject=email['subject'],
            content=email['body'],
            received_at=email['date'],
            gmail_thread_id=email['threadId']
        )
        
        # Process query logic (NLP or keyword matching)
        # Assign tasks or reply automatically as per your logic
