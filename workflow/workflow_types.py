from enum import Enum
from typing import List, Dict, Optional, Union
from datetime import datetime, timedelta
from pydantic import BaseModel
from ai.personality_types import PersonalityType

class WorkflowState(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    REVIEWING = "reviewing"
    BLOCKED = "blocked"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class WorkflowType(Enum):
    FEATURE_DEVELOPMENT = "feature_development"
    BUG_FIX = "bug_fix"
    CODE_REVIEW = "code_review"
    DESIGN_TASK = "design_task"
    TESTING = "testing"
    DOCUMENTATION = "documentation"
    ARCHITECTURE_REVIEW = "architecture_review"

class WorkflowPriority(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"

class DependencyType(Enum):
    BLOCKS = "blocks"
    REQUIRES = "requires"
    RELATES_TO = "relates_to"

class WorkflowStage(BaseModel):
    name: str
    assignee: PersonalityType
    state: WorkflowState
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    timeout_minutes: int
    retry_count: int = 0
    max_retries: int = 3
    artifacts: Dict = {}

class WorkflowDependency(BaseModel):
    workflow_id: str
    dependency_type: DependencyType
    created_at: datetime = datetime.utcnow()

class WorkflowProgress(BaseModel):
    total_stages: int
    completed_stages: int
    current_stage: int
    estimated_completion: Optional[datetime]
    actual_progress: float  # 0 to 1
    time_spent: timedelta
    blockers: List[str] = []

class WorkflowDefinition(BaseModel):
    """Base workflow definition"""
    stages: List[Dict]
    timeout_minutes: int
    required_roles: List[PersonalityType]
    artifacts_schema: Dict

# Predefined workflow definitions
WORKFLOW_DEFINITIONS: Dict[WorkflowType, WorkflowDefinition] = {
    WorkflowType.FEATURE_DEVELOPMENT: WorkflowDefinition(
        stages=[
            {
                "name": "Requirements Analysis",
                "assignee": PersonalityType.CTO,
                "timeout_minutes": 60,
                "artifacts": {
                    "requirements_doc": "str",
                    "technical_specs": "dict"
                }
            },
            {
                "name": "UX Design",
                "assignee": PersonalityType.UX_DESIGNER,
                "timeout_minutes": 120,
                "artifacts": {
                    "user_flows": "list",
                    "wireframes": "dict"
                }
            },
            {
                "name": "UI Design",
                "assignee": PersonalityType.UI_DESIGNER,
                "timeout_minutes": 120,
                "artifacts": {
                    "design_specs": "dict",
                    "component_library": "dict"
                }
            },
            {
                "name": "Implementation",
                "assignee": PersonalityType.DEVELOPER,
                "timeout_minutes": 240,
                "artifacts": {
                    "code_changes": "dict",
                    "tests": "dict"
                }
            },
            {
                "name": "Code Review",
                "assignee": PersonalityType.CODE_REVIEWER,
                "timeout_minutes": 60,
                "artifacts": {
                    "review_comments": "list",
                    "approved": "bool"
                }
            },
            {
                "name": "Testing",
                "assignee": PersonalityType.TESTER,
                "timeout_minutes": 120,
                "artifacts": {
                    "test_results": "dict",
                    "issues_found": "list"
                }
            }
        ],
        timeout_minutes=720,  # 12 hours total
        required_roles=[
            PersonalityType.CTO,
            PersonalityType.UX_DESIGNER,
            PersonalityType.UI_DESIGNER,
            PersonalityType.DEVELOPER,
            PersonalityType.CODE_REVIEWER,
            PersonalityType.TESTER
        ],
        artifacts_schema={
            "final_code": "dict",
            "documentation": "str",
            "test_coverage": "float"
        }
    ),

    WorkflowType.BUG_FIX: WorkflowDefinition(
        stages=[
            {
                "name": "Bug Analysis",
                "assignee": PersonalityType.TESTER,
                "timeout_minutes": 30,
                "artifacts": {
                    "bug_report": "dict",
                    "reproduction_steps": "list"
                }
            },
            {
                "name": "Implementation",
                "assignee": PersonalityType.DEVELOPER,
                "timeout_minutes": 120,
                "artifacts": {
                    "code_changes": "dict",
                    "tests": "dict"
                }
            },
            {
                "name": "Code Review",
                "assignee": PersonalityType.CODE_REVIEWER,
                "timeout_minutes": 30,
                "artifacts": {
                    "review_comments": "list",
                    "approved": "bool"
                }
            },
            {
                "name": "Testing",
                "assignee": PersonalityType.TESTER,
                "timeout_minutes": 60,
                "artifacts": {
                    "test_results": "dict",
                    "verification": "bool"
                }
            }
        ],
        timeout_minutes=240,  # 4 hours total
        required_roles=[
            PersonalityType.DEVELOPER,
            PersonalityType.CODE_REVIEWER,
            PersonalityType.TESTER
        ],
        artifacts_schema={
            "fix_code": "dict",
            "test_results": "dict"
        }
    ),

    WorkflowType.DESIGN_TASK: WorkflowDefinition(
        stages=[
            {
                "name": "Requirements Analysis",
                "assignee": PersonalityType.UX_DESIGNER,
                "timeout_minutes": 60,
                "artifacts": {
                    "user_requirements": "dict",
                    "user_stories": "list"
                }
            },
            {
                "name": "UX Design",
                "assignee": PersonalityType.UX_DESIGNER,
                "timeout_minutes": 120,
                "artifacts": {
                    "wireframes": "dict",
                    "user_flows": "list"
                }
            },
            {
                "name": "UI Design",
                "assignee": PersonalityType.UI_DESIGNER,
                "timeout_minutes": 180,
                "artifacts": {
                    "design_specs": "dict",
                    "components": "dict",
                    "assets": "list"
                }
            },
            {
                "name": "Design Review",
                "assignee": PersonalityType.CTO,
                "timeout_minutes": 60,
                "artifacts": {
                    "review_comments": "list",
                    "approved": "bool"
                }
            }
        ],
        timeout_minutes=420,  # 7 hours total
        required_roles=[
            PersonalityType.UX_DESIGNER,
            PersonalityType.UI_DESIGNER,
            PersonalityType.CTO
        ],
        artifacts_schema={
            "final_design": "dict",
            "assets": "list",
            "documentation": "str"
        }
    )
}

class Workflow(BaseModel):
    """Workflow instance"""
    id: str
    type: WorkflowType
    title: str
    description: str
    creator_id: str
    priority: WorkflowPriority
    state: WorkflowState
    stages: List[WorkflowStage]
    dependencies: List[WorkflowDependency] = []
    progress: WorkflowProgress
    created_at: datetime = datetime.utcnow()
    updated_at: datetime = datetime.utcnow()
    completed_at: Optional[datetime] = None
    artifacts: Dict = {}
    metadata: Dict = {}

    def is_blocked(self) -> bool:
        """Check if workflow is blocked by dependencies"""
        return self.state == WorkflowState.BLOCKED

    def can_proceed(self) -> bool:
        """Check if workflow can proceed to next stage"""
        return (
            not self.is_blocked() and
            self.state not in [WorkflowState.COMPLETED, WorkflowState.FAILED, WorkflowState.CANCELLED]
        )

    def current_stage(self) -> Optional[WorkflowStage]:
        """Get current workflow stage"""
        if 0 <= self.progress.current_stage < len(self.stages):
            return self.stages[self.progress.current_stage]
        return None

    def is_timed_out(self) -> bool:
        """Check if workflow has timed out"""
        if self.created_at:
            workflow_def = WORKFLOW_DEFINITIONS[self.type]
            timeout = self.created_at + timedelta(minutes=workflow_def.timeout_minutes)
            return datetime.utcnow() > timeout
        return False

    def update_progress(self) -> None:
        """Update workflow progress"""
        completed = len([s for s in self.stages if s.state == WorkflowState.COMPLETED])
        self.progress.completed_stages = completed
        self.progress.actual_progress = completed / self.progress.total_stages
        
        if self.created_at:
            self.progress.time_spent = datetime.utcnow() - self.created_at

    class Config:
        arbitrary_types_allowed = True