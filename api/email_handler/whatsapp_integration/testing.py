import requests
import json

url = "https://waapi.app/api/v1/instances/59949/client/action/get-chats"

headers = {
    "accept": "application/json",
    "content-type": "application/json",
    "authorization": "Bearer 4Uy6ByLNn17sqBBhCT4GB9Yi0AbTlu5r4Pzicxy62f6e1efb"
}

payload = {
    "chatId": "923423311653@c.us",  # Trial phone number in correct format
    "message": "Hello! This is a test message from MaxRemind CRM",
    "previewLink": True
}

try:
    response = requests.post(url, headers=headers, json=payload)
    # print(f"Status Code: {response.status_code}")
    # print("Response:", json.dumps(response.json(), indent=2))
except Exception as e:
    print(f"Error: {str(e)}")