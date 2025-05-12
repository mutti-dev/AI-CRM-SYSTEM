import os
import httpx
from dotenv import load_dotenv
from ms_graph import get_access_token  # Ensure this is defined correctly

load_dotenv()


class OutlookClient:
    def __init__(self):
        self.application_id = os.getenv("APPLICATION_CLIENT_ID")
        self.client_secret = os.getenv("CLIENT_SECRET")
        self.scopes = [
            'User.Read',
            'Mail.ReadWrite',
            'Mail.Send',
            'Calendars.ReadWrite',
            'Mail.ReadBasic',
            'Mail.Read',
            'Mail.ReadWrite.Shared',
            'Calendars.ReadWrite.Shared',
            'OnlineMeetings.ReadWrite',
            'ChannelMessage.Send',
            'Team.ReadBasic.All',
        ]
        self.base_url = os.getenv("MS_GRAPH_BASE_URL", "https://graph.microsoft.com/v1.0")
        self.token = self.get_access_token()

    def get_access_token(self):
        return get_access_token(
            application_id=self.application_id,
            client_secret=self.client_secret,
            scopes=self.scopes
        )

    def get_headers(self):
        return {
            'Authorization': f'Bearer {self.token}',
            'Content-Type': 'application/json'
        }

    # ================= OUTLOOK MAIL =================

    def fetch_unread_emails(self):
        endpoint = f'{self.base_url}/me/messages'
        headers = self.get_headers()
        params = {
            '$filter': "isRead eq false",
            '$select': 'subject,sender,receivedDateTime',
            '$orderby': 'receivedDateTime desc',
        }
        response = httpx.get(endpoint, headers=headers, params=params)
        response.raise_for_status()
        for msg in response.json().get('value', []):
            print("Message ID:", msg.get('id'))
            print("Subject:", msg.get('subject'))
            print("From:", msg.get('sender', {}).get('emailAddress', {}).get('address'))
            print("Received:", msg.get('receivedDateTime'))
            print("-" * 50)

    def send_email(self, subject, body, to_emails, attachments=None):
        endpoint = f"{self.base_url}/me/sendMail"
        headers = self.get_headers()
        message = {
            "subject": subject,
            "body": {"contentType": "Text", "content": body},
            "toRecipients": [{"emailAddress": {"address": email}} for email in to_emails]
        }
        if attachments:
            message["attachments"] = attachments
        response = httpx.post(endpoint, headers=headers, json={"message": message})
        response.raise_for_status()
        print("Email sent successfully.")

    def move_email_to_folder(self, message_id, folder_id):
        endpoint = f"{self.base_url}/me/messages/{message_id}/move"
        headers = self.get_headers()
        response = httpx.post(endpoint, headers=headers, json={"destinationId": folder_id})
        response.raise_for_status()
        print("Email moved successfully.")

    def list_mail_folders(self):
        endpoint = f"{self.base_url}/me/mailFolders"
        headers = self.get_headers()
        response = httpx.get(endpoint, headers=headers)
        response.raise_for_status()
        for folder in response.json().get("value", []):
            print(f"Folder ID: {folder['id']} - Name: {folder['displayName']}")

    def download_attachments(self, message_id):
        endpoint = f"{self.base_url}/me/messages/{message_id}/attachments"
        headers = self.get_headers()
        response = httpx.get(endpoint, headers=headers)
        response.raise_for_status()
        for attach in response.json().get("value", []):
            print(f"Attachment: {attach['name']} (Size: {attach['size']})")

    def set_auto_reply(self, message):
        endpoint = f"{self.base_url}/me/mailboxSettings"
        headers = self.get_headers()
        payload = {
            "automaticRepliesSetting": {
                "status": "alwaysEnabled",
                "externalAudience": "all",
                "internalReplyMessage": message,
                "externalReplyMessage": message
            }
        }
        response = httpx.patch(endpoint, headers=headers, json=payload)
        response.raise_for_status()
        print("Auto-reply configured.")

    def search_emails(self, keyword):
        endpoint = f"{self.base_url}/me/messages?$search=\"{keyword}\""
        headers = self.get_headers()
        response = httpx.get(endpoint, headers=headers)
        response.raise_for_status()
        for mail in response.json().get("value", []):
            print("Subject:", mail.get("subject"))
            print("From:", mail.get("sender", {}).get("emailAddress", {}).get("address"))
            print("Received:", mail.get("receivedDateTime"))
            print("-" * 50)

    # ================= CALENDAR =================

    def create_recurring_event(self, subject, start, end, recurrence_days):
        endpoint = f"{self.base_url}/me/events"
        headers = self.get_headers()
        payload = {
            "subject": subject,
            "start": {"dateTime": start, "timeZone": "UTC"},
            "end": {"dateTime": end, "timeZone": "UTC"},
            "recurrence": {
                "pattern": {"type": "weekly", "interval": 1, "daysOfWeek": recurrence_days},
                "range": {"type": "endDate", "startDate": start.split("T")[0], "endDate": end.split("T")[0]}
            },
            "isOnlineMeeting": True,
            "onlineMeetingProvider": "teamsForBusiness"
        }
        response = httpx.post(endpoint, headers=headers, json=payload)
        response.raise_for_status()
        print("Recurring meeting created successfully.")

    def get_schedule(self, email, start, end):
        endpoint = f"{self.base_url}/me/calendar/getSchedule"
        headers = self.get_headers()
        payload = {
            "schedules": [email],
            "startTime": {"dateTime": start, "timeZone": "UTC"},
            "endTime": {"dateTime": end, "timeZone": "UTC"},
            "availabilityViewInterval": 30
        }
        response = httpx.post(endpoint, headers=headers, json=payload)
        response.raise_for_status()
        print("Schedule:", response.json())

    # ================= TEAMS =================

    def list_joined_teams(self):
        endpoint = f"{self.base_url}/me/joinedTeams"
        headers = self.get_headers()
        response = httpx.get(endpoint, headers=headers)
        response.raise_for_status()
        for team in response.json().get("value", []):
            print(f"Team ID: {team['id']} - Name: {team['displayName']}")

    def list_team_channels(self, team_id):
        endpoint = f"{self.base_url}/teams/{team_id}/channels"
        headers = self.get_headers()
        response = httpx.get(endpoint, headers=headers)
        response.raise_for_status()
        for channel in response.json().get("value", []):
            print(f"Channel ID: {channel['id']} - Name: {channel['displayName']}")

    def send_message_to_channel(self, team_id, channel_id, message):
        endpoint = f"{self.base_url}/teams/{team_id}/channels/{channel_id}/messages"
        headers = self.get_headers()
        payload = {"body": {"content": message}}
        response = httpx.post(endpoint, headers=headers, json=payload)
        response.raise_for_status()
        print("Message sent to channel.")






# ================= TEST FUNCTION =================



if __name__ == "__main__":
    graph = OutlookClient()
    print("--- Teams ---")
    graph.fetch_unread_emails()
