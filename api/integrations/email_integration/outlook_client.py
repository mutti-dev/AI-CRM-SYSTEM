import os
import httpx
from dotenv import load_dotenv
from ms_graph import get_access_token  # Ensure this is defined correctly

load_dotenv()

APPLICATION_ID = os.getenv("APPLICATION_CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
SCOPES = [
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
MS_GRAPH_BASE_URL = os.getenv("MS_GRAPH_BASE_URL", "https://graph.microsoft.com/v1.0")


def get_headers():
    token = get_access_token(
        application_id=APPLICATION_ID,
        client_secret=CLIENT_SECRET,
        scopes=SCOPES
    )
    return {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }


# ================= OUTLOOK MAIL =================


def fetch_unread_emails():
    """
    Fetches unread emails from Outlook.
    """
    endpoint = f'{MS_GRAPH_BASE_URL}/me/messages'
    try:
        access_token = get_access_token(
            application_id=APPLICATION_ID,
            client_secret=CLIENT_SECRET,
            scopes=SCOPES
        )

        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }

        query_params = {
            '$filter': "isRead eq false",
            '$select': 'subject,sender,receivedDateTime',
            '$orderby': 'receivedDateTime desc',
        }

        response = httpx.get(endpoint, headers=headers, params=query_params)

        if response.status_code != 200:
            raise httpx.HTTPStatusError(
                f"Error fetching unread emails: {response.status_code} - {response.text}",
                request=response.request,
                response=response
            )

        messages = response.json().get('value', [])

        for msg in messages:
            print("Message ID:", msg.get('id'))  # <-- Added here
            print("Subject:", msg.get('subject'))
            print("From:", msg.get('sender', {}).get('emailAddress', {}).get('address'))
            print("Received:", msg.get('receivedDateTime'))
            print("-" * 50)

    except httpx.HTTPStatusError as e:
        print("HTTP Error:", e.response.status_code, e.response.text)

    except Exception as e:
        print("Error:", str(e))


def send_email(subject, body, to_emails, attachments=None):
    endpoint = f"{MS_GRAPH_BASE_URL}/me/sendMail"
    headers = get_headers()

    message = {
        "subject": subject,
        "body": {
            "contentType": "Text",
            "content": body
        },
        "toRecipients": [
            {"emailAddress": {"address": email}} for email in to_emails
        ]
    }

    if attachments:
        message["attachments"] = attachments

    response = httpx.post(endpoint, headers=headers, json={"message": message})
    response.raise_for_status()
    print("Email sent successfully.")


def move_email_to_folder(message_id, folder_id):
    endpoint = f"{MS_GRAPH_BASE_URL}/me/messages/{message_id}/move"
    headers = get_headers()
    response = httpx.post(endpoint, headers=headers, json={"destinationId": folder_id})
    response.raise_for_status()
    print("Email moved successfully.")


def list_mail_folders():
    endpoint = f"{MS_GRAPH_BASE_URL}/me/mailFolders"
    headers = get_headers()
    response = httpx.get(endpoint, headers=headers)
    response.raise_for_status()
    folders = response.json().get("value", [])
    for folder in folders:
        print(f"Folder ID: {folder['id']} - Name: {folder['displayName']}")


def download_attachments(message_id):
    endpoint = f"{MS_GRAPH_BASE_URL}/me/messages/{message_id}/attachments"
    headers = get_headers()
    response = httpx.get(endpoint, headers=headers)
    response.raise_for_status()
    attachments = response.json().get("value", [])
    for attach in attachments:
        print(f"Attachment: {attach['name']} (Size: {attach['size']})")


def set_auto_reply(message):
    endpoint = f"{MS_GRAPH_BASE_URL}/me/mailboxSettings"
    headers = get_headers()
    settings = {
        "automaticRepliesSetting": {
            "status": "alwaysEnabled",
            "externalAudience": "all",
            "internalReplyMessage": message,
            "externalReplyMessage": message
        }
    }
    response = httpx.patch(endpoint, headers=headers, json=settings)
    response.raise_for_status()
    print("Auto-reply configured.")


def search_emails(keyword):
    endpoint = f"{MS_GRAPH_BASE_URL}/me/messages?$search=\"{keyword}\""
    headers = get_headers()
    response = httpx.get(endpoint, headers=headers)
    response.raise_for_status()
    results = response.json().get("value", [])
    for mail in results:
        print("Subject:", mail.get("subject"))
        print("From:", mail.get("sender", {}).get("emailAddress", {}).get("address"))
        print("Received:", mail.get("receivedDateTime"))
        print("-" * 50)


# ================= CALENDAR =================

def create_recurring_event(subject, start, end, recurrence_days):
    endpoint = f"{MS_GRAPH_BASE_URL}/me/events"
    headers = get_headers()

    event = {
        "subject": subject,
        "start": {"dateTime": start, "timeZone": "UTC"},
        "end": {"dateTime": end, "timeZone": "UTC"},
        "recurrence": {
            "pattern": {
                "type": "weekly",
                "interval": 1,
                "daysOfWeek": recurrence_days
            },
            "range": {
                "type": "endDate",
                "startDate": start.split("T")[0],
                "endDate": end.split("T")[0]
            }
        },
        "isOnlineMeeting": True,
        "onlineMeetingProvider": "teamsForBusiness"
    }

    response = httpx.post(endpoint, headers=headers, json=event)
    response.raise_for_status()
    print("Recurring meeting created successfully.")


def get_schedule(email, start, end):
    endpoint = f"{MS_GRAPH_BASE_URL}/me/calendar/getSchedule"
    headers = get_headers()
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

# TODO: {
# Team.ReadBasic.All ✅ (Required for listing joined teams)
#
# Channel.ReadBasic.All ✅ (If listing channels later)
#
# Group.Read.All ✅ (Sometimes needed for team metadata)
#
# Chat.ReadWrite (Optional, for broader messaging access)}

def list_joined_teams():
    endpoint = f"{MS_GRAPH_BASE_URL}/me/joinedTeams"
    headers = get_headers()
    response = httpx.get(endpoint, headers=headers)
    response.raise_for_status()
    teams = response.json().get("value", [])
    for team in teams:
        print(f"Team ID: {team['id']} - Name: {team['displayName']}")


def list_team_channels(team_id):
    endpoint = f"{MS_GRAPH_BASE_URL}/teams/{team_id}/channels"
    headers = get_headers()
    response = httpx.get(endpoint, headers=headers)
    response.raise_for_status()
    channels = response.json().get("value", [])
    for channel in channels:
        print(f"Channel ID: {channel['id']} - Name: {channel['displayName']}")


def send_message_to_channel(team_id, channel_id, message):
    endpoint = f"{MS_GRAPH_BASE_URL}/teams/{team_id}/channels/{channel_id}/messages"
    headers = get_headers()
    payload = {
        "body": {
            "content": message
        }
    }
    response = httpx.post(endpoint, headers=headers, json=payload)
    response.raise_for_status()
    print("Message sent to channel.")


# ================= TEST FUNCTION =================



if __name__ == "__main__":
    # print("--- Mail Folders ---")
    # list_mail_folders()
    # Fetch unread emails
    # fetch_unread_emails()

    # print("--- Send Email ---")
    # send_email(subject="Test Email",body="This is a test email.", to_emails=["mutti0738@gmail.com"])

    # Schedule a Teams call
    # schedule_teams_call(
    #     subject="Team Meeting",
    #     start_time="2025-05-13T10:00:00",
    #     end_time="2025-05-13T11:00:00",
    #     attendees=["muqureshi8549@gmail.com"]
    # )

    # Fetch calendar events
    # fetch_calendar_events()

    # Mark an email as read
    # mark_email_as_read("MESSAGE_ID_HERE")

    # Delete an email
    # delete_email("MESSAGE_ID_HERE")


#
    # print("--- Search Emails ---")
    # search_emails("Invoice")
#
#     print("--- Download Attachments ---")
#     # download_attachments("MESSAGE_ID")
#
#     print("--- Auto-reply ---")
#     # set_auto_reply("I am currently out of office.")
#
#     print("--- Recurring Event ---")
#     # create_recurring_event("Weekly Sync", "2025-05-13T09:00:00", "2025-05-13T09:30:00", ["Tuesday"])
#
#     print("--- Get Schedule ---")
#     # get_schedule("example@example.com", "2025-05-13T08:00:00", "2025-05-13T17:00:00")
#
    print("--- Teams ---")
    list_joined_teams()
    # list_team_channels("TEAM_ID")
    # send_message_to_channel("TEAM_ID", "CHANNEL_ID", "Hello from API!")
