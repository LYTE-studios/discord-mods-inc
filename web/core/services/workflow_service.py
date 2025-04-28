"""
Workflow service module for handling workflow management
"""
from typing import Dict, List, Optional
from django.contrib.auth import get_user_model
from django.utils import timezone
from web.core.models import BaseModel
from django.db import models

User = get_user_model()

class Workflow(BaseModel):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    name = models.CharField(max_length=200)
    description = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_workflows')
    assigned_team = models.ManyToManyField(User, related_name='assigned_workflows')
    completion_date = models.DateTimeField(null=True, blank=True)

    class Meta:
        app_label = 'core'

class WorkflowStep(BaseModel):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('blocked', 'Blocked'),
    ]

    workflow = models.ForeignKey(Workflow, on_delete=models.CASCADE, related_name='steps')
    name = models.CharField(max_length=200)
    description = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    order = models.IntegerField()
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='assigned_steps')
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        app_label = 'core'
        ordering = ['order']

class WorkflowService:
    def create_workflow(self, data: Dict, user: User) -> Workflow:
        """
        Create a new workflow
        """
        workflow = Workflow.objects.create(
            name=data['name'],
            description=data['description'],
            created_by=user
        )
        
        # Add steps if provided
        if 'steps' in data:
            for i, step_data in enumerate(data['steps']):
                WorkflowStep.objects.create(
                    workflow=workflow,
                    name=step_data['name'],
                    description=step_data.get('description', ''),
                    order=i + 1,
                    assigned_to=step_data.get('assigned_to')
                )

        return workflow

    def update_workflow_status(self, workflow_id: int, status: str) -> Optional[Workflow]:
        """
        Update workflow status
        """
        try:
            workflow = Workflow.objects.get(id=workflow_id)
            workflow.status = status
            if status == 'completed':
                workflow.completion_date = timezone.now()
            workflow.save()
            return workflow
        except Workflow.DoesNotExist:
            return None

    def update_step_status(self, step_id: int, status: str, user: User) -> Optional[WorkflowStep]:
        """
        Update workflow step status
        """
        try:
            step = WorkflowStep.objects.get(id=step_id)
            step.status = status
            if status == 'completed':
                step.completed_at = timezone.now()
            step.save()

            # Check if all steps are completed
            workflow = step.workflow
            if all(s.status == 'completed' for s in workflow.steps.all()):
                self.update_workflow_status(workflow.id, 'completed')

            return step
        except WorkflowStep.DoesNotExist:
            return None

    def assign_step(self, step_id: int, user: User) -> Optional[WorkflowStep]:
        """
        Assign workflow step to a user
        """
        try:
            step = WorkflowStep.objects.get(id=step_id)
            step.assigned_to = user
            step.status = 'in_progress'
            step.save()
            return step
        except WorkflowStep.DoesNotExist:
            return None

    def get_user_workflows(self, user: User, status: Optional[str] = None) -> List[Workflow]:
        """
        Get workflows for a user (either created by or assigned to)
        """
        workflows = Workflow.objects.filter(
            models.Q(created_by=user) | models.Q(assigned_team=user)
        ).distinct()
        if status:
            workflows = workflows.filter(status=status)
        return workflows.order_by('-created_at')

    def get_workflow_stats(self) -> Dict:
        """
        Get workflow statistics
        """
        total = Workflow.objects.count()
        active = Workflow.objects.filter(status='active').count()
        completed = Workflow.objects.filter(status='completed').count()
        
        return {
            'total': total,
            'active': active,
            'completed': completed,
            'completion_rate': (completed / total * 100) if total > 0 else 0
        }

workflow_service = WorkflowService()