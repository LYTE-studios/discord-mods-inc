from django.apps import AppConfig

class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'web.core'
    verbose_name = 'Core System'

    def ready(self):
        """
        Initialize any core app specific signals or configurations
        """
        pass  # Add any initialization code here if needed