from django.apps import AppConfig

class ChatConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'chat'
    verbose_name = 'Chat System'

    def ready(self):
        """
        Initialize any chat app specific signals or configurations
        """
        pass  # Add any initialization code here if needed