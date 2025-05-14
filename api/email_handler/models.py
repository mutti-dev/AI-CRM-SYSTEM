from django.db import models
from customers.models import Customer
from users.models import Agent, Team

class EmailQuery(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    subject = models.CharField(max_length=255)
    content = models.TextField()
    received_at = models.DateTimeField()
    gmail_thread_id = models.CharField(max_length=255, blank=True, null=True)
    gmail_message_id = models.CharField(max_length=255, blank=True, null=True)
    outlook_message_id = models.CharField(max_length=255, blank=True, null=True)
    is_replied = models.BooleanField(default=False)
    assigned_team = models.ForeignKey(Team, on_delete=models.SET_NULL, null=True, blank=True)
    assigned_agent = models.ForeignKey(Agent, on_delete=models.SET_NULL, null=True, blank=True)
    is_complex = models.BooleanField(default=False, help_text="Indicates if manual intervention is needed.")
    created_at = models.DateTimeField(auto_now_add=True)
    email_source = models.CharField(max_length=255, null=True)

    def __str__(self):
        return f"{self.subject} - {self.customer.email} - {self.email_source}"

class EmailAttachment(models.Model):
    email_query = models.ForeignKey(EmailQuery, on_delete=models.CASCADE, related_name='attachments')
    filename = models.CharField(max_length=255)
    mime_type = models.CharField(max_length=100)
    size = models.IntegerField()
    download_url = models.TextField()

    def __str__(self):
        return f"Attachment: {self.filename} ({self.mime_type})"

class EmailReply(models.Model):
    email_query = models.ForeignKey(EmailQuery, on_delete=models.CASCADE, related_name='replies')
    responder = models.ForeignKey(Agent, on_delete=models.SET_NULL, null=True, blank=True)
    content = models.TextField()
    sent_at = models.DateTimeField(auto_now_add=True)
    gmail_message_id = models.CharField(max_length=255, unique=True, null=True, blank=True)
    outlook_message_id = models.CharField(max_length=255, unique=True, null=True, blank=True)
    source = models.CharField(max_length=255,null=True)

    def __str__(self):
        return f"Reply to: {self.email_query.subject}"

class EmailLog(models.Model):
    ACTION_CHOICES = [
        ('Fetched', 'Fetched'),
        ('Processed', 'Processed'),
        ('Replied', 'Replied'),
        ('Failed', 'Failed'),
    ]
    email_query = models.ForeignKey(EmailQuery, on_delete=models.SET_NULL, null=True, blank=True)
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    message = models.TextField(blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.action} - {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}"
