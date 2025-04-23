import discord
from discord.ext import commands
from typing import Optional, List, Dict
from config import settings
from utils.logger import logger
from database.supabase_client import db
from ai.personality_types import PersonalityType
from ai.conversation_manager import conversation_manager
from tickets.ticket_manager import ticket_manager
from github.github_client import github_manager

class AITeamManager(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def get_conversation_id(self, ctx, role: Optional[str] = None) -> str:
        """Generate a unique conversation ID"""
        base_id = f"{ctx.guild.id}-{ctx.channel.id}"
        return f"{base_id}-{role}" if role else base_id

    async def get_context_data(self, ctx) -> Dict:
        """Gather context data for AI responses"""
        try:
            # Get active tickets
            active_tickets = await ticket_manager.list_tickets(
                status=None,  # All statuses
                assigned_to=str(ctx.author.id)
            )

            # Get recent GitHub activity
            # This would be implemented based on your GitHub integration
            github_context = {}  # Placeholder for GitHub context

            return {
                "current_task": None,  # Set by specific commands
                "related_tickets": [ticket["id"] for ticket in active_tickets],
                "github_context": github_context,
                "collaboration_history": []  # Updated during team discussions
            }
        except Exception as e:
            logger.error(f"Error gathering context data: {str(e)}")
            return {}

    @commands.has_permissions(manage_messages=True)
    @commands.command(name="ai_chat")
    async def ai_chat(self, ctx, role: str, *, message: str):
        """Chat with a specific AI team member"""
        try:
            # Convert role to personality type
            try:
                personality_type = PersonalityType(role.lower())
            except ValueError:
                roles = ", ".join([r.value for r in PersonalityType])
                await ctx.send(f"❌ Invalid role. Available roles: {roles}")
                return

            # Show typing indicator
            async with ctx.typing():
                # Get context data
                context = await self.get_context_data(ctx)
                
                # Get AI response
                conversation_id = self.get_conversation_id(ctx, role)
                response = await conversation_manager.get_ai_response(
                    conversation_id=conversation_id,
                    user_message=message,
                    personality_type=personality_type,
                    context=context
                )

                if response:
                    # Log the interaction
                    await db.log_activity(
                        str(ctx.author.id),
                        "ai_chat",
                        f"Chat with {role}: {message[:100]}..."
                    )
                    
                    # Create and send embed response
                    embed = discord.Embed(
                        title=f"AI {role.upper()}",
                        description=response,
                        color=discord.Color.blue()
                    )
                    embed.set_footer(text=f"Requested by {ctx.author.name}")
                    await ctx.send(embed=embed)
                else:
                    await ctx.send("❌ Failed to get AI response. Please try again.")

        except Exception as e:
            logger.error(f"Error in ai_chat command: {str(e)}")
            await ctx.send("❌ An error occurred while processing your request.")

    @commands.has_permissions(manage_messages=True)
    @commands.command(name="team_review")
    async def team_review(self, ctx, content_type: str, *, content: str):
        """Get team review on code, design, or other content"""
        try:
            # Define reviewers based on content type
            reviewers = {
                "code": [
                    (PersonalityType.CODE_REVIEWER, "Code Review"),
                    (PersonalityType.DEVELOPER, "Implementation Feedback"),
                    (PersonalityType.TESTER, "Testing Considerations")
                ],
                "design": [
                    (PersonalityType.UI_DESIGNER, "UI Analysis"),
                    (PersonalityType.UX_DESIGNER, "UX Analysis"),
                    (PersonalityType.DEVELOPER, "Implementation Feasibility")
                ],
                "architecture": [
                    (PersonalityType.CTO, "Architecture Review"),
                    (PersonalityType.DEVELOPER, "Implementation Impact"),
                    (PersonalityType.CODE_REVIEWER, "Code Structure Impact")
                ]
            }

            if content_type not in reviewers:
                await ctx.send(f"❌ Invalid content type. Use: {', '.join(reviewers.keys())}")
                return

            async with ctx.typing():
                context = await self.get_context_data(ctx)
                
                embed = discord.Embed(
                    title=f"Team Review: {content_type.title()}",
                    description=f"Content to review:\n```\n{content[:1000]}\n```",
                    color=discord.Color.blue()
                )

                for personality_type, review_type in reviewers[content_type]:
                    conversation_id = self.get_conversation_id(ctx, personality_type.value)
                    response = await conversation_manager.get_review_response(
                        conversation_id=conversation_id,
                        personality_type=personality_type,
                        content=content,
                        context=context
                    )
                    
                    if response:
                        embed.add_field(
                            name=review_type,
                            value=response[:1024],  # Discord field value limit
                            inline=False
                        )

                await ctx.send(embed=embed)

        except Exception as e:
            logger.error(f"Error in team_review command: {str(e)}")
            await ctx.send("❌ An error occurred while processing the review.")

    @commands.has_permissions(manage_messages=True)
    @commands.command(name="team_discuss")
    async def team_discuss(self, ctx, *, topic: str):
        """Start a discussion between all AI team members about a topic"""
        try:
            async with ctx.typing():
                context = await self.get_context_data(ctx)
                
                # Create participants list with conversation IDs and personality types
                participants = [
                    (self.get_conversation_id(ctx, p_type.value), p_type)
                    for p_type in PersonalityType
                ]
                
                responses = await conversation_manager.facilitate_team_discussion(
                    topic=topic,
                    participants=participants,
                    context=context
                )
                
                if responses:
                    # Create main embed for topic
                    main_embed = discord.Embed(
                        title="Team Discussion",
                        description=f"Topic: {topic}",
                        color=discord.Color.blue()
                    )
                    await ctx.send(embed=main_embed)
                    
                    # Send individual responses
                    for response in responses:
                        embed = discord.Embed(
                            title=f"AI {response['role'].upper()}",
                            description=response['response'],
                            color=discord.Color.green()
                        )
                        await ctx.send(embed=embed)
                    
                    # Log the discussion
                    await db.log_activity(
                        str(ctx.author.id),
                        "team_discuss",
                        f"Team discussion about: {topic[:100]}..."
                    )
                else:
                    await ctx.send("❌ Failed to facilitate team discussion.")

        except Exception as e:
            logger.error(f"Error in team_discuss command: {str(e)}")
            await ctx.send("❌ An error occurred during the team discussion.")

    @commands.has_permissions(manage_messages=True)
    @commands.command(name="task_analysis")
    async def task_analysis(self, ctx, ticket_id: str):
        """Get AI team analysis of a specific task/ticket"""
        try:
            # Get ticket details
            ticket = await ticket_manager.get_ticket(ticket_id)
            if not ticket:
                await ctx.send("❌ Ticket not found.")
                return

            async with ctx.typing():
                context = await self.get_context_data(ctx)
                context["current_task"] = ticket_id
                
                # Define analysis roles and their focus
                analysts = [
                    (PersonalityType.CTO, "Strategic Overview"),
                    (PersonalityType.UX_DESIGNER, "User Experience Impact"),
                    (PersonalityType.UI_DESIGNER, "Visual Design Requirements"),
                    (PersonalityType.DEVELOPER, "Implementation Plan"),
                    (PersonalityType.TESTER, "Testing Strategy")
                ]
                
                # Create main embed for ticket
                main_embed = discord.Embed(
                    title=f"Task Analysis: #{ticket_id}",
                    description=f"Title: {ticket['title']}\nDescription: {ticket['description']}",
                    color=discord.Color.blue()
                )
                await ctx.send(embed=main_embed)
                
                # Get analysis from each role
                for personality_type, analysis_type in analysts:
                    conversation_id = self.get_conversation_id(ctx, personality_type.value)
                    response = await conversation_manager.get_task_response(
                        conversation_id=conversation_id,
                        personality_type=personality_type,
                        task_description=f"{ticket['title']}\n{ticket['description']}",
                        context=context
                    )
                    
                    if response:
                        embed = discord.Embed(
                            title=analysis_type,
                            description=response,
                            color=discord.Color.green()
                        )
                        embed.set_footer(text=f"Analysis by AI {personality_type.value.upper()}")
                        await ctx.send(embed=embed)

        except Exception as e:
            logger.error(f"Error in task_analysis command: {str(e)}")
            await ctx.send("❌ An error occurred while analyzing the task.")

    @commands.has_permissions(manage_messages=True)
    @commands.command(name="clear_chat")
    async def clear_chat(self, ctx, role: Optional[str] = None):
        """Clear chat history with an AI team member or all members"""
        try:
            if role:
                try:
                    PersonalityType(role.lower())  # Validate role
                    conversation_id = self.get_conversation_id(ctx, role)
                    conversation_manager.clear_conversation(conversation_id)
                    await ctx.send(f"✅ Chat history cleared for AI {role.upper()}")
                except ValueError:
                    await ctx.send("❌ Invalid role specified.")
            else:
                # Clear all conversations for this channel
                for personality_type in PersonalityType:
                    conversation_id = self.get_conversation_id(ctx, personality_type.value)
                    conversation_manager.clear_conversation(conversation_id)
                await ctx.send("✅ Chat history cleared for all AI team members")

            await db.log_activity(
                str(ctx.author.id),
                "clear_chat",
                f"Cleared chat history for {role if role else 'all roles'}"
            )

        except Exception as e:
            logger.error(f"Error in clear_chat command: {str(e)}")
            await ctx.send("❌ An error occurred while clearing chat history.")

async def setup(bot):
    await bot.add_cog(AITeamManager(bot))