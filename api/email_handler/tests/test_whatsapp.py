import unittest
import logging
from django.test import TestCase
from django.urls import reverse
from email_handler.models import Customer, WhatsAppMessage
from email_handler.whatsapp_integration.whatsapp_client import WhatsAppClient
from django.utils import timezone

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class WhatsAppIntegrationTest(TestCase):
    def setUp(self):
        self.whatsapp_client = WhatsAppClient()
        self.test_phone = "+1234567890"  # Replace with your test number
        self.customer = Customer.objects.create(
            phone_number=self.test_phone,
            name="Test Customer",
            preferred_contact='whatsapp'
        )

    def test_fetch_messages(self):
        """Test fetching unread WhatsApp messages"""
        logger.info("Testing fetch_unread_messages...")
        response = self.client.post(reverse('fetch_whatsapp_messages'))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        logger.info(f"Response: {data}")
        self.assertIn('status', data)

    def test_send_reply(self):
        """Test sending a WhatsApp reply"""
        logger.info("Testing send_reply...")
        # Create a test message
        message = WhatsAppMessage.objects.create(
            customer=self.customer,
            content="Test message",
            received_at=timezone.now(),
            thread_id="test_thread",
            whatsapp_message_id="test_id"
        )

        response = self.client.post(
            reverse('reply_to_whatsapp'),
            {
                'message_id': message.id,
                'content': 'Test reply'
            },
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        logger.info(f"Response: {data}")
        self.assertIn('status', data)

if __name__ == '__main__':
    unittest.main()
