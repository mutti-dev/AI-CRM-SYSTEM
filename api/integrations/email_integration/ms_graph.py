import os
import webbrowser
import msal
from dotenv import load_dotenv

MS_GRAPH_BASE_URL = "https://graph.microsoft.com/v1.0"
REDIRECT_URI = "http://localhost:3000"


def get_access_token(application_id, client_secret, scopes):
    client = msal.ConfidentialClientApplication(
        client_id=application_id,
        client_credential=client_secret,
        authority='https://login.microsoftonline.com/consumers/',
    )

    refresh_token = None
    if os.path.exists('refresh_token.txt'):
        with open('refresh_token.txt', 'r') as file:
            refresh_token = file.read().strip()

    if refresh_token:
        token_response = client.acquire_token_by_refresh_token(refresh_token, scopes=scopes)
    else:
        auth_request_url = client.get_authorization_request_url(scopes,   redirect_uri=REDIRECT_URI)
        webbrowser.open(auth_request_url)
        authorization_code = input('Enter authorization code: ')

        if not authorization_code:
            raise ValueError("Authorization code is empty")

        token_response = client.acquire_token_by_authorization_code(
            code=authorization_code,
            scopes=scopes,
            redirect_uri=REDIRECT_URI
        )

    if 'access_token' in token_response:
        if 'refresh_token' in token_response:
            with open('refresh_token.txt', 'w') as file:
                file.write(token_response['refresh_token'])
        return token_response['access_token']
    else:
        print("Error obtaining access token:", token_response.get('error'), token_response.get('error_description'))
        raise ValueError("Failed to obtain access token")


def main():
    load_dotenv()

    APPLICATION_ID = os.getenv("APPLICATION_CLIENT_ID")
    CLIENT_SECRET = os.getenv("CLIENT_SECRET")
    SCOPES = [
    'User.Read',
    'Mail.ReadWrite',
    'Calendars.ReadWrite',
    'Mail.ReadBasic',
    'Mail.Read',
    'Mail.Send'
    ]

    if not APPLICATION_ID or not CLIENT_SECRET:
        raise ValueError("Missing required environment variables: APPLICATION_CLIENT_ID, CLIENT_SECRET")

    try:
        access_token = get_access_token(application_id=APPLICATION_ID, client_secret=CLIENT_SECRET, scopes=SCOPES)
        headers={
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'

        }
        # print("Headers", headers)
    except Exception as e:
        print("Failed to obtain access token:", e)


main()