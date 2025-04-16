import os
import requests
import logging
import urllib3
from django.conf import settings
from datetime import datetime
from dotenv import load_dotenv

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

load_dotenv()

# Suppress SSL verification warnings when WAAPI_SSL_VERIFY is False
if not settings.WAAPI_SSL_VERIFY:
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class WhatsAppClient:
    def __init__(self):
        self.instance_id = "59949"  # Your instance ID
        self.api_key = os.getenv('WAAPI_API_KEY')
        if not self.api_key:
            raise ValueError("WAAPI_API_KEY environment variable is not set")

        self.base_url = f"https://waapi.app/api/v1/instances/{self.instance_id}"
        self.verify_ssl = settings.WAAPI_SSL_VERIFY
        self.timeout = getattr(settings, 'WAAPI_TIMEOUT', 20)

        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

        # Setup session with retries, headers, and SSL config
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        self.session.verify = self.verify_ssl

        retry_strategy = urllib3.Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[408, 429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "POST"]
        )
        adapter = requests.adapters.HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("https://", adapter)

        logger.info("WhatsApp client initialized")
        logger.debug(f"Using API base URL: {self.base_url}")

    def _format_phone_number(self, phone_number):
        """Format phone number to WhatsApp chat ID format"""
        clean_number = ''.join(filter(lambda x: x.isdigit() or x == '+', phone_number))
        clean_number = clean_number.replace('+', '') + '@c.us'
        return clean_number

    def fetch_test_message(self):
        """Generate a test message for verification"""
        test_message = {
            'id': 'test_msg_123',
            'from': '923423311653',  # Test phone number
            'content': 'This is a test WhatsApp message',
            'thread_id': 'test_thread_123',
            'timestamp': datetime.now().isoformat()
        }
        logger.info(f"Generated test message: {test_message}")
        return [test_message]

    def fetch_unread_chats(self):
        """Fetch chats (threads) with unread messages"""
        try:
            response = self.session.post(
                f"{self.base_url}/client/action/get-chats",
                timeout=self.timeout
            )
            response.raise_for_status()
            try:
                data = response.json()
            except Exception as je:
                logger.error(f"Response is not JSON: {response.text}")
                return []
            
            # If response is not dict, log and return []
            if not isinstance(data, dict):
                logger.error(f"Unexpected response format: {data}")
                return []
            
            # Optionally: print for debugging
            if settings.DEBUG:
                logger.debug(f"get-chats WAAPI response: {data}")

            chats_data = data.get('data', [])
            # If chats_data isn't a list, warn and return
            if not isinstance(chats_data, list):
                logger.error(f"get-chats WAAPI 'data' is not a list: {chats_data}")
                return []

            unread_chats = [chat for chat in chats_data if isinstance(chat, dict) and chat.get('unreadCount', 0) > 0]
            return unread_chats
        except Exception as e:
            logger.error(f"Failed to fetch chats: {e}")
            return []

    def fetch_unread_messages(self):
        """
        Fetch all unread messages from chats with unread messages.
        Returns: list of message data dicts.
        """
        unread_chats = self.fetch_unread_chats()
        all_unread_messages = []

        for chat in unread_chats:
            chat_id = chat.get('id')
            unread_count = chat.get('unreadCount', 0)

            if chat_id and unread_count > 0:
                try:
                    res = self.session.post(
                        f"{self.base_url}/client/action/get-messages",
                        json={"chatId": chat_id},
                        timeout=self.timeout
                    )
                    res.raise_for_status()
                    messages = res.json().get('data', [])

                    # Most recent messages are at the end; get the unread ones
                    unread_msgs = [m for m in messages if not m.get('isRead', False)]
                    if not unread_msgs and unread_count <= len(messages):
                        # If there's no isRead property, assume last `unread_count` messages are unread
                        unread_msgs = messages[-unread_count:]
                    all_unread_messages.extend(unread_msgs)

                except Exception as ex:
                    logger.error(f"Error fetching messages for chat {chat_id}: {ex}")
                    continue
        return all_unread_messages

    def send_reply(self, to_number, message, thread_id=None, preview_link=True):
        """
        Send a reply message via WhatsApp (WAAPI).
        :param to_number: String, phone number, with or without "+".
        :param message: String, the message text.
        :param thread_id: String, message id to reply to (optional).
        :param preview_link: Boolean, whether to show link previews (default True).
        :return: dict of message id and status or None.
        """
        try:
            chat_id = self._format_phone_number(to_number)
            payload = {
                "chatId": chat_id,
                "message": message,
                "previewUrl": preview_link
            }
            if thread_id:
                payload["replyToMessageId"] = thread_id

            logger.debug(f"Sending message: {payload}")
            response = self.session.post(
                f"{self.base_url}/client/action/send-message",
                json=payload,
                timeout=self.timeout
            )
            response.raise_for_status()
            result = response.json()
            if result.get('status') == 'success':
                return {
                    'message_id': result.get('data', {}).get('_data', {}).get('id', {}).get('_serialized'),
                    'status': 'sent'
                }
            else:
                logger.error(f"Failed to send message: {result}")
                return None

        except Exception as e:
            logger.error(f"Error sending WhatsApp reply: {e}")
            return None

    def get_thread(self, thread_id):
        """Fetches all messages for a given chat/thread (by chatId)."""
        try:
            payload = {"chatId": thread_id}
            response = self.session.post(
                f"{self.base_url}/client/action/get-messages",
                json=payload,
                timeout=self.timeout
            )
            response.raise_for_status()
            result = response.json()
            if result.get('status') == 'success':
                return result.get('data', [])
            return []
        except Exception as e:
            logger.error(f"Error fetching thread: {e}")
            return []

    def __del__(self):
        try:
            self.session.close()
        except Exception:
            pass  # Protect from __del__ exceptions