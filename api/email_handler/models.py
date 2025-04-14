from django.db import models
from django.contrib.auth.models import User
from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError  # Add this import

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
    # Phone number validation
    phone_regex = RegexValidator(
        regex=r'^\+?1?\d{9,15}$',
        message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed."
    )

    email = models.EmailField(unique=True, blank=True, null=True)
    name = models.CharField(max_length=100, blank=True, null=True)
    phone_number = models.CharField(
        validators=[phone_regex],
        max_length=17,
        unique=True,
        blank=True,
        null=True,
        help_text="WhatsApp or primary contact number with country code (e.g. +1234567890)"
    )
    alternate_phone = models.CharField(
        validators=[phone_regex],
        max_length=17,
        blank=True,
        null=True,
        help_text="Alternative contact number"
    )
    preferred_contact = models.CharField(
        max_length=10,
        choices=[
            ('email', 'Email'),
            ('whatsapp', 'WhatsApp'),
            ('phone', 'Phone')
        ],
        default='email'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['phone_number']),
            models.Index(fields=['email'])
        ]
        constraints = [
            models.CheckConstraint(
                check=(
                    models.Q(email__isnull=False) |
                    models.Q(phone_number__isnull=False)
                ),
                name='customer_must_have_contact'
            )
        ]

    def clean(self):
        if not self.email and not self.phone_number:
            raise ValidationError('Customer must have either an email or phone number.')

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        contacts = []
        if self.name:
            contacts.append(self.name)
        if self.email:
            contacts.append(f"📧 {self.email}")
        if self.phone_number:
            contacts.append(f"📱 {self.phone_number}")
        return " | ".join(contacts)

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
