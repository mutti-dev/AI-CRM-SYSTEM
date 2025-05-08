from django.db import models
from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError

class Customer(models.Model):
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
                check=(models.Q(email__isnull=False) | models.Q(phone_number__isnull=False)),
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
