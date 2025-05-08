from django.db import models
from email_handler.models import EmailQuery
from whatsapp_handler.models import WhatsAppMessage
from users.models import Agent, Team

class Task(models.Model):
    TASK_STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('In Progress', 'In Progress'),
        ('Completed', 'Completed'),
    ]
    email_query = models.ForeignKey(EmailQuery, on_delete=models.CASCADE, related_name='tasks', null=True, blank=True)
    whatsapp_query = models.ForeignKey(WhatsAppMessage, on_delete=models.CASCADE, related_name='tasks', null=True, blank=True)
    title = models.CharField(max_length=255)
    description = models.TextField()
    assigned_team = models.ForeignKey(Team, on_delete=models.SET_NULL, null=True)
    assigned_agent = models.ForeignKey(Agent, on_delete=models.SET_NULL, null=True, blank=True)
    status = models.CharField(max_length=20, choices=TASK_STATUS_CHOICES, default='Pending')
    due_date = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title
