import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

class WhatsAppClient:
    def __init__(self):
        self.base_url = os.getenv('WAAPI_BASE_URL')
        self.api_key = os.getenv('WAAPI_API_KEY')
        print(f"API Key: {self.api_key}")

        self.chat_id = os.getenv('WAAPI_CHATID')
        self.timeout = 20  # You can customize if needed

        if not all([self.base_url, self.api_key, self.chat_id]):
            raise ValueError("Required environment variables are missing")

        self.headers = {
            
            "accept": "application/json",
            "content-type": "application/json",
            "authorization": f"Bearer {self.api_key}",

            
        }
        self.payload = {
            "chatId": self.chat_id,  # Trial phone number in correct format
            "message": "Hello! This is a test message from MaxRemind CRM 923423311653@c.us",
            "previewLink": True
        }


    def fetch_all_messages(self):
        """Fetch all messages from all chats and return JSON"""
        try:
            get_chats_url = f"{self.base_url}/client/action/get-chats"
            response = requests.post(
                get_chats_url,
                headers=self.headers,
                json=self.payload,
            )
            print(f"Status Code: {response.status_code}")
            
            chats = response.json()

            # Save to text file (pretty JSON string)
            with open("chats_response.txt", "w", encoding="utf-8") as file:
                file.write(json.dumps(chats, indent=2))
            
            return chats

        except Exception as e:
            print(f"Error fetching messages: {e}")
            return []



        




        
    def send_message(self):

        """Send Message"""

        try:
            send_message_url = f"{self.base_url}/client/action/send-message"
            response = requests.post(
                send_message_url,
                headers=self.headers,
                json=self.payload,
            )
            print(f"Status Code: {response.status_code}")
            print("Response:", json.dumps(response.json(), indent=2))
            if response.status_code == 200:
                return response.json()
            else:
                print(f"Failed to send message: {response.status_code}, {response.text}")
                return f"Failed to send message: {response.status_code}, {response.text}"

            
        except Exception as e:
            print(f"Error sending message: {e}")
            return None
        


        
    def get_chat_by_id(self, chat_id):
        """Get chat by ID"""
        payload = { "chatId": chat_id }
        try:
            get_chat_url = f"{self.base_url}/client/action/get-message-info-by-id"
            response = requests.post(
                get_chat_url,
                headers=self.headers,
                json=payload,
            )
            print(f"Status Code: {response.status_code}")
            print("Response:", json.dumps(response.json(), indent=2))
            if response.status_code == 200:
                return response.json()
            else:
                print(f"Failed to get chat: {response.status_code}, {response.text}")
                return f"Failed to get chat: {response.status_code}, {response.text}"

            
        except Exception as e:
            print(f"Error getting chat: {e}")
            return None
        



    def fetch_messages(self):
        """
        Fetch latest messages from the specified chat using the WAAPI endpoint.
        Returns the JSON response from the API.
        """
        try:
            fetch_messages_url = f"{self.base_url}/client/action/fetch-messages"
            payload = {
                "chatId": self.chat_id,
                "limit": 15,
                "includeMedia": False
            }
            # print(f"Payload Mutti: {payload}")
            response = requests.post(fetch_messages_url, headers=self.headers, json=payload, timeout=self.timeout)
            if response.status_code == 200:
                return response.json()
            else:
                print(f"Failed to fetch messages: {response.status_code}, {response.text}")
                return None
        except Exception as e:
            print(f"Error fetching messages: {e}")
            return None
        




    def send_custom_message(self, chatId, message):
        """
        Send a custom message to the specified chat using a different endpoint.
        """
        try:
            send_message_url = f"{self.base_url}/client/action/send-message"
            payload = {
                "chatId": chatId,
                "message": message
            }

            print(f"Payload Mutti: {payload}")
            response = requests.post(send_message_url, headers=self.headers, json=payload, timeout=self.timeout)
            print(f"Status Code: {response.status_code}")
            print("Response:", response.text)
            if response.status_code == 200:
                return response.json()
            else:
                print(f"Failed to send message: {response.status_code}, {response.text}")
                return None
        except Exception as e:
            print(f"Error sending custom message: {e}")
            return None

