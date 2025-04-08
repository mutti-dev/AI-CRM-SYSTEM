from django.db import models
from django.contrib.auth.models import User

class Team(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name

class Agent(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    team = models.ForeignKey(Team, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return self.user.get_full_name()

class Customer(models.Model):
    email = models.EmailField(unique=True)
    name = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.email

class FAQ(models.Model):
    question = models.TextField(unique=True)
    answer = models.TextField()
    keywords = models.TextField(help_text="Comma-separated keywords for NLP/Keyword matching.")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.question

class EmailQuery(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    subject = models.CharField(max_length=255)
    content = models.TextField()
    received_at = models.DateTimeField()
    gmail_thread_id = models.CharField(max_length=255, unique=True)
    is_replied = models.BooleanField(default=False)
    assigned_team = models.ForeignKey(Team, on_delete=models.SET_NULL, null=True, blank=True)
    assigned_agent = models.ForeignKey(Agent, on_delete=models.SET_NULL, null=True, blank=True)
    is_complex = models.BooleanField(default=False, help_text="Indicates if manual intervention is needed.")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.subject} - {self.customer.email}"

class EmailReply(models.Model):
    email_query = models.ForeignKey(EmailQuery, on_delete=models.CASCADE, related_name='replies')
    responder = models.ForeignKey(Agent, on_delete=models.SET_NULL, null=True, blank=True)
    content = models.TextField()
    sent_at = models.DateTimeField(auto_now_add=True)
    gmail_message_id = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return f"Reply to: {self.email_query.subject}"

class Task(models.Model):
    TASK_STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('In Progress', 'In Progress'),
        ('Completed', 'Completed'),
    ]
    email_query = models.ForeignKey(EmailQuery, on_delete=models.CASCADE, related_name='tasks')
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

class FineTunedDataset(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    data = models.JSONField()  # Store the fine-tuned dataset as JSON
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
