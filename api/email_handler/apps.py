from django.apps import AppConfig

class EmailHandlerConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'email_handler'

    def ready(self):
        create_periodic_tasks()

def create_periodic_tasks():
    from django_celery_beat.models import PeriodicTask, IntervalSchedule
    import json
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
            'task': 'email_handler.tasks.fetch_unread_emails_task',
            'args': json.dumps([]),
        }
    )

    # Task for fetching WhatsApp messages
    PeriodicTask.objects.update_or_create(
        name='Fetch WhatsApp messages and auto-reply',
        defaults={
            'interval': schedule,
            'task': 'email_handler.tasks.fetch_whatsapp_messages_task',
            'args': json.dumps([]),
        }
    )

    # Task for fetching WhatsApp messages periodically
    PeriodicTask.objects.update_or_create(
        name='Fetch WhatsApp messages periodically',
        defaults={
            'interval': schedule,
            'task': 'email_handler.tasks.fetch_whatsapp_messages_task',
            'args': json.dumps([]),
        }
    )
