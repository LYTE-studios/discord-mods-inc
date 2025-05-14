from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404, redirect, render
from django.views.generic import TemplateView, View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from datetime import datetime
import logging
from .models import Conversation, Message
from .serializers import ConversationSerializer, MessageSerializer

logger = logging.getLogger(__name__)


class ChatListView(LoginRequiredMixin, View):
    """
    View for displaying the chat list page and handling new messages.
    """
    template_name = 'chat/list.html'

    def get(self, request, *args, **kwargs):
        chat_type = request.GET.get('type', 'cto')
        conversations = Conversation.objects.filter(
            user=request.user,
            chat_type=chat_type
        ).order_by('-updated_at')
        
        context = {
            'conversations': conversations,
            'current_chat_type': chat_type,
            'chat_types': Conversation.CHAT_TYPES
        }
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        """Handle new message creation"""
        chat_type = request.GET.get('type', 'cto')
        message_content = request.POST.get('message')

        # Check if this is an AJAX request
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

        if not message_content:
            if is_ajax:
                return JsonResponse({'status': 'error', 'message': 'No message content provided'}, status=400)
            return redirect('chat:list')

        try:
            # Generate AI response
            from web.core.ai.conversation_manager import conversation_manager
            ai_response = conversation_manager.generate_response(
                message_content,
                chat_type
            )

            if is_ajax:
                # Return JSON response for AJAX requests
                return JsonResponse({
                    'status': 'success',
                    'message': {
                        'content': ai_response,
                        'is_ai': True,
                        'created_at': datetime.now().strftime('%H:%M')
                    }
                })
            else:
                # Redirect for regular form submissions
                return redirect('chat:list')

        except Exception as e:
            logger.error(f"Error in chat post: {str(e)}")
            if is_ajax:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Failed to process message. Please try again.'
                }, status=500)
            return redirect('chat:list')


class ChatRoomView(LoginRequiredMixin, TemplateView):
    """
    View for displaying the chat room page.
    Can be used for both new conversations and existing ones.
    """
    template_name = 'chat/room.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        pk = self.kwargs.get('pk')
        
        if pk:
            # Existing conversation
            conversation = get_object_or_404(
                Conversation,
                pk=pk,
                user=self.request.user
            )
            context['conversation'] = conversation
            context['messages'] = conversation.messages.all().order_by('created_at')
        else:
            # New conversation
            context['conversation'] = None
            context['messages'] = []
            
        # Add WebSocket URL for chat
        ws_protocol = 'wss' if self.request.is_secure() else 'ws'
        ws_host = self.request.get_host()
        context['websocket_url'] = f"{ws_protocol}://{ws_host}/ws/chat/"
        if pk:
            context['websocket_url'] += f"{pk}/"
            
        return context


class ConversationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing conversations.
    """
    serializer_class = ConversationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """
        Get conversations for the current user.
        """
        return Conversation.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        """
        Create a new conversation for the current user.
        """
        serializer.save(user=self.request.user)

    @action(detail=True, methods=['post'])
    def send_message(self, request, pk=None):
        """
        Send a message in the conversation.
        """
        conversation = self.get_object()
        serializer = MessageSerializer(data=request.data)
        
        if serializer.is_valid():
            serializer.save(
                conversation=conversation,
                user=request.user
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['get'])
    def messages(self, request, pk=None):
        """
        Get all messages in a conversation.
        """
        conversation = self.get_object()
        messages = Message.objects.filter(conversation=conversation)
        serializer = MessageSerializer(messages, many=True)
        return Response(serializer.data)