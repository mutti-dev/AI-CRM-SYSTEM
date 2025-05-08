from celery import shared_task
from .email_integration.gmail_client import GmailClient
from .models import EmailQuery, EmailReply, EmailLog
import logging

logger = logging.getLogger(__name__)
gmail_client = GmailClient()

@shared_task
def fetch_unread_emails_task():
    logger.info("Fetching unread emails...")
    emails = gmail_client.fetch_unread_emails()
    for email in emails:
        # Process each email (e.g., save to DB, send auto-reply)
        logger.info(f"Processing email: {email['subject']}")
    return f"Fetched {len(emails)} unread emails."


