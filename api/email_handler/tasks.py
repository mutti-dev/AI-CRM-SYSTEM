from celery import shared_task
from .views import fetch_unread_emails, fetch_whatsapp_messages  # Import the views
from django.test import RequestFactory

@shared_task
def fetch_unread_emails_task():
    factory = RequestFactory()
    request = factory.post('/dummy-url/')  # POST request, because your view expects POST
    response = fetch_unread_emails(request)
    return response.status_code

@shared_task
def fetch_whatsapp_messages_task():
    factory = RequestFactory()
    request = factory.post('/dummy-url/')  # POST request, because your view expects POST
    response = fetch_whatsapp_messages(request)

    return response.status_code


