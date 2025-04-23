from github import Github, GithubException
from github.Repository import Repository
from github.PullRequest import PullRequest
from typing import Optional, List, Dict
import aiohttp
import hmac
import hashlib
from config import settings
from utils.logger import logger
from database.supabase_client import db

class GitHubManager:
    def __init__(self):
        """Initialize GitHub client"""
        try:
            self.client = Github(settings.GITHUB_TOKEN)
            self.org = self.client.get_organization(settings.GITHUB_ORG) if settings.GITHUB_ORG else None
            logger.info("GitHub client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize GitHub client: {str(e)}")
            raise

    async def create_repository(
        self,
        name: str,
        description: str,
        private: bool = True,
        auto_init: bool = True
    ) -> Repository:
        """Create a new repository"""
        try:
            if self.org:
                repo = self.org.create_repo(
                    name=name,
                    description=description,
                    private=private,
                    auto_init=auto_init,
                    allow_squash_merge=True,
                    allow_merge_commit=True,
                    allow_rebase_merge=True
                )
            else:
                repo = self.client.get_user().create_repo(
                    name=name,
                    description=description,
                    private=private,
                    auto_init=auto_init
                )
            
            logger.info(f"Created repository: {name}")
            return repo
        except Exception as e:
            logger.error(f"Failed to create repository: {str(e)}")
            raise

    async def create_branch(
        self,
        repo_name: str,
        branch_name: str,
        base_branch: str = "main"
    ) -> bool:
        """Create a new branch"""
        try:
            repo = self.get_repository(repo_name)
            base = repo.get_branch(base_branch)
            repo.create_git_ref(f"refs/heads/{branch_name}", base.commit.sha)
            
            logger.info(f"Created branch {branch_name} in {repo_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to create branch: {str(e)}")
            raise

    async def create_pull_request(
        self,
        repo_name: str,
        title: str,
        body: str,
        head_branch: str,
        base_branch: str = "main"
    ) -> PullRequest:
        """Create a new pull request"""
        try:
            repo = self.get_repository(repo_name)
            pr = repo.create_pull(
                title=title,
                body=body,
                head=head_branch,
                base=base_branch
            )
            
            logger.info(f"Created pull request: {title} in {repo_name}")
            return pr
        except Exception as e:
            logger.error(f"Failed to create pull request: {str(e)}")
            raise

    async def get_pull_requests(
        self,
        repo_name: str,
        state: str = "open"
    ) -> List[PullRequest]:
        """Get repository pull requests"""
        try:
            repo = self.get_repository(repo_name)
            pulls = list(repo.get_pulls(state=state))
            return pulls
        except Exception as e:
            logger.error(f"Failed to get pull requests: {str(e)}")
            raise

    def get_repository(self, name: str) -> Repository:
        """Get a repository by name"""
        try:
            if self.org:
                return self.org.get_repo(name)
            return self.client.get_user().get_repo(name)
        except Exception as e:
            logger.error(f"Failed to get repository: {str(e)}")
            raise

    async def verify_webhook_signature(
        self,
        payload: bytes,
        signature: str
    ) -> bool:
        """Verify GitHub webhook signature"""
        try:
            if not signature.startswith("sha256="):
                return False
            
            expected = signature[7:]  # Remove 'sha256=' prefix
            secret = settings.GITHUB_WEBHOOK_SECRET.encode()
            
            mac = hmac.new(
                secret,
                msg=payload,
                digestmod=hashlib.sha256
            )
            
            return hmac.compare_digest(mac.hexdigest(), expected)
        except Exception as e:
            logger.error(f"Failed to verify webhook signature: {str(e)}")
            return False

    async def handle_webhook_event(
        self,
        event_type: str,
        payload: Dict
    ) -> None:
        """Handle GitHub webhook events"""
        try:
            handlers = {
                "push": self._handle_push_event,
                "pull_request": self._handle_pr_event,
                "issue": self._handle_issue_event,
                "workflow_run": self._handle_workflow_event
            }
            
            handler = handlers.get(event_type)
            if handler:
                await handler(payload)
            else:
                logger.warning(f"No handler for event type: {event_type}")
        
        except Exception as e:
            logger.error(f"Failed to handle webhook event: {str(e)}")
            raise

    async def _handle_push_event(self, payload: Dict) -> None:
        """Handle push events"""
        try:
            repo_name = payload["repository"]["name"]
            branch = payload["ref"].split("/")[-1]
            commits = payload["commits"]
            
            logger.info(f"Push to {repo_name}/{branch}: {len(commits)} commits")
            
            # Log activity
            await db.log_activity(
                payload["sender"]["id"],
                "github_push",
                f"Push to {repo_name}/{branch}"
            )
        except Exception as e:
            logger.error(f"Failed to handle push event: {str(e)}")

    async def _handle_pr_event(self, payload: Dict) -> None:
        """Handle pull request events"""
        try:
            action = payload["action"]
            pr = payload["pull_request"]
            repo_name = payload["repository"]["name"]
            
            logger.info(f"PR {action} in {repo_name}: {pr['title']}")
            
            # Log activity
            await db.log_activity(
                payload["sender"]["id"],
                "github_pr",
                f"PR {action}: {pr['title']}"
            )
        except Exception as e:
            logger.error(f"Failed to handle PR event: {str(e)}")

    async def _handle_issue_event(self, payload: Dict) -> None:
        """Handle issue events"""
        try:
            action = payload["action"]
            issue = payload["issue"]
            repo_name = payload["repository"]["name"]
            
            logger.info(f"Issue {action} in {repo_name}: {issue['title']}")
            
            # Log activity
            await db.log_activity(
                payload["sender"]["id"],
                "github_issue",
                f"Issue {action}: {issue['title']}"
            )
        except Exception as e:
            logger.error(f"Failed to handle issue event: {str(e)}")

    async def _handle_workflow_event(self, payload: Dict) -> None:
        """Handle workflow run events"""
        try:
            action = payload["action"]
            workflow = payload["workflow_run"]
            repo_name = payload["repository"]["name"]
            
            logger.info(f"Workflow {action} in {repo_name}: {workflow['name']}")
            
            # Log activity
            await db.log_activity(
                payload["sender"]["id"],
                "github_workflow",
                f"Workflow {action}: {workflow['name']}"
            )
        except Exception as e:
            logger.error(f"Failed to handle workflow event: {str(e)}")

# Initialize GitHub client
github_manager = GitHubManager()