from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()

class CustomAuthBackend(ModelBackend):
    """
    Custom authentication backend that updates last_login_at
    """
    
    def authenticate(self, request, username=None, password=None, **kwargs):
        user = super().authenticate(request, username, password, **kwargs)
        if user:
            user.last_login_at = timezone.now()
            user.save(update_fields=['last_login_at'])
        return user