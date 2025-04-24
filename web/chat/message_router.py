import asyncio
import json
from typing import Dict, Any, Optional
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.conf import settings

from ai.conversation_manager import ConversationManager
from ai.personality_types import AIRole
from tickets.ticket_manager import TicketManager
from github.github_client import GitHubClient

class MessageRouter:
    """
    Routes messages between the web interface and AI processing system
    """
    def __init__(self):
        self.channel_layer = get_channel_layer()
        self.conversation_manager = ConversationManager()
        self.ticket_manager = TicketManager()
        self.github_client = GitHubClient()
        self._conversation_contexts: Dict[str, Dict[str, Any]] = {}

    def process_message(self, conversation_id: str, message_content: str, user_id: str) -> None:
        """
        Process incoming message and route it to appropriate handlers
        """
        # Get or create conversation context
        context = self._get_conversation_context(conversation_id)
        
        # Update context with new message
        context['messages'].append({
            'role': 'user',
            'content': message_content
        })

        # Process message through AI system
        try:
            response = self.conversation_manager.process_message(
                message_content,
                context=context,
                user_id=user_id
            )

            # Handle different types of responses
            if response.get('type') == 'ticket':
                self._handle_ticket_response(conversation_id, response)
            elif response.get('type') == 'github':
                self._handle_github_response(conversation_id, response)
            else:
                self._handle_standard_response(conversation_id, response)

            # Update conversation context
            context['messages'].append({
                'role': response.get('role', 'assistant'),
                'content': response.get('content', '')
            })

        except Exception as e:
            self._send_error_message(conversation_id, str(e))

    def _get_conversation_context(self, conversation_id: str) -> Dict[str, Any]:
        """
        Get or create conversation context
        """
        if conversation_id not in self._conversation_contexts:
            self._conversation_contexts[conversation_id] = {
                'messages': [],
                'current_ticket': None,
                'github_context': {},
                'active_roles': set()
            }
        return self._conversation_contexts[conversation_id]

    def _handle_ticket_response(self, conversation_id: str, response: Dict[str, Any]) -> None:
        """
        Handle ticket-related responses
        """
        ticket_data = response.get('ticket_data', {})
        context = self._conversation_contexts[conversation_id]
        
        # Update ticket in context
        context['current_ticket'] = ticket_data
        
        # Send ticket update to websocket
        self._send_to_websocket(conversation_id, {
            'type': 'ticket_update',
            'ticket': ticket_data
        })

        # Send AI response message
        self._send_ai_message(conversation_id, response)

    def _handle_github_response(self, conversation_id: str, response: Dict[str, Any]) -> None:
        """
        Handle GitHub-related responses
        """
        github_data = response.get('github_data', {})
        context = self._conversation_contexts[conversation_id]
        
        # Update GitHub context
        context['github_context'].update(github_data)
        
        # Send AI response message
        self._send_ai_message(conversation_id, response)

    def _handle_standard_response(self, conversation_id: str, response: Dict[str, Any]) -> None:
        """
        Handle standard AI responses
        """
        self._send_ai_message(conversation_id, response)

    def _send_ai_message(self, conversation_id: str, response: Dict[str, Any]) -> None:
        """
        Send AI message to websocket
        """
        message_data = {
            'type': 'chat_message',
            'message': {
                'role': response.get('role', 'assistant'),
                'content': response.get('content', ''),
                'metadata': response.get('metadata', {}),
            }
        }

        if response.get('ticket_id'):
            message_data['message']['ticket_id'] = response['ticket_id']

        self._send_to_websocket(conversation_id, message_data)

    def _send_error_message(self, conversation_id: str, error_message: str) -> None:
        """
        Send error message to websocket
        """
        self._send_to_websocket(conversation_id, {
            'type': 'chat_message',
            'message': {
                'role': 'system',
                'content': f"Error: {error_message}",
                'metadata': {'error': True}
            }
        })

    def _send_to_websocket(self, conversation_id: str, message: Dict[str, Any]) -> None:
        """
        Send message to websocket group
        """
        async_to_sync(self.channel_layer.group_send)(
            f"chat_{conversation_id}",
            message
        )

    def handle_file_upload(self, conversation_id: str, file_data: Dict[str, Any]) -> None:
        """
        Handle file uploads and route to appropriate processors
        """
        try:
            # Process file through appropriate handler
            if file_data.get('type') == 'code':
                response = self.github_client.process_file(file_data)
            else:
                response = self.conversation_manager.process_file(file_data)

            # Send response
            self._handle_standard_response(conversation_id, response)

        except Exception as e:
            self._send_error_message(conversation_id, f"File upload error: {str(e)}")

    def handle_file_download(self, conversation_id: str, file_request: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Handle file download requests
        """
        try:
            if file_request.get('source') == 'github':
                return self.github_client.get_file(file_request)
            return None
        except Exception as e:
            self._send_error_message(conversation_id, f"File download error: {str(e)}")
            return None

# Create global router instance
message_router = MessageRouter()