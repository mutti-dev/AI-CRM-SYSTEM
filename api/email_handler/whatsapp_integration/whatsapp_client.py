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
WAAPI_API_KEY = os.getenv("WAAPI_API_KEY")

if not WAAPI_API_KEY:
    raise ValueError("WAAPI_API_KEY environment variable is not set.")

class WhatsAppClient:
    def __init__(self):
        self.api_key = settings.WAAPI_API_KEY
        self.base_url = settings.WAAPI_BASE_URL
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        self.session = requests.Session()
        
        # Configure SSL verification and retry strategy
        self.session.verify = settings.WAAPI_SSL_VERIFY
        retry_strategy = urllib3.Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[408, 429, 500, 502, 503, 504],
        )
        adapter = requests.adapters.HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("https://", adapter)

    def fetch_unread_messages(self):
        try:
            logger.debug("Attempting to fetch unread WhatsApp messages")
            response = self.session.get(
                f"{self.base_url}/messages/unread",
                headers=self.headers,
                timeout=30
            )
            
            # Log the response for debugging
            logger.debug(f"WhatsApp API Response Status: {response.status_code}")
            logger.debug(f"WhatsApp API Response: {response.text[:500]}...")  # Log first 500 chars
            
            response.raise_for_status()
            data = response.json()
            
            if not isinstance(data.get('messages', []), list):
                logger.error("Invalid response format from WhatsApp API")
                return []
                
            return data['messages']
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {str(e)}")
            return []
        except Exception as e:
            logger.error(f"Error fetching unread WhatsApp messages: {str(e)}")
            return []

    def send_reply(self, to_number, message, thread_id=None):
        try:
            payload = {
                "to": to_number,
                "message": message,
                "thread_id": thread_id
            }
            response = self.session.post(
                f"{self.base_url}/messages/send",
                headers=self.headers,
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error sending WhatsApp reply: {e}")
            return None

    def get_thread(self, thread_id):
        try:
            response = self.session.get(
                f"{self.base_url}/messages/thread/{thread_id}",
                headers=self.headers,
                timeout=30
            )
            response.raise_for_status()
            return response.json()['messages']
        except Exception as e:
            logger.error(f"Error fetching WhatsApp thread: {e}")
            return []

    def __del__(self):
        self.session.close()
