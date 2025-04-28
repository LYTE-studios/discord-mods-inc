from django.db import models

# Base models for core functionality can be added here
class BaseModel(models.Model):
    """
    Abstract base model providing common fields
    """
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True