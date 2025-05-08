from celery import shared_task
from .views import fetch_whatsapp_messages
import logging
from django.test import RequestFactory

logger = logging.getLogger(__name__)


@shared_task
def fetch_whatsapp_messages_task():
    factory = RequestFactory()
    request = factory.post('/dummy-url/')  # POST request, because your view expects POST
    response = fetch_whatsapp_messages(request)

    return response.status_code
