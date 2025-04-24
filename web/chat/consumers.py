import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils import timezone
from .models import Conversation, Message
from .message_router import message_router

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope["user"]
        self.conversation_id = self.scope["url_route"]["kwargs"]["conversation_id"]
        self.room_group_name = f"chat_{self.conversation_id}"

        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

        # Send initial team status
        await self.send_team_status()

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        """
        Handle incoming WebSocket messages
        """
        try:
            data = json.loads(text_data)
            message_type = data.get('type', 'message')

            if message_type == 'heartbeat':
                return

            if message_type == 'message':
                # Save message to database
                message = await self.save_message(data['content'])
                
                # Send message to room group
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        "type": "chat_message",
                        "message": {
                            "id": message.id,
                            "content": message.content,
                            "role": "user",
                            "created_at": message.created_at.isoformat(),
                        }
                    }
                )

                # Process message through router
                await self.process_message(message)

            elif message_type == 'file_upload':
                await self.handle_file_upload(data)

            elif message_type == 'file_download':
                await self.handle_file_download(data)

        except Exception as e:
            await self.send(text_data=json.dumps({
                "type": "error",
                "message": str(e)
            }))

    async def chat_message(self, event):
        """
        Send message to WebSocket
        """
        await self.send(text_data=json.dumps(event["message"]))

    async def team_status(self, event):
        """
        Send team status update to WebSocket
        """
        await self.send(text_data=json.dumps({
            "type": "status",
            "role": event["role"],
            "status": event["status"]
        }))

    async def ticket_update(self, event):
        """
        Send ticket update to WebSocket
        """
        await self.send(text_data=json.dumps({
            "type": "ticket",
            "ticket": event["ticket"]
        }))

    @database_sync_to_async
    def save_message(self, content):
        """
        Save message to database
        """
        conversation = Conversation.objects.get(id=self.conversation_id)
        return Message.objects.create(
            conversation=conversation,
            role='user',
            content=content
        )

    @database_sync_to_async
    def process_message(self, message):
        """
        Process message through router
        """
        message_router.process_message(
            conversation_id=self.conversation_id,
            message_content=message.content,
            user_id=str(self.user.id)
        )

    async def handle_file_upload(self, data):
        """
        Handle file upload request
        """
        file_data = data.get('file', {})
        if not file_data:
            raise ValueError("No file data provided")

        # Process file through router
        await self.channel_layer.send(
            self.channel_name,
            {
                "type": "process_file_upload",
                "file_data": file_data
            }
        )

    async def process_file_upload(self, event):
        """
        Process file upload through router
        """
        message_router.handle_file_upload(
            self.conversation_id,
            event['file_data']
        )

    async def handle_file_download(self, data):
        """
        Handle file download request
        """
        file_request = data.get('file_request', {})
        if not file_request:
            raise ValueError("No file request data provided")

        # Get file through router
        file_data = message_router.handle_file_download(
            self.conversation_id,
            file_request
        )

        if file_data:
            await self.send(text_data=json.dumps({
                "type": "file_download",
                "file": file_data
            }))
        else:
            await self.send(text_data=json.dumps({
                "type": "error",
                "message": "File not found or access denied"
            }))

    async def send_team_status(self):
        """
        Send initial status for all team members
        """
        roles = ['cto', 'ux', 'ui', 'dev', 'tester']
        for role in roles:
            await self.send(text_data=json.dumps({
                "type": "status",
                "role": role,
                "status": "online"
            }))