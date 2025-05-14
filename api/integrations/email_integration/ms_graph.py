# ms_graph.py

import os
import webbrowser
import msal

REDIRECT_URI = "http://localhost:3000"

def get_access_token(application_id, client_secret, scopes):
    print("=================DEBUG=================")
    print(application_id)
    print(client_secret)
    print(scopes)
    client = msal.ConfidentialClientApplication(
        client_id=application_id,
        client_credential=client_secret,
        authority='https://login.microsoftonline.com/common/',
    )

    refresh_token = None
    if os.path.exists('refresh_token.txt'):
        with open('refresh_token.txt', 'r') as file:
            refresh_token = file.read().strip()

    if refresh_token:
        token_response = client.acquire_token_by_refresh_token(refresh_token, scopes=scopes)
    else:
        auth_url = client.get_authorization_request_url(scopes, redirect_uri=REDIRECT_URI)
        print("Open this URL in a browser to authorize:", auth_url)
        webbrowser.open(auth_url)
        authorization_code = input("Enter the authorization code: ")

        if not authorization_code:
            raise ValueError("No authorization code provided.")

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
        print("Failed to obtain token:", token_response.get("error_description"))
        raise RuntimeError("Access token request failed")
