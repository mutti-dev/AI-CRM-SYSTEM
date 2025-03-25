import os
import base64
from email.mime.text import MIMEText
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request  # Add this import
from bs4 import BeautifulSoup
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

SCOPES = ['https://www.googleapis.com/auth/gmail.modify']

class GmailClient:
    def __init__(self, creds_file='credentials.json', token_file='token.json'):
        creds_path = os.path.abspath(creds_file)
        logging.debug("Looking for credentials file at: %s", creds_path)
        if not os.path.exists(creds_path):
            logging.error("Credentials file not found at: %s", creds_path)
            raise FileNotFoundError(f"Credentials file not found at: {creds_path}")
        logging.debug("Initializing GmailClient with credentials file: %s and token file: %s", creds_file, token_file)
        self.creds_file = creds_file
        self.token_file = token_file
        self.service = self.authenticate_gmail()

    def authenticate_gmail(self):
        logging.debug("Authenticating Gmail API...")
        creds = None
        if os.path.exists(self.token_file):
            logging.debug("Token file found: %s", self.token_file)
            creds = Credentials.from_authorized_user_file(self.token_file, SCOPES)
        
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                logging.debug("Refreshing expired credentials...")
                creds.refresh(Request())
            else:
                logging.debug("No valid credentials found. Initiating OAuth flow...")
                flow = InstalledAppFlow.from_client_secrets_file(self.creds_file, SCOPES)
                creds = flow.run_local_server(port=0)

            with open(self.token_file, 'w') as token:
                logging.debug("Saving new token to file: %s", self.token_file)
                token.write(creds.to_json())

        service = build('gmail', 'v1', credentials=creds)
        logging.debug("Gmail API authenticated successfully.")
        return service

    def fetch_unread_emails(self):
        logging.debug("Fetching unread emails...")
        try:
            results = self.service.users().messages().list(
                userId='me',
                labelIds=['INBOX'],
                q='is:unread'
            ).execute()

            messages = results.get('messages', [])
            logging.debug("Found %d unread emails.", len(messages))

            emails = []
            for msg in messages:
                email_data = self.get_email(msg['id'])
                emails.append(email_data)

                # Mark email as read after fetching
                self.service.users().messages().modify(
                    userId='me',
                    id=msg['id'],
                    body={'removeLabelIds': ['UNREAD']}
                ).execute()
                logging.debug("Marked email with ID %s as read.", msg['id'])

            return emails

        except Exception as e:
            logging.error("Error fetching emails: %s", e)
            return []

    def get_email(self, msg_id):
        logging.debug("Fetching email with ID: %s", msg_id)
        try:
            msg = self.service.users().messages().get(userId='me', id=msg_id, format='full').execute()
            payload = msg['payload']
            headers = payload['headers']

            subject = sender = date = ''
            for header in headers:
                if header['name'] == 'Subject':
                    subject = header['value']
                elif header['name'] == 'From':
                    sender = header['value']
                elif header['name'] == 'Date':
                    date = header['value']

            parts = payload.get('parts', [])
            body = ""
            if parts:
                body = self._parse_parts(parts)
            else:
                data = payload['body'].get('data', '')
                body = base64.urlsafe_b64decode(data).decode('utf-8')

            # Remove HTML tags if present
            soup = BeautifulSoup(body, "html.parser")
            clean_body = soup.get_text()

            logging.debug("Email fetched successfully: Subject: %s, Sender: %s", subject, sender)
            return {
                'id': msg_id,
                'threadId': msg['threadId'],
                'subject': subject,
                'sender': sender,
                'date': date,
                'body': clean_body.strip()
            }
        except Exception as e:
            logging.error("Error fetching email with ID %s: %s", msg_id, e)
            return {}

    def _parse_parts(self, parts):
        logging.debug("Parsing email parts...")
        body = ""
        for part in parts:
            if part.get('mimeType') == 'text/plain' and part['body'].get('data'):
                body += base64.urlsafe_b64decode(part['body']['data']).decode('utf-8')
            elif part.get('parts'):
                body += self._parse_parts(part.get('parts'))
        return body

    def send_reply(self, to_email, subject, body, thread_id):
        logging.debug("Sending reply to: %s, Subject: %s", to_email, subject)
        try:
            message = MIMEText(body)
            message['to'] = to_email
            message['subject'] = subject

            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()

            message_sent = self.service.users().messages().send(
                userId='me',
                body={
                    'raw': raw_message,
                    'threadId': thread_id
                }
            ).execute()

            logging.info("Reply sent successfully: Gmail Message ID: %s", message_sent['id'])
            return message_sent['id']

        except Exception as e:
            logging.error("Error sending reply: %s", e)
            return None

if __name__ == "__main__":
    logging.info("Starting GmailClient test...")
    gmail_client = GmailClient()

    # Test fetching unread emails
    logging.info("Fetching unread emails...")
    emails = gmail_client.fetch_unread_emails()
    logging.info("Fetched %d emails.", len(emails))
    for email in emails:
        logging.info("Email: %s", email)

    # Uncomment the following lines to test sending a reply
    # if emails:
    #     first_email = emails[0]
    #     logging.info("Sending reply to the first email...")
    #     gmail_client.send_reply(
    #         to_email=first_email['sender'],
    #         subject=f"Re: {first_email['subject']}",
    #         body="This is a test reply.",
    #         thread_id=first_email['threadId']
    #     )

