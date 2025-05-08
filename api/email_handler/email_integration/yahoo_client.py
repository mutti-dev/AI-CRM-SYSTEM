import imaplib
import email
from email.header import decode_header
import logging
from email_handler.models import Customer

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

class YahooClient:
    def __init__(self, email_address, password):
        self.email_address = email_address
        self.password = password
        self.imap_server = "imap.mail.yahoo.com"
        self.connection = self.authenticate_yahoo()

    def authenticate_yahoo(self):
        logging.debug("Authenticating Yahoo IMAP...")
        try:
            connection = imaplib.IMAP4_SSL(self.imap_server)
            connection.login(self.email_address, self.password)
            logging.debug("Yahoo IMAP authenticated successfully.")
            return connection
        except Exception as e:
            logging.error("Error authenticating Yahoo IMAP: %s", e)
            raise

    def fetch_unread_emails(self):
        logging.debug("Fetching unread emails from Yahoo...")
        try:
            self.connection.select("INBOX")
            status, messages = self.connection.search(None, 'UNSEEN')
            email_ids = messages[0].split()
            logging.debug("Found %d unread emails in Yahoo.", len(email_ids))

            emails = []
            for email_id in email_ids:
                status, msg_data = self.connection.fetch(email_id, '(RFC822)')
                for response_part in msg_data:
                    if isinstance(response_part, tuple):
                        msg = email.message_from_bytes(response_part[1])
                        subject, encoding = decode_header(msg["Subject"])[0]
                        if isinstance(subject, bytes):
                            subject = subject.decode(encoding or "utf-8")
                        sender = msg.get("From")
                        date = msg.get("Date")

                        # Extract sender email
                        sender_email = email.utils.parseaddr(sender)[1]
                        logging.debug("Extracted sender email: %s", sender_email)

                        # Check if the sender exists in the Customer table
                        if Customer.objects.filter(email=sender_email).exists():
                            body = ""
                            if msg.is_multipart():
                                for part in msg.walk():
                                    if part.get_content_type() == "text/plain":
                                        body = part.get_payload(decode=True).decode()
                                        break
                            else:
                                body = msg.get_payload(decode=True).decode()

                            emails.append({
                                'id': email_id.decode(),
                                'subject': subject,
                                'sender': sender_email,
                                'date': date,
                                'body': body.strip()
                            })

            return emails
        except Exception as e:
            logging.error("Error fetching emails from Yahoo: %s", e)
            return []

if __name__ == "__main__":
    logging.info("Starting YahooClient test...")
    yahoo_client = YahooClient(
        email_address="your_email@yahoo.com",
        password="your_password"
    )

    # Test fetching unread emails
    logging.info("Fetching unread emails from Yahoo...")
    emails = yahoo_client.fetch_unread_emails()
    logging.info("Fetched %d emails from Yahoo.", len(emails))
    for email in emails:
        logging.info("Email: %s", email)
