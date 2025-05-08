import os
import base64
import re  # Add this import for regular expressions
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart  # Add this import for multipart messages
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request  # Add this import
from bs4 import BeautifulSoup
import logging
import json  # Add this import for JSON handling
from email_handler.models import Customer


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

                # Extract the email address from the sender field
                sender_email = email_data.get('sender')
                match = re.search(r'<(.*?)>', sender_email)
                if match:
                    sender_email = match.group(1)
                else:
                    sender_email = sender_email.strip()  # Handle cases where no name is present

                logging.debug("Extracted sender email: %s", sender_email)  # Log the extracted email

                # Check if the sender exists in the Customer table
                if Customer.objects.filter(email=sender_email).exists():
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
                elif header['name'].lower() == 'message-id':
                    message_id = header['value']

            parts = payload.get('parts', [])
            body = ""
            attachments = []
            if parts:
                body, attachments = self._parse_parts_with_attachments(parts, msg_id)
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
                'body': clean_body.strip(),
                'message_id': message_id,
                'attachments': attachments  # Include attachments in the email data
            }
        except Exception as e:
            logging.error("Error fetching email with ID %s: %s", msg_id, e)
            return {}

    def _parse_parts_with_attachments(self, parts, msg_id):
        logging.debug("Parsing email parts with attachments...")
        body = ""
        attachments = []
        for part in parts:
            if part.get('mimeType') == 'text/plain' and part['body'].get('data'):
                body += base64.urlsafe_b64decode(part['body']['data']).decode('utf-8')
            elif part.get('filename'):
                attachment_id = part['body'].get('attachmentId')
                if attachment_id:
                    attachment = self.service.users().messages().attachments().get(
                        userId='me', messageId=msg_id, id=attachment_id
                    ).execute()
                    data = base64.urlsafe_b64decode(attachment['data'])
                    attachments.append({
                        'filename': part['filename'],
                        'mimeType': part['mimeType'],
                        'size': part['body'].get('size'),
                        'download_url': f"/api/download_attachment/{msg_id}/{attachment_id}"
                    })
            elif part.get('parts'):
                sub_body, sub_attachments = self._parse_parts_with_attachments(part.get('parts'), msg_id)
                body += sub_body
                attachments.extend(sub_attachments)
        return body, attachments

    def _parse_parts(self, parts):
        logging.debug("Parsing email parts...")
        body = ""
        for part in parts:
            if part.get('mimeType') == 'text/plain' and part['body'].get('data'):
                body += base64.urlsafe_b64decode(part['body']['data']).decode('utf-8')
            elif part.get('parts'):
                body += self._parse_parts(part.get('parts'))
        return body

    def send_reply(self, to_email, subject, body, thread_id, message_id=None):
        logging.debug("Sending reply to: %s, Subject: %s", to_email, subject)
        try:
            # Create a MIME message
            message = MIMEMultipart("alternative")
            message['to'] = to_email
            message['subject'] = subject

            # Add In-Reply-To and References headers if replying to a specific message
            if message_id:
                message['In-Reply-To'] = message_id
                message['References'] = message_id

            # Attach the HTML body
            message.attach(MIMEText(body, "html"))

            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()

            message_sent = self.service.users().messages().send(
                userId='me',
                body={
                    'raw': raw_message,
                    'threadId': thread_id  # Ensure the reply is sent in the same thread
                }
            ).execute()

            logging.info("Reply sent successfully: Gmail Message ID: %s", message_sent['id'])
            return message_sent['id']

        except Exception as e:
            logging.error("Error sending reply: %s", e)
            return None

    def get_thread(self, thread_id):
        logging.debug("Fetching thread with ID: %s", thread_id)
        try:
            thread = self.service.users().threads().get(userId='me', id=thread_id).execute()
            messages = []
            
            for message in thread['messages']:
                msg_data = self.get_email(message['id'])
                if msg_data:
                    messages.append(msg_data)
            
            # Sort messages by date
            messages.sort(key=lambda x: x.get('date', ''))
            return messages
        except Exception as e:
            logging.error("Error fetching thread %s: %s", thread_id, e)
            return []

    def reply_to_thread(self, to_email, subject, body, thread_id, message_id=None):
        logging.debug("Sending reply to thread: %s", thread_id)
        try:
            # Create a MIME message
            message = MIMEMultipart("alternative")
            message['to'] = to_email
            message['subject'] = subject

            # Add In-Reply-To and References headers if replying to a specific message
            if message_id:
                message['In-Reply-To'] = message_id
                message['References'] = message_id

            # Attach the HTML body
            message.attach(MIMEText(body, "html"))

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

    def get_attachment(self, email_id, attachment_id):
        logging.debug("Fetching attachment with ID: %s for email: %s", attachment_id, email_id)
        try:
            attachment = self.service.users().messages().attachments().get(
                userId='me', messageId=email_id, id=attachment_id
            ).execute()
            data = base64.urlsafe_b64decode(attachment['data'])
            return {
                'data': data,
                'mimeType': attachment.get('mimeType', 'application/octet-stream'),
                'filename': attachment.get('filename', 'attachment')
            }
        except Exception as e:
            logging.error("Error fetching attachment %s for email %s: %s", attachment_id, email_id, e)
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

