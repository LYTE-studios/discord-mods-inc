from typing import List, Optional, Dict
from datetime import datetime, timezone
import uuid
from config import settings
from utils.logger import logger
from database.supabase_client import db
from .ticket_types import (
    Ticket, TicketStatus, TicketPriority, TicketType,
    TicketAssignment, TicketRelation, TicketComment,
    TicketNotification, TicketUpdate, TicketReport
)

class TicketManager:
    def __init__(self):
        """Initialize ticket manager"""
        self.db = db

    async def create_ticket(
        self,
        title: str,
        description: str,
        creator_id: str,
        ticket_type: TicketType,
        priority: TicketPriority = TicketPriority.MEDIUM,
        assignees: List[str] = None,
        due_date: Optional[datetime] = None,
        labels: List[str] = None
    ) -> Ticket:
        """Create a new ticket"""
        try:
            ticket_id = str(uuid.uuid4())
            
            # Create ticket assignments if any
            ticket_assignments = []
            if assignees:
                ticket_assignments = [
                    TicketAssignment(
                        user_id=user_id,
                        assigned_by=creator_id
                    ) for user_id in assignees
                ]

            # Create ticket
            ticket = Ticket(
                id=ticket_id,
                title=title,
                description=description,
                type=ticket_type,
                priority=priority,
                status=TicketStatus.OPEN,
                creator_id=creator_id,
                assignees=ticket_assignments,
                due_date=due_date,
                labels=labels or []
            )

            # Save to database
            await self.db.table('tickets').insert(ticket.dict()).execute()
            
            # Create notifications for assignees
            if assignees:
                await self._create_assignment_notifications(ticket, assignees)

            logger.info(f"Created ticket {ticket_id}: {title}")
            return ticket

        except Exception as e:
            logger.error(f"Failed to create ticket: {str(e)}")
            raise

    async def update_ticket(
        self,
        ticket_id: str,
        updates: Dict,
        updated_by: str
    ) -> Ticket:
        """Update a ticket"""
        try:
            # Get current ticket
            ticket_data = await self.get_ticket(ticket_id)
            if not ticket_data:
                raise ValueError(f"Ticket {ticket_id} not found")

            ticket = Ticket(**ticket_data)
            
            # Track updates for notification
            updates_description = []
            
            for field, new_value in updates.items():
                old_value = getattr(ticket, field)
                if old_value != new_value:
                    # Record update
                    update = TicketUpdate(
                        field=field,
                        old_value=str(old_value) if old_value else None,
                        new_value=str(new_value),
                        updated_by=updated_by
                    )
                    await self.db.table('ticket_updates').insert(update.dict()).execute()
                    
                    updates_description.append(f"{field}: {old_value} → {new_value}")
                    
                    # Update ticket
                    setattr(ticket, field, new_value)

            if updates_description:
                ticket.updated_at = datetime.now(timezone.utc)
                await self.db.table('tickets').update(ticket.dict()).eq('id', ticket_id).execute()
                
                # Create notification for changes
                await self._create_update_notification(ticket, updates_description)

            logger.info(f"Updated ticket {ticket_id}")
            return ticket

        except Exception as e:
            logger.error(f"Failed to update ticket: {str(e)}")
            raise

    async def get_ticket(self, ticket_id: str) -> Optional[Dict]:
        """Get a ticket by ID"""
        try:
            response = await self.db.table('tickets').select('*').eq('id', ticket_id).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Failed to get ticket: {str(e)}")
            raise

    async def list_tickets(
        self,
        status: Optional[TicketStatus] = None,
        priority: Optional[TicketPriority] = None,
        assigned_to: Optional[str] = None,
        created_by: Optional[str] = None
    ) -> List[Dict]:
        """List tickets with optional filters"""
        try:
            query = self.db.table('tickets').select('*')
            
            if status:
                query = query.eq('status', status)
            if priority:
                query = query.eq('priority', priority)
            if assigned_to:
                query = query.contains('assignees', [{"user_id": assigned_to}])
            if created_by:
                query = query.eq('creator_id', created_by)

            response = await query.execute()
            return response.data

        except Exception as e:
            logger.error(f"Failed to list tickets: {str(e)}")
            raise

    async def add_comment(
        self,
        ticket_id: str,
        author_id: str,
        content: str
    ) -> TicketComment:
        """Add a comment to a ticket"""
        try:
            comment = TicketComment(
                id=str(uuid.uuid4()),
                ticket_id=ticket_id,
                author_id=author_id,
                content=content
            )
            
            await self.db.table('ticket_comments').insert(comment.dict()).execute()
            
            # Create notification for ticket assignees
            ticket = await self.get_ticket(ticket_id)
            if ticket:
                assignees = [a["user_id"] for a in ticket["assignees"]]
                await self._create_comment_notification(ticket, comment, assignees)

            logger.info(f"Added comment to ticket {ticket_id}")
            return comment

        except Exception as e:
            logger.error(f"Failed to add comment: {str(e)}")
            raise

    async def add_relation(
        self,
        ticket_id: str,
        related_ticket_id: str,
        relation_type: str
    ) -> TicketRelation:
        """Add a relation between tickets"""
        try:
            relation = TicketRelation(
                relation_type=relation_type,
                ticket_id=related_ticket_id
            )
            
            # Update ticket relations
            ticket = await self.get_ticket(ticket_id)
            if not ticket:
                raise ValueError(f"Ticket {ticket_id} not found")
                
            relations = ticket.get("relations", [])
            relations.append(relation.dict())
            
            await self.db.table('tickets').update(
                {"relations": relations}
            ).eq('id', ticket_id).execute()

            logger.info(f"Added relation between tickets {ticket_id} and {related_ticket_id}")
            return relation

        except Exception as e:
            logger.error(f"Failed to add relation: {str(e)}")
            raise

    async def generate_report(self) -> TicketReport:
        """Generate a ticket statistics report"""
        try:
            all_tickets = await self.db.table('tickets').select('*').execute()
            tickets = all_tickets.data
            
            now = datetime.now(timezone.utc)
            
            # Calculate statistics
            total = len(tickets)
            open_tickets = len([t for t in tickets if t["status"] == TicketStatus.OPEN.value])
            completed = len([t for t in tickets if t["status"] == TicketStatus.COMPLETED.value])
            overdue = len([
                t for t in tickets 
                if t["due_date"] and datetime.fromisoformat(t["due_date"]) < now
                and t["status"] not in [TicketStatus.COMPLETED.value, TicketStatus.CLOSED.value]
            ])
            
            # Group by categories
            priority_count = {}
            status_count = {}
            type_count = {}
            
            for ticket in tickets:
                priority_count[ticket["priority"]] = priority_count.get(ticket["priority"], 0) + 1
                status_count[ticket["status"]] = status_count.get(ticket["status"], 0) + 1
                type_count[ticket["type"]] = type_count.get(ticket["type"], 0) + 1
            
            # Calculate average completion time
            completion_times = []
            for ticket in tickets:
                if ticket["status"] == TicketStatus.COMPLETED.value:
                    created = datetime.fromisoformat(ticket["created_at"])
                    completed = datetime.fromisoformat(ticket["updated_at"])
                    completion_times.append((completed - created).total_seconds() / 3600)  # hours
            
            avg_completion_time = sum(completion_times) / len(completion_times) if completion_times else None

            report = TicketReport(
                total_tickets=total,
                open_tickets=open_tickets,
                completed_tickets=completed,
                overdue_tickets=overdue,
                tickets_by_priority=priority_count,
                tickets_by_status=status_count,
                tickets_by_type=type_count,
                average_completion_time=avg_completion_time
            )

            logger.info("Generated ticket report")
            return report

        except Exception as e:
            logger.error(f"Failed to generate report: {str(e)}")
            raise

    async def _create_assignment_notifications(
        self,
        ticket: Ticket,
        assignees: List[str]
    ) -> None:
        """Create notifications for ticket assignments"""
        try:
            notifications = [
                TicketNotification(
                    id=str(uuid.uuid4()),
                    ticket_id=ticket.id,
                    user_id=assignee,
                    type="assignment",
                    message=f"You have been assigned to ticket #{ticket.id}: {ticket.title}"
                ).dict()
                for assignee in assignees
            ]
            
            await self.db.table('ticket_notifications').insert(notifications).execute()
            
        except Exception as e:
            logger.error(f"Failed to create assignment notifications: {str(e)}")
            raise

    async def _create_update_notification(
        self,
        ticket: Ticket,
        updates: List[str]
    ) -> None:
        """Create notifications for ticket updates"""
        try:
            assignees = [a.user_id for a in ticket.assignees]
            if assignees:
                notifications = [
                    TicketNotification(
                        id=str(uuid.uuid4()),
                        ticket_id=ticket.id,
                        user_id=assignee,
                        type="update",
                        message=f"Ticket #{ticket.id} was updated: {', '.join(updates)}"
                    ).dict()
                    for assignee in assignees
                ]
                
                await self.db.table('ticket_notifications').insert(notifications).execute()
                
        except Exception as e:
            logger.error(f"Failed to create update notifications: {str(e)}")
            raise

    async def _create_comment_notification(
        self,
        ticket: Dict,
        comment: TicketComment,
        assignees: List[str]
    ) -> None:
        """Create notifications for new comments"""
        try:
            notifications = [
                TicketNotification(
                    id=str(uuid.uuid4()),
                    ticket_id=ticket["id"],
                    user_id=assignee,
                    type="comment",
                    message=f"New comment on ticket #{ticket['id']}: {comment.content[:100]}..."
                ).dict()
                for assignee in assignees
                if assignee != comment.author_id  # Don't notify the comment author
            ]
            
            if notifications:
                await self.db.table('ticket_notifications').insert(notifications).execute()
                
        except Exception as e:
            logger.error(f"Failed to create comment notifications: {str(e)}")
            raise

# Initialize ticket manager
ticket_manager = TicketManager()