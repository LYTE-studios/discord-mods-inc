"""
Ticket service module for handling support tickets
"""
from typing import Dict, List, Optional
from django.contrib.auth import get_user_model
from django.utils import timezone
from web.core.models import BaseModel
from django.db import models

User = get_user_model()

class Ticket(BaseModel):
    STATUS_CHOICES = [
        ('open', 'Open'),
        ('in_progress', 'In Progress'),
        ('resolved', 'Resolved'),
        ('closed', 'Closed'),
    ]

    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]

    title = models.CharField(max_length=200)
    description = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='medium')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_tickets')
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='assigned_tickets')
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        app_label = 'core'

class TicketService:
    def create_ticket(self, data: Dict, user: User) -> Ticket:
        """
        Create a new ticket
        """
        ticket = Ticket.objects.create(
            title=data['title'],
            description=data['description'],
            priority=data.get('priority', 'medium'),
            created_by=user
        )
        return ticket

    def assign_ticket(self, ticket_id: int, user: User) -> Optional[Ticket]:
        """
        Assign ticket to a user
        """
        try:
            ticket = Ticket.objects.get(id=ticket_id)
            ticket.assigned_to = user
            ticket.status = 'in_progress'
            ticket.save()
            return ticket
        except Ticket.DoesNotExist:
            return None

    def update_status(self, ticket_id: int, status: str) -> Optional[Ticket]:
        """
        Update ticket status
        """
        try:
            ticket = Ticket.objects.get(id=ticket_id)
            ticket.status = status
            if status == 'resolved':
                ticket.resolved_at = timezone.now()
            ticket.save()
            return ticket
        except Ticket.DoesNotExist:
            return None

    def get_user_tickets(self, user: User, status: Optional[str] = None) -> List[Ticket]:
        """
        Get tickets for a user (either created by or assigned to)
        """
        tickets = Ticket.objects.filter(
            models.Q(created_by=user) | models.Q(assigned_to=user)
        )
        if status:
            tickets = tickets.filter(status=status)
        return tickets.order_by('-created_at')

    def get_open_tickets(self) -> List[Ticket]:
        """
        Get all open tickets
        """
        return Ticket.objects.filter(status='open').order_by('-created_at')

    def get_ticket_stats(self) -> Dict:
        """
        Get ticket statistics
        """
        total = Ticket.objects.count()
        open_tickets = Ticket.objects.filter(status='open').count()
        in_progress = Ticket.objects.filter(status='in_progress').count()
        resolved = Ticket.objects.filter(status='resolved').count()
        
        return {
            'total': total,
            'open': open_tickets,
            'in_progress': in_progress,
            'resolved': resolved,
            'resolution_rate': (resolved / total * 100) if total > 0 else 0
        }

ticket_service = TicketService()