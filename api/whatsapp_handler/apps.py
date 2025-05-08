from django.apps import AppConfig


class WhatsappHandlerConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "whatsapp_handler"

    def ready(self):
        # Avoid database access here
        pass
