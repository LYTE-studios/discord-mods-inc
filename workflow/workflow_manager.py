import uuid
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timezone
import asyncio
from config import settings
from utils.logger import logger
from database.supabase_client import db
from ai.conversation_manager import conversation_manager
from .workflow_types import (
    Workflow, WorkflowType, WorkflowState, WorkflowPriority,
    WorkflowStage, WorkflowProgress, WorkflowDependency,
    WORKFLOW_DEFINITIONS
)

class WorkflowManager:
    def __init__(self):
        """Initialize workflow manager"""
        self.active_workflows: Dict[str, Workflow] = {}
        self._monitoring_task = None

    async def create_workflow(
        self,
        workflow_type: WorkflowType,
        title: str,
        description: str,
        creator_id: str,
        priority: WorkflowPriority = WorkflowPriority.MEDIUM,
        dependencies: List[str] = None
    ) -> Workflow:
        """Create a new workflow"""
        try:
            workflow_id = str(uuid.uuid4())
            workflow_def = WORKFLOW_DEFINITIONS[workflow_type]

            # Create workflow stages
            stages = [
                WorkflowStage(
                    name=stage["name"],
                    assignee=stage["assignee"],
                    state=WorkflowState.PENDING,
                    timeout_minutes=stage["timeout_minutes"],
                    artifacts={}
                )
                for stage in workflow_def.stages
            ]

            # Create workflow dependencies
            workflow_dependencies = []
            if dependencies:
                for dep_id in dependencies:
                    workflow_dependencies.append(
                        WorkflowDependency(
                            workflow_id=dep_id,
                            dependency_type="blocks"
                        )
                    )

            # Create workflow progress
            progress = WorkflowProgress(
                total_stages=len(stages),
                completed_stages=0,
                current_stage=0,
                estimated_completion=None,
                actual_progress=0.0,
                time_spent=datetime.utcnow() - datetime.utcnow()  # Zero timedelta
            )

            # Create workflow
            workflow = Workflow(
                id=workflow_id,
                type=workflow_type,
                title=title,
                description=description,
                creator_id=creator_id,
                priority=priority,
                state=WorkflowState.PENDING,
                stages=stages,
                dependencies=workflow_dependencies,
                progress=progress
            )

            # Save to database
            await self.save_workflow(workflow)
            
            # Add to active workflows
            self.active_workflows[workflow_id] = workflow
            
            # Start monitoring if not already running
            await self.ensure_monitoring()

            logger.info(f"Created workflow {workflow_id}: {title}")
            return workflow

        except Exception as e:
            logger.error(f"Failed to create workflow: {str(e)}")
            raise

    async def update_workflow_stage(
        self,
        workflow_id: str,
        stage_index: int,
        updates: Dict,
        updated_by: str
    ) -> Optional[Workflow]:
        """Update a workflow stage"""
        try:
            workflow = await self.get_workflow(workflow_id)
            if not workflow:
                raise ValueError(f"Workflow {workflow_id} not found")

            if not 0 <= stage_index < len(workflow.stages):
                raise ValueError(f"Invalid stage index: {stage_index}")

            stage = workflow.stages[stage_index]
            
            # Update stage fields
            for field, value in updates.items():
                if hasattr(stage, field):
                    setattr(stage, field, value)

            # Update timestamps
            if "state" in updates:
                if updates["state"] == WorkflowState.IN_PROGRESS and not stage.started_at:
                    stage.started_at = datetime.utcnow()
                elif updates["state"] == WorkflowState.COMPLETED and not stage.completed_at:
                    stage.completed_at = datetime.utcnow()

            # Update workflow state and progress
            await self._update_workflow_state(workflow)
            
            # Save changes
            await self.save_workflow(workflow)
            
            return workflow

        except Exception as e:
            logger.error(f"Failed to update workflow stage: {str(e)}")
            raise

    async def check_dependencies(self, workflow: Workflow) -> List[str]:
        """Check workflow dependencies and return blocker IDs"""
        try:
            blockers = []
            for dep in workflow.dependencies:
                dep_workflow = await self.get_workflow(dep.workflow_id)
                if dep_workflow and dep_workflow.state != WorkflowState.COMPLETED:
                    blockers.append(dep.workflow_id)
            return blockers

        except Exception as e:
            logger.error(f"Failed to check dependencies: {str(e)}")
            return []

    async def _update_workflow_state(self, workflow: Workflow) -> None:
        """Update workflow state based on stages and dependencies"""
        try:
            # Check dependencies
            blockers = await self.check_dependencies(workflow)
            if blockers:
                workflow.state = WorkflowState.BLOCKED
                workflow.progress.blockers = blockers
                return

            # Count stages by state
            stage_states = {
                state: len([s for s in workflow.stages if s.state == state])
                for state in WorkflowState
            }

            # Update workflow state
            if stage_states[WorkflowState.COMPLETED] == len(workflow.stages):
                workflow.state = WorkflowState.COMPLETED
                workflow.completed_at = datetime.utcnow()
            elif stage_states[WorkflowState.FAILED] > 0:
                workflow.state = WorkflowState.FAILED
            elif stage_states[WorkflowState.IN_PROGRESS] > 0:
                workflow.state = WorkflowState.IN_PROGRESS
            elif stage_states[WorkflowState.PENDING] == len(workflow.stages):
                workflow.state = WorkflowState.PENDING

            # Update progress
            workflow.update_progress()

        except Exception as e:
            logger.error(f"Failed to update workflow state: {str(e)}")
            raise

    async def monitor_workflows(self) -> None:
        """Monitor active workflows for timeouts and state updates"""
        try:
            while True:
                for workflow_id, workflow in list(self.active_workflows.items()):
                    try:
                        # Check workflow timeout
                        if workflow.is_timed_out():
                            workflow.state = WorkflowState.FAILED
                            workflow.progress.blockers.append("Workflow timeout")
                            await self.save_workflow(workflow)
                            continue

                        # Check stage timeouts
                        current_stage = workflow.current_stage()
                        if current_stage and current_stage.state == WorkflowState.IN_PROGRESS:
                            if current_stage.started_at:
                                timeout = current_stage.started_at + \
                                    timedelta(minutes=current_stage.timeout_minutes)
                                if datetime.utcnow() > timeout:
                                    if current_stage.retry_count < current_stage.max_retries:
                                        # Retry stage
                                        current_stage.retry_count += 1
                                        current_stage.started_at = datetime.utcnow()
                                        logger.info(f"Retrying stage {current_stage.name} in workflow {workflow_id}")
                                    else:
                                        # Mark stage as failed
                                        current_stage.state = WorkflowState.FAILED
                                        logger.error(f"Stage {current_stage.name} in workflow {workflow_id} failed after max retries")
                                    
                                    await self.save_workflow(workflow)

                        # Remove completed/failed workflows from active monitoring
                        if workflow.state in [WorkflowState.COMPLETED, WorkflowState.FAILED, WorkflowState.CANCELLED]:
                            self.active_workflows.pop(workflow_id)

                    except Exception as e:
                        logger.error(f"Error monitoring workflow {workflow_id}: {str(e)}")

                await asyncio.sleep(60)  # Check every minute

        except Exception as e:
            logger.error(f"Error in workflow monitor: {str(e)}")
            self._monitoring_task = None

    async def ensure_monitoring(self) -> None:
        """Ensure workflow monitoring is running"""
        if not self._monitoring_task or self._monitoring_task.done():
            self._monitoring_task = asyncio.create_task(self.monitor_workflows())

    async def get_workflow(self, workflow_id: str) -> Optional[Workflow]:
        """Get a workflow by ID"""
        try:
            # Check active workflows first
            if workflow_id in self.active_workflows:
                return self.active_workflows[workflow_id]

            # Check database
            response = await db.table('workflows').select('*').eq('id', workflow_id).execute()
            if response.data:
                workflow = Workflow(**response.data[0])
                return workflow
            return None

        except Exception as e:
            logger.error(f"Failed to get workflow: {str(e)}")
            raise

    async def save_workflow(self, workflow: Workflow) -> None:
        """Save workflow to database"""
        try:
            workflow.updated_at = datetime.utcnow()
            
            # Update database
            await db.table('workflows').upsert(
                workflow.dict(),
                on_conflict='id'
            ).execute()
            
            # Update active workflows if present
            if workflow.id in self.active_workflows:
                self.active_workflows[workflow.id] = workflow

        except Exception as e:
            logger.error(f"Failed to save workflow: {str(e)}")
            raise

    async def list_workflows(
        self,
        state: Optional[WorkflowState] = None,
        workflow_type: Optional[WorkflowType] = None
    ) -> List[Workflow]:
        """List workflows with optional filters"""
        try:
            query = db.table('workflows').select('*')
            
            if state:
                query = query.eq('state', state)
            if workflow_type:
                query = query.eq('type', workflow_type)

            response = await query.execute()
            return [Workflow(**data) for data in response.data]

        except Exception as e:
            logger.error(f"Failed to list workflows: {str(e)}")
            raise

    async def generate_report(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict:
        """Generate workflow statistics report"""
        try:
            query = db.table('workflows').select('*')
            
            if start_date:
                query = query.gte('created_at', start_date.isoformat())
            if end_date:
                query = query.lte('created_at', end_date.isoformat())

            response = await query.execute()
            workflows = [Workflow(**data) for data in response.data]

            # Calculate statistics
            total = len(workflows)
            completed = len([w for w in workflows if w.state == WorkflowState.COMPLETED])
            failed = len([w for w in workflows if w.state == WorkflowState.FAILED])
            active = len([w for w in workflows if w.state == WorkflowState.IN_PROGRESS])
            blocked = len([w for w in workflows if w.state == WorkflowState.BLOCKED])

            # Calculate average completion time
            completion_times = []
            for workflow in workflows:
                if workflow.state == WorkflowState.COMPLETED and workflow.completed_at:
                    time_taken = workflow.completed_at - workflow.created_at
                    completion_times.append(time_taken.total_seconds() / 3600)  # hours

            avg_completion_time = sum(completion_times) / len(completion_times) if completion_times else None

            return {
                "total_workflows": total,
                "completed_workflows": completed,
                "failed_workflows": failed,
                "active_workflows": active,
                "blocked_workflows": blocked,
                "average_completion_time": avg_completion_time,
                "completion_rate": (completed / total) if total > 0 else 0,
                "generated_at": datetime.utcnow()
            }

        except Exception as e:
            logger.error(f"Failed to generate report: {str(e)}")
            raise

# Initialize workflow manager
workflow_manager = WorkflowManager()