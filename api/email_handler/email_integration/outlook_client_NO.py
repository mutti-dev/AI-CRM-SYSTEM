import os
import requests
import logging
from email_handler.models import Customer
from dotenv import load_dotenv

load_dotenv()


# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

class OutlookClient:
    def __init__(self, client_id, client_secret, tenant_id, token_file='outlook_token.json'):
        self.client_id = os.getenv("CLIENT_ID")
        self.client_secret = os.getenv("CLIENT_SECRET_ID")
        self.tenant_id = os.getenv("TENANT_ID")
        self.token_file = token_file
        self.base_url = "https://graph.microsoft.com/v1.0"
        self.token = self.authenticate_outlook()

    def authenticate_outlook(self):
        logging.debug("Authenticating Outlook API...")
        token_url = f"https://login.microsoftonline.com/{self.tenant_id}/oauth2/v2.0/token"
        data = {
            'client_id': self.client_id,
            'scope': 'https://graph.microsoft.com/.default',
            'client_secret': self.client_secret,
            'grant_type': 'client_credentials'
        }
        try:
            response = requests.post(token_url, data=data)
            response.raise_for_status()
            token_data = response.json()
            logging.debug("Outlook API authenticated successfully.")
            return token_data['access_token']
        except Exception as e:
            logging.error("Error authenticating Outlook API: %s", e)
            raise

    def fetch_unread_emails(self):
        logging.debug("Fetching unread emails from Outlook...")
        try:
            headers = {'Authorization': f'Bearer {self.token}'}
            response = requests.get(f"{self.base_url}/me/mailFolders/inbox/messages?$filter=isRead eq false", headers=headers)
            response.raise_for_status()
            messages = response.json().get('value', [])
            logging.debug("Found %d unread emails in Outlook.", len(messages))

            emails = []
            for msg in messages:
                sender_email = msg['from']['emailAddress']['address']
                logging.debug("Extracted sender email: %s", sender_email)

                # Check if the sender exists in the Customer table
                if Customer.objects.filter(email=sender_email).exists():
                    email_data = {
                        'id': msg['id'],
                        'subject': msg.get('subject', ''),
                        'sender': sender_email,
                        'date': msg.get('receivedDateTime', ''),
                        'body': msg.get('body', {}).get('content', '').strip()
                    }
                    emails.append(email_data)

                    # Mark email as read after fetching
                    self.mark_email_as_read(msg['id'])

            return emails
        except Exception as e:
            logging.error("Error fetching emails from Outlook: %s", e)
            return []

    def mark_email_as_read(self, email_id):
        logging.debug("Marking email with ID %s as read in Outlook...", email_id)
        try:
            headers = {'Authorization': f'Bearer {self.token}', 'Content-Type': 'application/json'}
            data = {'isRead': True}
            response = requests.patch(f"{self.base_url}/me/messages/{email_id}", headers=headers, json=data)
            response.raise_for_status()
            logging.debug("Email with ID %s marked as read.", email_id)
        except Exception as e:
            logging.error("Error marking email as read in Outlook: %s", e)

if __name__ == "__main__":
    logging.info("Starting OutlookClient test...")
    outlook_client = OutlookClient(
        client_id="your_client_id",
        client_secret="your_client_secret",
        tenant_id="your_tenant_id"
    )

    # Test fetching unread emails
    logging.info("Fetching unread emails from Outlook...")
    emails = outlook_client.fetch_unread_emails()
    logging.info("Fetched %d emails from Outlook.", len(emails))
    for email in emails:
        logging.info("Email: %s", email)
