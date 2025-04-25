from rest_framework import serializers
from .models import Conversation, Message

class MessageSerializer(serializers.ModelSerializer):
    """
    Serializer for Message model.
    """
    username = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = Message
        fields = ['id', 'content', 'created_at', 'is_ai', 'username']
        read_only_fields = ['created_at', 'user']

class ConversationSerializer(serializers.ModelSerializer):
    """
    Serializer for Conversation model.
    """
    messages = MessageSerializer(many=True, read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)
    message_count = serializers.SerializerMethodField()

    class Meta:
        model = Conversation
        fields = ['id', 'title', 'created_at', 'updated_at', 'username', 'messages', 'message_count']
        read_only_fields = ['created_at', 'updated_at', 'user']

    def get_message_count(self, obj):
        """
        Get the number of messages in the conversation.
        """
        return obj.messages.count()