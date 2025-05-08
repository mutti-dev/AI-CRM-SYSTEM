from django.db import models
from customers.models import Customer

class WhatsAppMessage(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    thread_id = models.CharField(max_length=255)
    content = models.TextField()
    received_at = models.DateTimeField()
    is_replied = models.BooleanField(default=False)
    whatsapp_message_id = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return f"WhatsApp from {self.customer.name} - {self.received_at}"

class WhatsAppReply(models.Model):
    message = models.ForeignKey(WhatsAppMessage, on_delete=models.CASCADE, related_name='replies')
    content = models.TextField()
    sent_at = models.DateTimeField(auto_now_add=True)
    whatsapp_message_id = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return f"Reply to WhatsApp: {self.message.customer.name}"
