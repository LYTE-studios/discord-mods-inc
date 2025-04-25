from django.test import TestCase, override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model
from .models import Conversation, Message

User = get_user_model()

@override_settings(
    SECRET_KEY='django-insecure-test-key-123',
    MIDDLEWARE=[
        'django.contrib.sessions.middleware.SessionMiddleware',
        'django.middleware.common.CommonMiddleware',
        'django.middleware.csrf.CsrfViewMiddleware',
        'django.contrib.auth.middleware.AuthenticationMiddleware',
        'django.contrib.messages.middleware.MessageMiddleware',
    ]
)
class ConversationTests(APITestCase):
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
        
        self.conversation = Conversation.objects.create(
            user=self.user,
            title='Test Conversation'
        )
        
        self.message = Message.objects.create(
            conversation=self.conversation,
            user=self.user,
            content='Test message',
            is_ai=False
        )

    def test_create_conversation(self):
        """Test creating a new conversation"""
        url = reverse('conversation-list')
        data = {'title': 'New Conversation'}
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Conversation.objects.count(), 2)
        self.assertEqual(response.data['title'], 'New Conversation')

    def test_list_conversations(self):
        """Test listing conversations"""
        url = reverse('conversation-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['title'], 'Test Conversation')

    def test_get_conversation(self):
        """Test retrieving a single conversation"""
        url = reverse('conversation-detail', args=[self.conversation.id])
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'Test Conversation')

    def test_update_conversation(self):
        """Test updating a conversation"""
        url = reverse('conversation-detail', args=[self.conversation.id])
        data = {'title': 'Updated Conversation'}
        response = self.client.patch(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'Updated Conversation')

    def test_delete_conversation(self):
        """Test deleting a conversation"""
        url = reverse('conversation-detail', args=[self.conversation.id])
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Conversation.objects.count(), 0)

    def test_send_message(self):
        """Test sending a message in a conversation"""
        url = reverse('conversation-send-message', args=[self.conversation.id])
        data = {'content': 'New message'}
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Message.objects.count(), 2)
        self.assertEqual(response.data['content'], 'New message')

    def test_list_messages(self):
        """Test listing messages in a conversation"""
        url = reverse('conversation-messages', args=[self.conversation.id])
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['content'], 'Test message')

    def test_unauthorized_access(self):
        """Test unauthorized access to conversations"""
        self.client.force_authenticate(user=None)
        url = reverse('conversation-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

@override_settings(SECRET_KEY='django-insecure-test-key-123')
class ConversationModelTests(TestCase):
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.conversation = Conversation.objects.create(
            user=self.user,
            title='Test Conversation'
        )

    def test_conversation_str(self):
        """Test the string representation of Conversation"""
        self.assertEqual(
            str(self.conversation),
            f"Test Conversation - {self.user.username}"
        )

    def test_message_str(self):
        """Test the string representation of Message"""
        message = Message.objects.create(
            conversation=self.conversation,
            user=self.user,
            content='Test message content that is longer than fifty characters to test truncation',
            is_ai=False
        )
        self.assertEqual(
            str(message),
            f"{self.user.username}: Test message content that is longer than fifty cha..."
        )

    def test_conversation_ordering(self):
        """Test conversation ordering"""
        conversation2 = Conversation.objects.create(
            user=self.user,
            title='Second Conversation'
        )
        conversations = Conversation.objects.all()
        self.assertEqual(conversations[0], conversation2)
        self.assertEqual(conversations[1], self.conversation)

    def test_message_ordering(self):
        """Test message ordering"""
        message1 = Message.objects.create(
            conversation=self.conversation,
            user=self.user,
            content='First message',
            is_ai=False
        )
        message2 = Message.objects.create(
            conversation=self.conversation,
            user=self.user,
            content='Second message',
            is_ai=True
        )
        messages = Message.objects.all()
        self.assertEqual(messages[0], message1)
        self.assertEqual(messages[1], message2)