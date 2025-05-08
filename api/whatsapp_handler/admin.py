from django.contrib import admin
from .models import WhatsAppMessage, WhatsAppReply

admin.site.register(WhatsAppMessage)
admin.site.register(WhatsAppReply)

