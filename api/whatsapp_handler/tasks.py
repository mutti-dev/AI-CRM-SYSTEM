from celery import shared_task
from .whatsapp_integration.whatsapp_client import WhatsAppClient
from .models import WhatsAppMessage, WhatsAppReply
import logging

logger = logging.getLogger(__name__)
whatsapp_client = WhatsAppClient()

@shared_task
def fetch_whatsapp_messages_task():
    logger.info("Fetching WhatsApp messages...")
    messages = whatsapp_client.fetch_all_messages()
    for message in messages:
        # Process each message (e.g., save to DB, send auto-reply)
        logger.info(f"Processing WhatsApp message: {message['content']}")
    return f"Fetched {len(messages)} WhatsApp messages."
