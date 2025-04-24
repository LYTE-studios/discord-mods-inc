from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.conf import settings
from .models import Conversation, Message

@login_required
def chat_room(request, conversation_id=None):
    # Get or create conversation
    if conversation_id:
        conversation = get_object_or_404(
            Conversation, 
            id=conversation_id,
            user=request.user
        )
    else:
        conversation = Conversation.objects.create(
            user=request.user,
            title=f"New Conversation {request.user.conversations.count() + 1}"
        )

    # Get messages for this conversation
    messages = conversation.messages.all()

    # Get current ticket if any
    current_ticket = None
    latest_ticket_message = messages.filter(ticket_id__isnull=False).last()
    if latest_ticket_message:
        current_ticket = {
            'id': latest_ticket_message.ticket_id,
            'status': 'Active',  # This would come from your ticket system
            'title': 'Current Task',  # This would come from your ticket system
            'description': 'Working on current task...',  # This would come from your ticket system
            'assignee': 'AI Team'  # This would come from your ticket system
        }

    # WebSocket URL
    websocket_protocol = 'wss' if request.is_secure() else 'ws'
    websocket_url = f"{websocket_protocol}://{request.get_host()}/ws/chat/{conversation.id}/"

    context = {
        'conversation': conversation,
        'messages': messages,
        'current_ticket': current_ticket,
        'websocket_url': websocket_url,
    }

    return render(request, 'chat/room.html', context)

@login_required
def conversation_list(request):
    conversations = request.user.conversations.all()
    return render(request, 'chat/list.html', {'conversations': conversations})