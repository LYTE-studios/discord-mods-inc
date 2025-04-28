import discord
from discord.ext import commands
from typing import Optional
from config import settings
from utils.logger import logger
from database.supabase_client import db
from github.github_client import github_manager
from aiohttp import web
import asyncio
import json

class GitHubManager(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.webhook_app = web.Application()
        self.webhook_app.router.add_post("/github/webhook", self.handle_webhook)
        self.webhook_runner = None
        self.setup_webhook_server()

    def setup_webhook_server(self):
        """Setup webhook server"""
        try:
            loop = asyncio.get_event_loop()
            self.webhook_runner = web.AppRunner(self.webhook_app)
            loop.run_until_complete(self.webhook_runner.setup())
            site = web.TCPSite(
                self.webhook_runner,
                settings.WEBHOOK_HOST,
                settings.WEBHOOK_PORT
            )
            loop.run_until_complete(site.start())
            logger.info(f"Webhook server started on port {settings.WEBHOOK_PORT}")
        except Exception as e:
            logger.error(f"Failed to start webhook server: {str(e)}")

    async def handle_webhook(self, request: web.Request) -> web.Response:
        """Handle incoming GitHub webhooks"""
        try:
            # Verify signature
            signature = request.headers.get("X-Hub-Signature-256")
            if not signature:
                return web.Response(status=401)

            payload = await request.read()
            if not await github_manager.verify_webhook_signature(payload, signature):
                return web.Response(status=401)

            # Process event
            event_type = request.headers.get("X-GitHub-Event")
            data = json.loads(payload)
            await github_manager.handle_webhook_event(event_type, data)

            # Send Discord notification
            await self.send_webhook_notification(event_type, data)
            
            return web.Response(status=200)
        except Exception as e:
            logger.error(f"Error handling webhook: {str(e)}")
            return web.Response(status=500)

    async def send_webhook_notification(self, event_type: str, data: dict):
        """Send webhook notification to Discord"""
        try:
            channel = self.bot.get_channel(int(settings.GITHUB_NOTIFICATIONS_CHANNEL))
            if not channel:
                return

            embed = discord.Embed(
                title=f"GitHub {event_type.replace('_', ' ').title()} Event",
                color=discord.Color.blue()
            )

            if event_type == "push":
                embed.add_field(
                    name="Repository",
                    value=data["repository"]["full_name"],
                    inline=False
                )
                embed.add_field(
                    name="Branch",
                    value=data["ref"].split("/")[-1],
                    inline=True
                )
                embed.add_field(
                    name="Commits",
                    value=str(len(data["commits"])),
                    inline=True
                )

            elif event_type == "pull_request":
                embed.add_field(
                    name="Action",
                    value=data["action"],
                    inline=True
                )
                embed.add_field(
                    name="Pull Request",
                    value=f"[{data['pull_request']['title']}]({data['pull_request']['html_url']})",
                    inline=False
                )

            await channel.send(embed=embed)

        except Exception as e:
            logger.error(f"Error sending webhook notification: {str(e)}")

    @commands.has_permissions(manage_messages=True)
    @commands.command(name="create_repo")
    async def create_repo(self, ctx, name: str, *, description: str = ""):
        """Create a new GitHub repository"""
        try:
            repo = await github_manager.create_repository(name, description)
            
            embed = discord.Embed(
                title="Repository Created",
                description=f"Repository {repo.full_name} has been created successfully!",
                color=discord.Color.green()
            )
            embed.add_field(name="URL", value=repo.html_url)
            
            await ctx.send(embed=embed)
            
            await db.log_activity(
                str(ctx.author.id),
                "github_create_repo",
                f"Created repository: {name}"
            )
        except Exception as e:
            logger.error(f"Error creating repository: {str(e)}")
            await ctx.send("❌ Failed to create repository. Please check the logs.")

    @commands.has_permissions(manage_messages=True)
    @commands.command(name="create_branch")
    async def create_branch(self, ctx, repo: str, branch: str, base: str = "main"):
        """Create a new branch in a repository"""
        try:
            await github_manager.create_branch(repo, branch, base)
            
            await ctx.send(f"✅ Branch `{branch}` created successfully!")
            
            await db.log_activity(
                str(ctx.author.id),
                "github_create_branch",
                f"Created branch {branch} in {repo}"
            )
        except Exception as e:
            logger.error(f"Error creating branch: {str(e)}")
            await ctx.send("❌ Failed to create branch. Please check the logs.")

    @commands.has_permissions(manage_messages=True)
    @commands.command(name="create_pr")
    async def create_pr(self, ctx, repo: str, title: str, head: str, base: str = "main", *, body: str = ""):
        """Create a new pull request"""
        try:
            pr = await github_manager.create_pull_request(
                repo,
                title,
                body,
                head,
                base
            )
            
            embed = discord.Embed(
                title="Pull Request Created",
                description=f"Pull request [{pr.title}]({pr.html_url}) has been created!",
                color=discord.Color.green()
            )
            
            await ctx.send(embed=embed)
            
            await db.log_activity(
                str(ctx.author.id),
                "github_create_pr",
                f"Created PR: {title} in {repo}"
            )
        except Exception as e:
            logger.error(f"Error creating pull request: {str(e)}")
            await ctx.send("❌ Failed to create pull request. Please check the logs.")

    @commands.has_permissions(manage_messages=True)
    @commands.command(name="list_prs")
    async def list_prs(self, ctx, repo: str, state: str = "open"):
        """List pull requests in a repository"""
        try:
            pulls = await github_manager.get_pull_requests(repo, state)
            
            if not pulls:
                await ctx.send(f"No {state} pull requests found in {repo}")
                return

            embed = discord.Embed(
                title=f"Pull Requests in {repo}",
                color=discord.Color.blue()
            )
            
            for pr in pulls[:10]:  # Limit to 10 PRs to avoid message length issues
                embed.add_field(
                    name=f"#{pr.number} {pr.title}",
                    value=f"[View PR]({pr.html_url})\nStatus: {pr.state}",
                    inline=False
                )
            
            await ctx.send(embed=embed)
        except Exception as e:
            logger.error(f"Error listing pull requests: {str(e)}")
            await ctx.send("❌ Failed to list pull requests. Please check the logs.")

    def cog_unload(self):
        """Cleanup when cog is unloaded"""
        if self.webhook_runner:
            loop = asyncio.get_event_loop()
            loop.run_until_complete(self.webhook_runner.cleanup())

async def setup(bot):
    await bot.add_cog(GitHubManager(bot))