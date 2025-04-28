import discord
from discord.ext import commands
from typing import Optional
from datetime import datetime, timezone
from config import settings
from utils.logger import logger
from database.supabase_client import db
from workflow.workflow_manager import workflow_manager
from workflow.workflow_types import (
    WorkflowType, WorkflowState, WorkflowPriority,
    WORKFLOW_DEFINITIONS
)

class WorkflowManagerCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def create_workflow_embed(self, workflow, include_stages=True) -> discord.Embed:
        """Create a Discord embed for a workflow"""
        # Define status colors
        status_colors = {
            WorkflowState.PENDING.value: discord.Color.light_grey(),
            WorkflowState.IN_PROGRESS.value: discord.Color.blue(),
            WorkflowState.REVIEWING.value: discord.Color.purple(),
            WorkflowState.BLOCKED.value: discord.Color.red(),
            WorkflowState.COMPLETED.value: discord.Color.green(),
            WorkflowState.FAILED.value: discord.Color.dark_red(),
            WorkflowState.CANCELLED.value: discord.Color.dark_grey()
        }

        embed = discord.Embed(
            title=f"Workflow: {workflow.title}",
            description=workflow.description,
            color=status_colors.get(workflow.state, discord.Color.default())
        )

        # Add basic info
        embed.add_field(
            name="Status",
            value=workflow.state.upper(),
            inline=True
        )
        embed.add_field(
            name="Type",
            value=workflow.type.replace("_", " ").title(),
            inline=True
        )
        embed.add_field(
            name="Priority",
            value=workflow.priority.upper(),
            inline=True
        )

        # Add progress
        progress_bar = "█" * int(workflow.progress.actual_progress * 10)
        progress_bar += "░" * (10 - len(progress_bar))
        embed.add_field(
            name="Progress",
            value=f"`{progress_bar}` {workflow.progress.actual_progress * 100:.1f}%\n"
                  f"Stages: {workflow.progress.completed_stages}/{workflow.progress.total_stages}",
            inline=False
        )

        # Add stages if requested
        if include_stages:
            stages_text = ""
            for i, stage in enumerate(workflow.stages):
                status_emoji = {
                    WorkflowState.PENDING.value: "⚪",
                    WorkflowState.IN_PROGRESS.value: "🔵",
                    WorkflowState.REVIEWING.value: "🟣",
                    WorkflowState.BLOCKED.value: "🔴",
                    WorkflowState.COMPLETED.value: "✅",
                    WorkflowState.FAILED.value: "❌",
                    WorkflowState.CANCELLED.value: "⚫"
                }
                emoji = status_emoji.get(stage.state, "⚪")
                stages_text += f"\n{emoji} **{stage.name}** ({stage.assignee.value})"
                if stage.state == WorkflowState.IN_PROGRESS and stage.started_at:
                    time_spent = datetime.now(timezone.utc) - stage.started_at
                    stages_text += f" - {time_spent.total_seconds() / 60:.1f}m"
            
            embed.add_field(
                name="Stages",
                value=stages_text or "No stages",
                inline=False
            )

        # Add blockers if any
        if workflow.progress.blockers:
            embed.add_field(
                name="Blockers",
                value="\n".join(workflow.progress.blockers),
                inline=False
            )

        # Add footer with times
        footer_text = f"Created: {workflow.created_at.strftime('%Y-%m-%d %H:%M UTC')}"
        if workflow.completed_at:
            footer_text += f" | Completed: {workflow.completed_at.strftime('%Y-%m-%d %H:%M UTC')}"
        embed.set_footer(text=footer_text)

        return embed

    @commands.has_permissions(manage_messages=True)
    @commands.command(name="create_workflow")
    async def create_workflow(
        self,
        ctx,
        workflow_type: str,
        priority: str,
        title: str,
        *,
        description: str
    ):
        """Create a new workflow"""
        try:
            # Validate workflow type
            try:
                w_type = WorkflowType(workflow_type.lower())
            except ValueError:
                types = ", ".join([t.value for t in WorkflowType])
                await ctx.send(f"❌ Invalid workflow type. Use: {types}")
                return

            # Validate priority
            try:
                w_priority = WorkflowPriority(priority.lower())
            except ValueError:
                priorities = ", ".join([p.value for p in WorkflowPriority])
                await ctx.send(f"❌ Invalid priority. Use: {priorities}")
                return

            workflow = await workflow_manager.create_workflow(
                workflow_type=w_type,
                title=title,
                description=description,
                creator_id=str(ctx.author.id),
                priority=w_priority
            )

            embed = self.create_workflow_embed(workflow)
            await ctx.send("✅ Workflow created!", embed=embed)

            await db.log_activity(
                str(ctx.author.id),
                "workflow_create",
                f"Created workflow: {title}"
            )

        except Exception as e:
            logger.error(f"Error creating workflow: {str(e)}")
            await ctx.send("❌ Failed to create workflow. Please check the logs.")

    @commands.has_permissions(manage_messages=True)
    @commands.command(name="workflow_status")
    async def workflow_status(self, ctx, workflow_id: str):
        """Get workflow status"""
        try:
            workflow = await workflow_manager.get_workflow(workflow_id)
            if not workflow:
                await ctx.send("❌ Workflow not found.")
                return

            embed = self.create_workflow_embed(workflow, include_stages=True)
            await ctx.send(embed=embed)

        except Exception as e:
            logger.error(f"Error getting workflow status: {str(e)}")
            await ctx.send("❌ Failed to get workflow status. Please check the logs.")

    @commands.has_permissions(manage_messages=True)
    @commands.command(name="list_workflows")
    async def list_workflows(
        self,
        ctx,
        status: Optional[str] = None,
        workflow_type: Optional[str] = None
    ):
        """List workflows with optional filters"""
        try:
            # Validate status if provided
            w_state = None
            if status:
                try:
                    w_state = WorkflowState(status.lower())
                except ValueError:
                    states = ", ".join([s.value for s in WorkflowState])
                    await ctx.send(f"❌ Invalid status. Use: {states}")
                    return

            # Validate type if provided
            w_type = None
            if workflow_type:
                try:
                    w_type = WorkflowType(workflow_type.lower())
                except ValueError:
                    types = ", ".join([t.value for t in WorkflowType])
                    await ctx.send(f"❌ Invalid workflow type. Use: {types}")
                    return

            workflows = await workflow_manager.list_workflows(
                state=w_state,
                workflow_type=w_type
            )

            if not workflows:
                await ctx.send("No workflows found matching the criteria.")
                return

            # Create paginated embeds
            workflows_per_page = 5
            pages = []
            
            for i in range(0, len(workflows), workflows_per_page):
                page_workflows = workflows[i:i + workflows_per_page]
                embed = discord.Embed(
                    title="Workflows",
                    color=discord.Color.blue()
                )
                
                for workflow in page_workflows:
                    embed.add_field(
                        name=f"#{workflow.id}: {workflow.title}",
                        value=f"Type: {workflow.type}\n"
                              f"Status: {workflow.state}\n"
                              f"Progress: {workflow.progress.actual_progress * 100:.1f}%",
                        inline=False
                    )
                
                pages.append(embed)

            # Send first page
            current_page = 0
            message = await ctx.send(embed=pages[current_page])

            # Add navigation reactions if multiple pages
            if len(pages) > 1:
                await message.add_reaction("◀️")
                await message.add_reaction("▶️")

                def check(reaction, user):
                    return user == ctx.author and str(reaction.emoji) in ["◀️", "▶️"]

                while True:
                    try:
                        reaction, user = await self.bot.wait_for(
                            "reaction_add",
                            timeout=60.0,
                            check=check
                        )

                        if str(reaction.emoji) == "▶️" and current_page < len(pages) - 1:
                            current_page += 1
                            await message.edit(embed=pages[current_page])
                        elif str(reaction.emoji) == "◀️" and current_page > 0:
                            current_page -= 1
                            await message.edit(embed=pages[current_page])

                        await message.remove_reaction(reaction, user)
                    except asyncio.TimeoutError:
                        break

        except Exception as e:
            logger.error(f"Error listing workflows: {str(e)}")
            await ctx.send("❌ Failed to list workflows. Please check the logs.")

    @commands.has_permissions(manage_messages=True)
    @commands.command(name="workflow_report")
    async def workflow_report(self, ctx):
        """Generate workflow statistics report"""
        try:
            report = await workflow_manager.generate_report()
            
            embed = discord.Embed(
                title="Workflow Statistics Report",
                color=discord.Color.blue(),
                timestamp=report["generated_at"]
            )
            
            embed.add_field(
                name="Overview",
                value=f"Total Workflows: {report['total_workflows']}\n"
                      f"Active: {report['active_workflows']}\n"
                      f"Completed: {report['completed_workflows']}\n"
                      f"Failed: {report['failed_workflows']}\n"
                      f"Blocked: {report['blocked_workflows']}",
                inline=False
            )
            
            if report["average_completion_time"]:
                embed.add_field(
                    name="Average Completion Time",
                    value=f"{report['average_completion_time']:.1f} hours",
                    inline=True
                )
            
            embed.add_field(
                name="Completion Rate",
                value=f"{report['completion_rate'] * 100:.1f}%",
                inline=True
            )
            
            await ctx.send(embed=embed)

        except Exception as e:
            logger.error(f"Error generating workflow report: {str(e)}")
            await ctx.send("❌ Failed to generate report. Please check the logs.")

async def setup(bot):
    await bot.add_cog(WorkflowManagerCog(bot))