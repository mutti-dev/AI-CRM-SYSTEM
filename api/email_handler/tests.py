from django.test import TestCase
from .ai.chat_history import client, MODEL_NAME  # Updated import to use relative path
import os

class ChatHistoryTestCase(TestCase):
    def test_client_and_model_configuration(self):
        # Ensure the client is properly initialized
        self.assertIsNotNone(client, "Client should be initialized")
        
        # Ensure the model name is set correctly
        self.assertIsNotNone(MODEL_NAME, "Model name should be set")
        self.assertTrue(isinstance(MODEL_NAME, str), "Model name should be a string")
        
        # Check environment variables for API_HOST
        api_host = os.getenv("API_HOST", "github")
        self.assertIn(api_host, ["azure", "ollama", "github", "openai"], "API_HOST should be a valid option")

    def test_generate_response(self):
        prompt = "Hello, how can I assist you today?"
        try:
            response = client.models.generate_content(model=MODEL_NAME, contents=prompt)
            self.assertIsNotNone(response, "Response should not be None")
            self.assertTrue(hasattr(response, 'text'), "Response should have a 'text' attribute")
            self.assertGreater(len(response.text.strip()), 0, "Response text should not be empty")
        except Exception as e:
            self.fail(f"Client failed to generate a response: {e}")





