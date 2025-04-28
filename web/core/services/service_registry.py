"""
Service registry module for easy access to all services
"""
from .ai_service import ai_service
from .monitoring_service import monitoring_service
from .security_service import security_service
from .ticket_service import ticket_service
from .workflow_service import workflow_service

__all__ = [
    'ai_service',
    'monitoring_service',
    'security_service',
    'ticket_service',
    'workflow_service',
]