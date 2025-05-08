from django.urls import path
from . import views as whatsapp_views

urlpatterns = [
    path('messages/', whatsapp_views.fetch_whatsapp_messages, name='fetch_whatsapp_messages'),
    path('get-chat-by-id/', whatsapp_views.get_chat_by_id, name='get_chat_by_id'),
    path('get-all-messages/', whatsapp_views.get_all_whatsapp_messages, name='get_all_whatsapp_messages'),
    path('control-fetch/', whatsapp_views.get_whatsapp_messages_control, name='get_whatsapp_messages_control'),
    path('send-custom-message/', whatsapp_views.send_custom_message_view, name='send_custom_message_view'),
]
