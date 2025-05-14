import os
import httpx
from dotenv import load_dotenv
import msal
import webbrowser


load_dotenv()



MS_GRAPH_BASE_URL = "https://graph.microsoft.com/v1.0"
REDIRECT_URI = "http://localhost:3000"

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
        self.token = self.get_access_token()  # ✅ FIXED

    def get_access_token(self):  # ✅ FIXED indentation and scope
        client = msal.ConfidentialClientApplication(
            client_id=self.application_id,
            client_credential=self.client_secret,
            authority='https://login.microsoftonline.com/common/'
        )

        refresh_token_path = 'refresh_token.txt'
        refresh_token = None

        if os.path.exists(refresh_token_path):
            with open(refresh_token_path, 'r') as file:
                refresh_token = file.read().strip()

        if refresh_token:
            token_response = client.acquire_token_by_refresh_token(refresh_token, scopes=self.scopes)
            if 'access_token' in token_response:
                return token_response['access_token']
            else:
                print("⚠️ Refresh token failed. Removing and falling back to auth flow.")
                os.remove(refresh_token_path)

        # If no valid refresh token, do interactive login
        auth_url = client.get_authorization_request_url(self.scopes, redirect_uri=REDIRECT_URI)
        print(f"Please go to the following URL to authenticate:\n{auth_url}")
        webbrowser.open(auth_url)
        code = input("Enter the authorization code: ").strip()

        token_response = client.acquire_token_by_authorization_code(
            code=code,
            scopes=self.scopes,
            redirect_uri=REDIRECT_URI
        )

        if 'access_token' in token_response:
            if 'refresh_token' in token_response:
                with open(refresh_token_path, 'w') as file:
                    file.write(token_response['refresh_token'])
            return token_response['access_token']
        else:
            print("❌ Error obtaining access token:", token_response.get('error'),
                  token_response.get('error_description'))
            raise RuntimeError("Access token request failed")





    def get_headers(self):
        return {
            'Authorization': f'Bearer {self.token}',
            'Content-Type': 'application/json'
        }


    # ================= My Profile ===================

    def my_profile(self, ):
        endpoint = f'{self.base_url}/me'
        headers = self.get_headers()
        response = httpx.get(endpoint, headers=headers)
        response.raise_for_status()
        # print(response.json())
        return  response.json()


    def my_profile_pic(self):

        endpoint = f'{self.base_url}/me/photo/$value'
        response = httpx.get(endpoint, headers = self.get_headers())
        response.raise_for_status
        # print(response.json())
        return response.json()










    # ================= OUTLOOK MAIL =================

    def fetch_unread_emails(self, include_attachments=True):
        endpoint = f'{self.base_url}/me/messages'
        headers = self.get_headers()
        params = {
            '$filter': "isRead eq false",
            '$orderby': 'receivedDateTime desc'
        }
        response = httpx.get(endpoint, headers=headers, params=params)
        response.raise_for_status()

        emails = []
        for msg in response.json().get('value', []):
            email = {
                "id": msg.get("id"),
                "subject": msg.get("subject"),
                "sender": msg.get("sender", {}).get("emailAddress", {}).get("address"),
                "senderName": msg.get("sender", {}).get("emailAddress", {}).get("name"),
                "receivedDateTime": msg.get("receivedDateTime"),
                "bodyPreview": msg.get("bodyPreview"),
                "importance": msg.get("importance"),
                "isRead": msg.get("isRead"),
                "parentFolderId": msg.get("parentFolderId"),
                "attachments": []
            }

            # ✅ Include attachments if flag is True
            if include_attachments:
                attachments_endpoint = f"{self.base_url}/me/messages/{email['id']}/attachments"
                attach_response = httpx.get(attachments_endpoint, headers=headers)
                attach_response.raise_for_status()

                for attach in attach_response.json().get('value', []):
                    if attach.get("@odata.type") == "#microsoft.graph.fileAttachment":
                        email['attachments'].append({
                            "name": attach.get("name"),
                            "contentType": attach.get("contentType"),
                            "size": attach.get("size"),
                            "contentBytes": attach.get("contentBytes")  # base64 encoded content
                        })
            print("EMAILS===========", emails)

            emails.append(email)

        return emails

    def mark_email_as_read(self, message_id):
        endpoint = f"{self.base_url}/me/messages/{message_id}"
        headers = self.get_headers()
        data = {
            "isRead": True
        }

        response = httpx.patch(endpoint, headers=headers, json=data)
        response.raise_for_status()

    def send_email(self, subject, body, to_emails, attachments=None):
        endpoint = f"{self.base_url}/me/sendMail"
        headers = self.get_headers()
        message = {
            "subject": subject,
            "body": {"contentType": "HTML", "content": body},
            "toRecipients": [{"emailAddress": {"address": email}} for email in to_emails]
        }
        if attachments:
            message["attachments"] = attachments
        response = httpx.post(endpoint, headers=headers, json={"message": message})

        print("Email sent successfully.")
        return response.raise_for_status()

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

#
#
if __name__ == "__main__":
    graph = OutlookClient()
    print("--- Debugs  ---")
    graph.fetch_unread_emails()
    # graph.send_email(subject="Mutti Test", body="This just testing of outlook", to_emails=["mutti0738@gmail.com"])

    # graph.get_schedule(email="mutti0738@gmail.com", start="2025-05-13T09:00:00", end="2025-05-13T17:00:00")
    # graph.my_profile_pic()
