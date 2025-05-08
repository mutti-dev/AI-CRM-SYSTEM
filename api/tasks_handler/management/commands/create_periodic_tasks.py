from django.core.management.base import BaseCommand
from django_celery_beat.models import PeriodicTask, IntervalSchedule
import json

class Command(BaseCommand):
    help = 'Create periodic tasks for the application'

    def handle(self, *args, **kwargs):
        # Create interval schedule for periodic tasks
        schedule, created = IntervalSchedule.objects.get_or_create(
            every=1,
            period=IntervalSchedule.MINUTES,
        )

        # Task for fetching unread emails
        PeriodicTask.objects.update_or_create(
            name='Fetch unread emails and auto-reply',
            defaults={
                'interval': schedule,
                'task': 'email_handler.tasks.fetch_unread_emails_task',  # Email task
                'args': json.dumps([]),
            }
        )

        # Task for fetching WhatsApp messages
        PeriodicTask.objects.update_or_create(
            name='Fetch WhatsApp messages and auto-reply',
            defaults={
                'interval': schedule,
                'task': 'whatsapp_handler.tasks.fetch_whatsapp_messages_task',  # WhatsApp task
                'args': json.dumps([]),
            }
        )

        self.stdout.write(self.style.SUCCESS('Periodic tasks created successfully.'))
