from enum import Enum
from datetime import datetime
from typing import Optional, List, Dict
from pydantic import BaseModel

class TicketPriority(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"

class TicketStatus(Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    REVIEW = "review"
    BLOCKED = "blocked"
    COMPLETED = "completed"
    CLOSED = "closed"

class TicketType(Enum):
    FEATURE = "feature"
    BUG = "bug"
    TASK = "task"
    IMPROVEMENT = "improvement"
    DOCUMENTATION = "documentation"

class TicketRelationType(Enum):
    BLOCKS = "blocks"
    BLOCKED_BY = "blocked_by"
    RELATES_TO = "relates_to"
    DUPLICATES = "duplicates"
    PARENT_OF = "parent_of"
    CHILD_OF = "child_of"

class TicketRelation(BaseModel):
    relation_type: TicketRelationType
    ticket_id: str
    created_at: datetime = datetime.utcnow()

class TicketComment(BaseModel):
    id: str
    ticket_id: str
    author_id: str
    content: str
    created_at: datetime = datetime.utcnow()
    updated_at: Optional[datetime] = None

class TicketAssignment(BaseModel):
    user_id: str
    assigned_at: datetime = datetime.utcnow()
    assigned_by: str

class Ticket(BaseModel):
    id: str
    title: str
    description: str
    type: TicketType
    priority: TicketPriority
    status: TicketStatus
    creator_id: str
    created_at: datetime = datetime.utcnow()
    updated_at: Optional[datetime] = None
    due_date: Optional[datetime] = None
    assignees: List[TicketAssignment] = []
    relations: List[TicketRelation] = []
    comments: List[TicketComment] = []
    labels: List[str] = []
    github_pr: Optional[str] = None
    github_issue: Optional[str] = None

    class Config:
        use_enum_values = True

class TicketNotification(BaseModel):
    id: str
    ticket_id: str
    user_id: str
    type: str
    message: str
    created_at: datetime = datetime.utcnow()
    read: bool = False

class TicketUpdate(BaseModel):
    field: str
    old_value: Optional[str]
    new_value: str
    updated_by: str
    updated_at: datetime = datetime.utcnow()

class TicketReport(BaseModel):
    total_tickets: int
    open_tickets: int
    completed_tickets: int
    overdue_tickets: int
    tickets_by_priority: Dict[str, int]
    tickets_by_status: Dict[str, int]
    tickets_by_type: Dict[str, int]
    average_completion_time: Optional[float]
    generated_at: datetime = datetime.utcnow()

def format_ticket_for_discord(ticket: Ticket) -> Dict:
    """Format ticket data for Discord embed"""
    status_colors = {
        TicketStatus.OPEN.value: 0x00ff00,  # Green
        TicketStatus.IN_PROGRESS.value: 0x0099ff,  # Blue
        TicketStatus.REVIEW.value: 0xff9900,  # Orange
        TicketStatus.BLOCKED.value: 0xff0000,  # Red
        TicketStatus.COMPLETED.value: 0x9900ff,  # Purple
        TicketStatus.CLOSED.value: 0x666666,  # Gray
    }

    priority_icons = {
        TicketPriority.LOW.value: "🔽",
        TicketPriority.MEDIUM.value: "➡️",
        TicketPriority.HIGH.value: "🔼",
        TicketPriority.URGENT.value: "‼️",
    }

    return {
        "title": f"Ticket #{ticket.id}: {ticket.title}",
        "color": status_colors.get(ticket.status, 0x000000),
        "fields": [
            {
                "name": "Status",
                "value": ticket.status.upper(),
                "inline": True
            },
            {
                "name": "Priority",
                "value": f"{priority_icons.get(ticket.priority, '')} {ticket.priority.upper()}",
                "inline": True
            },
            {
                "name": "Type",
                "value": ticket.type.upper(),
                "inline": True
            },
            {
                "name": "Description",
                "value": (ticket.description[:1000] + "...") if len(ticket.description) > 1000 else ticket.description,
                "inline": False
            },
            {
                "name": "Assignees",
                "value": ", ".join([f"<@{a.user_id}>" for a in ticket.assignees]) or "None",
                "inline": True
            },
            {
                "name": "Due Date",
                "value": ticket.due_date.strftime("%Y-%m-%d %H:%M UTC") if ticket.due_date else "None",
                "inline": True
            }
        ],
        "footer": {
            "text": f"Created by <@{ticket.creator_id}> | Last updated: {ticket.updated_at or ticket.created_at}"
        }
    }