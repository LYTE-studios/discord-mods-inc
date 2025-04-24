from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    """Custom user model for integration with Supabase auth"""
    supabase_uid = models.CharField(max_length=255, unique=True)
    avatar_url = models.URLField(max_length=500, blank=True)
    last_login_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'auth_user'
        
    def __str__(self):
        return self.email