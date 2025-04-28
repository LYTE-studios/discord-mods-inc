import discord
from discord.ext import commands
from typing import Optional, List
from datetime import datetime, timezone
import asyncio
from config import settings
from utils.logger import logger
from database.supabase_client import db
from tickets.ticket_manager import ticket_manager
from tickets.ticket_types import (
    Ticket, TicketStatus, TicketPriority, TicketType,
    format_ticket_for_discord
)

class TicketManagerCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.notification_task = self.bot.loop.create_task(self.check_notifications())

    async def check_notifications(self):
        """Check for new notifications periodically"""
        try:
            while not self.bot.is_closed():
                notifications = await db.table('ticket_notifications').select('*').eq('read', False).execute()
                
                for notification in notifications.data:
                    channel = self.bot.get_channel(int(settings.TICKET_NOTIFICATIONS_CHANNEL))
                    if channel:
                        embed = discord.Embed(
                            title="Ticket Notification",
                            description=notification["message"],
                            color=discord.Color.blue()
                        )
                        await channel.send(f"<@{notification['user_id']}>", embed=embed)
                        
                        # Mark as read
                        await db.table('ticket_notifications').update(
                            {'read': True}
                        ).eq('id', notification['id']).execute()

                await asyncio.sleep(60)  # Check every minute
        except Exception as e:
            logger.error(f"Error in notification checker: {str(e)}")

    @commands.has_permissions(manage_messages=True)
    @commands.command(name="create_ticket")
    async def create_ticket(
        self,
        ctx,
        ticket_type: str,
        priority: str,
        title: str,
        *,
        description: str
    ):
        """Create a new ticket"""
        try:
            # Validate ticket type
            try:
                ticket_type = TicketType(ticket_type.lower())
            except ValueError:
                await ctx.send("❌ Invalid ticket type. Use: feature, bug, task, improvement, or documentation")
                return

            # Validate priority
            try:
                priority = TicketPriority(priority.lower())
            except ValueError:
                await ctx.send("❌ Invalid priority. Use: low, medium, high, or urgent")
                return

            ticket = await ticket_manager.create_ticket(
                title=title,
                description=description,
                creator_id=str(ctx.author.id),
                ticket_type=ticket_type,
                priority=priority
            )

            embed = discord.Embed(**format_ticket_for_discord(ticket))
            await ctx.send("✅ Ticket created!", embed=embed)

        except Exception as e:
            logger.error(f"Error creating ticket: {str(e)}")
            await ctx.send("❌ Failed to create ticket. Please check the logs.")

    @commands.has_permissions(manage_messages=True)
    @commands.command(name="assign_ticket")
    async def assign_ticket(self, ctx, ticket_id: str, members: commands.Greedy[discord.Member]):
        """Assign users to a ticket"""
        try:
            assignees = [str(member.id) for member in members]
            
            await ticket_manager.update_ticket(
                ticket_id=ticket_id,
                updates={"assignees": [
                    {"user_id": user_id, "assigned_by": str(ctx.author.id)}
                    for user_id in assignees
                ]},
                updated_by=str(ctx.author.id)
            )

            mentions = ", ".join(member.mention for member in members)
            await ctx.send(f"✅ Assigned {mentions} to ticket #{ticket_id}")

        except Exception as e:
            logger.error(f"Error assigning ticket: {str(e)}")
            await ctx.send("❌ Failed to assign ticket. Please check the logs.")

    @commands.has_permissions(manage_messages=True)
    @commands.command(name="update_status")
    async def update_status(self, ctx, ticket_id: str, status: str):
        """Update ticket status"""
        try:
            try:
                new_status = TicketStatus(status.lower())
            except ValueError:
                statuses = ", ".join(s.value for s in TicketStatus)
                await ctx.send(f"❌ Invalid status. Use: {statuses}")
                return

            ticket = await ticket_manager.update_ticket(
                ticket_id=ticket_id,
                updates={"status": new_status},
                updated_by=str(ctx.author.id)
            )

            embed = discord.Embed(**format_ticket_for_discord(ticket))
            await ctx.send("✅ Status updated!", embed=embed)

        except Exception as e:
            logger.error(f"Error updating ticket status: {str(e)}")
            await ctx.send("❌ Failed to update status. Please check the logs.")

    @commands.has_permissions(manage_messages=True)
    @commands.command(name="add_comment")
    async def add_comment(self, ctx, ticket_id: str, *, comment: str):
        """Add a comment to a ticket"""
        try:
            await ticket_manager.add_comment(
                ticket_id=ticket_id,
                author_id=str(ctx.author.id),
                content=comment
            )

            await ctx.send(f"✅ Comment added to ticket #{ticket_id}")

        except Exception as e:
            logger.error(f"Error adding comment: {str(e)}")
            await ctx.send("❌ Failed to add comment. Please check the logs.")

    @commands.has_permissions(manage_messages=True)
    @commands.command(name="list_tickets")
    async def list_tickets(
        self,
        ctx,
        status: Optional[str] = None,
        priority: Optional[str] = None
    ):
        """List tickets with optional filters"""
        try:
            # Validate status if provided
            ticket_status = None
            if status:
                try:
                    ticket_status = TicketStatus(status.lower())
                except ValueError:
                    statuses = ", ".join(s.value for s in TicketStatus)
                    await ctx.send(f"❌ Invalid status. Use: {statuses}")
                    return

            # Validate priority if provided
            ticket_priority = None
            if priority:
                try:
                    ticket_priority = TicketPriority(priority.lower())
                except ValueError:
                    priorities = ", ".join(p.value for p in TicketPriority)
                    await ctx.send(f"❌ Invalid priority. Use: {priorities}")
                    return

            tickets = await ticket_manager.list_tickets(
                status=ticket_status,
                priority=ticket_priority
            )

            if not tickets:
                await ctx.send("No tickets found matching the criteria.")
                return

            # Create paginated embeds for tickets
            tickets_per_page = 5
            pages = []
            
            for i in range(0, len(tickets), tickets_per_page):
                page_tickets = tickets[i:i + tickets_per_page]
                embed = discord.Embed(
                    title="Ticket List",
                    color=discord.Color.blue()
                )
                
                for ticket in page_tickets:
                    ticket_obj = Ticket(**ticket)
                    assignees = ", ".join(f"<@{a['user_id']}>" for a in ticket["assignees"]) or "None"
                    
                    embed.add_field(
                        name=f"#{ticket['id']}: {ticket['title']}",
                        value=f"Status: {ticket['status']}\n"
                              f"Priority: {ticket['priority']}\n"
                              f"Assignees: {assignees}",
                        inline=False
                    )
                
                pages.append(embed)

            # Send first page
            current_page = 0
            message = await ctx.send(embed=pages[current_page])

            # Add navigation reactions
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
            logger.error(f"Error listing tickets: {str(e)}")
            await ctx.send("❌ Failed to list tickets. Please check the logs.")

    @commands.has_permissions(manage_messages=True)
    @commands.command(name="ticket_report")
    async def ticket_report(self, ctx):
        """Generate a ticket statistics report"""
        try:
            report = await ticket_manager.generate_report()
            
            embed = discord.Embed(
                title="Ticket Statistics Report",
                color=discord.Color.blue(),
                timestamp=report.generated_at
            )
            
            embed.add_field(
                name="Overview",
                value=f"Total Tickets: {report.total_tickets}\n"
                      f"Open Tickets: {report.open_tickets}\n"
                      f"Completed Tickets: {report.completed_tickets}\n"
                      f"Overdue Tickets: {report.overdue_tickets}",
                inline=False
            )
            
            if report.average_completion_time:
                embed.add_field(
                    name="Average Completion Time",
                    value=f"{report.average_completion_time:.1f} hours",
                    inline=False
                )
            
            # Format distribution data
            for field, data in [
                ("Priority Distribution", report.tickets_by_priority),
                ("Status Distribution", report.tickets_by_status),
                ("Type Distribution", report.tickets_by_type)
            ]:
                value = "\n".join(f"{k}: {v}" for k, v in data.items())
                embed.add_field(name=field, value=value or "No data", inline=True)
            
            await ctx.send(embed=embed)

        except Exception as e:
            logger.error(f"Error generating report: {str(e)}")
            await ctx.send("❌ Failed to generate report. Please check the logs.")

    def cog_unload(self):
        """Cleanup when cog is unloaded"""
        self.notification_task.cancel()

async def setup(bot):
    await bot.add_cog(TicketManagerCog(bot))