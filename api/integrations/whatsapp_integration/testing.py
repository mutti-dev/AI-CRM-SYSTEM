import requests

url = "https://waapi.app/api/v1/instances/60995/client/action/fetch-messages"

payload = {
    "chatId": "923423311653@c.us",
    "limit": 10,
    "fromMe": False,
    "includeMedia": False
}
headers = {
    "accept": "application/json",
    "content-type": "application/json",
    "authorization": "Bearer SknzPqmdKC9Lvol3YPsuPcP9Vz5hpRdPF7AmpjQS1eea6b54"
}

response = requests.post(url, json=payload, headers=headers)

print(response.text)