from django.db import models
from django.conf import settings

class Conversation(models.Model):
    """
    Model representing a conversation.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='conversations'
    )
    title = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_cto_chat = models.BooleanField(default=False)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        return f"{self.title} - {self.user.username}"

class Message(models.Model):
    """
    Model representing a message in a conversation.
    """
    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name='messages'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='messages'
    )
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_ai = models.BooleanField(default=False)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        truncated_content = self.content[:50] + "..." if len(self.content) > 50 else self.content
        return f"{self.user.username}: {truncated_content}"