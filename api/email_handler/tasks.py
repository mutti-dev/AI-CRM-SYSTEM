from celery import shared_task
from celery import Celery
from .gmail_integration.gmail_client import GmailClient
from email_handler.models import EmailQuery, Customerfrom django.utils.timezone import now
ng
@shared_task
def fetch_and_process_emails():t()
    gmail = GmailClient()
    emails = gmail.fetch_unread_emails()@shared_task
task():
    for email in emails:
        customer, created = Customer.objects.get_or_create(read_emails()
            email=email['sender'],
            defaults={'name': email['sender'].split('@')[0]}
        )    for email in emails:

        query, created = EmailQuery.objects.get_or_create(sing 'threadId' in email: %s", email)
            customer=customer,
            subject=email['subject'],
            content=email['body'],er(gmail_thread_id=email['threadId']).exists():
            received_at=email['date'],t_or_create(email=email.get('sender', 'unknown@example.com'))
            gmail_thread_id=email['threadId']   EmailQuery.objects.create(
                customer=customer,)
        t'),
        # Process query logic (NLP or keyword matching)
                received_at=now(),        # Assign tasks or reply automatically as per your logic







    return emails_fetched    logging.info(f"Fetched {emails_fetched} new emails.")            emails_fetched += 1            )                gmail_thread_id=email['threadId']