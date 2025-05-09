import os
import httpx
from dotenv import load_dotenv
from ms_graph import get_access_token  # Ensure this is defined correctly




# TODO: [
#  /users/{email}/mailFolders/Inbox/messages   {Fetch inbox mails} right now it is fetching notes
#  fetch emails with media
#
#  ]

def main():
    load_dotenv()

    APPLICATION_ID = os.getenv("APPLICATION_CLIENT_ID")
    CLIENT_SECRET = os.getenv("CLIENT_SECRET")
    SCOPES = ['User.Read', 'Mail.ReadWrite', 'Mail.Send']
    MS_GRAPH_BASE_URL = os.getenv("MS_GRAPH_BASE_URL", "https://graph.microsoft.com/v1.0")

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

        for skip_value in range(0, 4, 2):
            query_params = {
                '$top': 2,
                '$skip': skip_value,
                '$select': 'subject,sender,receivedDateTime',
                '$orderby': 'receivedDateTime desc',
            }

            response = httpx.get(endpoint, headers=headers, params=query_params)

            if response.status_code != 200:
                raise httpx.HTTPStatusError(
                    f"Error fetching emails: {response.status_code} - {response.text}",
                    request=response.request,
                    response=response
                )

            messages = response.json().get('value', [])
            print(response.json())
            for msg in messages:
                print("Subject:", msg.get('subject'))
                print("From:", msg.get('sender', {}).get('emailAddress', {}).get('address'))
                print("Received:", msg.get('receivedDateTime'))
                print("-" * 50)

    except httpx.HTTPStatusError as e:
        print("HTTP Error:", e.response.status_code, e.response.text)

    except Exception as e:
        print("Error:", str(e))


if __name__ == "__main__":
    main()
