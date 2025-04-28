import discord
from discord.ext import commands
from typing import Optional
from datetime import datetime, timedelta
import asyncio
from config import settings
from utils.logger import logger
from database.supabase_client import db
from security.auth_manager import auth_manager
from monitoring.monitor_manager import monitor_manager

class MonitorManagerCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.start_monitoring()

    def start_monitoring(self):
        """Start the monitoring system"""
        asyncio.create_task(monitor_manager.start_monitoring())

    def create_metrics_embed(self, metrics: dict) -> discord.Embed:
        """Create embed for system metrics"""
        embed = discord.Embed(
            title="System Metrics",
            color=discord.Color.blue(),
            timestamp=datetime.utcnow()
        )
        
        # CPU and Memory
        embed.add_field(
            name="CPU Usage",
            value=f"{metrics['cpu_usage']:.1f}%",
            inline=True
        )
        embed.add_field(
            name="Memory Usage",
            value=f"{metrics['memory_usage']:.1f}%",
            inline=True
        )
        embed.add_field(
            name="Disk Usage",
            value=f"{metrics['disk_usage']:.1f}%",
            inline=True
        )
        
        return embed

    def create_health_embed(self, health: dict) -> discord.Embed:
        """Create embed for system health"""
        status_colors = {
            'healthy': discord.Color.green(),
            'warning': discord.Color.orange(),
            'error': discord.Color.red()
        }
        
        embed = discord.Embed(
            title="System Health Status",
            color=status_colors.get(health['status'], discord.Color.default()),
            timestamp=datetime.utcnow()
        )
        
        # Status and Metrics
        embed.add_field(
            name="Status",
            value=health['status'].upper(),
            inline=False
        )
        
        # Performance Metrics
        performance = health['performance']
        embed.add_field(
            name="Performance",
            value=f"Command Latency: {performance['avg_command_latency']:.2f}ms\n"
                  f"API Latency: {performance['avg_api_latency']:.2f}ms\n"
                  f"Error Rate: {performance['error_rate']:.2f}%",
            inline=False
        )
        
        # Active Alerts
        if health['active_alerts']:
            alerts_text = "\n".join(
                f"• {alert['type']}: {alert['message']}"
                for alert in health['active_alerts'][:5]
            )
            if len(health['active_alerts']) > 5:
                alerts_text += f"\n...and {len(health['active_alerts']) - 5} more"
            
            embed.add_field(
                name="Active Alerts",
                value=alerts_text,
                inline=False
            )
        
        return embed

    @commands.has_permissions(administrator=True)
    @commands.command(name="system_status")
    async def system_status(self, ctx):
        """Get current system status"""
        try:
            # Verify permissions
            if not await auth_manager.verify_permissions(
                str(ctx.author.id),
                ['admin', 'monitor']
            ):
                await ctx.send("❌ You don't have permission to use this command.")
                return

            # Check rate limit
            if not await auth_manager.check_rate_limit(str(ctx.author.id)):
                await ctx.send("❌ Rate limit exceeded. Please try again later.")
                return

            async with ctx.typing():
                health = await monitor_manager.get_system_health()
                embed = self.create_health_embed(health)
                await ctx.send(embed=embed)

        except Exception as e:
            logger.error(f"Error in system_status command: {str(e)}")
            await ctx.send("❌ Failed to get system status.")

    @commands.has_permissions(administrator=True)
    @commands.command(name="metrics")
    async def metrics(self, ctx):
        """Get current system metrics"""
        try:
            # Verify permissions
            if not await auth_manager.verify_permissions(
                str(ctx.author.id),
                ['admin', 'monitor']
            ):
                await ctx.send("❌ You don't have permission to use this command.")
                return

            # Check rate limit
            if not await auth_manager.check_rate_limit(str(ctx.author.id)):
                await ctx.send("❌ Rate limit exceeded. Please try again later.")
                return

            async with ctx.typing():
                metrics = await monitor_manager.metrics_collector.collect_system_metrics()
                embed = self.create_metrics_embed(metrics)
                await ctx.send(embed=embed)

        except Exception as e:
            logger.error(f"Error in metrics command: {str(e)}")
            await ctx.send("❌ Failed to get system metrics.")

    @commands.has_permissions(administrator=True)
    @commands.command(name="active_alerts")
    async def active_alerts(self, ctx):
        """Get current active alerts"""
        try:
            # Verify permissions
            if not await auth_manager.verify_permissions(
                str(ctx.author.id),
                ['admin', 'monitor']
            ):
                await ctx.send("❌ You don't have permission to use this command.")
                return

            # Check rate limit
            if not await auth_manager.check_rate_limit(str(ctx.author.id)):
                await ctx.send("❌ Rate limit exceeded. Please try again later.")
                return

            async with ctx.typing():
                alerts = monitor_manager.alert_manager.active_alerts
                
                if not alerts:
                    await ctx.send("✅ No active alerts.")
                    return

                embed = discord.Embed(
                    title="Active Alerts",
                    color=discord.Color.red(),
                    timestamp=datetime.utcnow()
                )
                
                for alert_id, alert in alerts.items():
                    embed.add_field(
                        name=f"{alert['type']} ({alert['severity']})",
                        value=alert['message'],
                        inline=False
                    )
                
                await ctx.send(embed=embed)

        except Exception as e:
            logger.error(f"Error in active_alerts command: {str(e)}")
            await ctx.send("❌ Failed to get active alerts.")

    @commands.has_permissions(administrator=True)
    @commands.command(name="performance")
    async def performance(self, ctx):
        """Get system performance metrics"""
        try:
            # Verify permissions
            if not await auth_manager.verify_permissions(
                str(ctx.author.id),
                ['admin', 'monitor']
            ):
                await ctx.send("❌ You don't have permission to use this command.")
                return

            # Check rate limit
            if not await auth_manager.check_rate_limit(str(ctx.author.id)):
                await ctx.send("❌ Rate limit exceeded. Please try again later.")
                return

            async with ctx.typing():
                health = await monitor_manager.get_system_health()
                performance = health['performance']
                
                embed = discord.Embed(
                    title="System Performance",
                    color=discord.Color.blue(),
                    timestamp=datetime.utcnow()
                )
                
                embed.add_field(
                    name="Command Latency",
                    value=f"{performance['avg_command_latency']:.2f}ms",
                    inline=True
                )
                embed.add_field(
                    name="API Latency",
                    value=f"{performance['avg_api_latency']:.2f}ms",
                    inline=True
                )
                embed.add_field(
                    name="Error Rate",
                    value=f"{performance['error_rate']:.2f}%",
                    inline=True
                )
                
                await ctx.send(embed=embed)

        except Exception as e:
            logger.error(f"Error in performance command: {str(e)}")
            await ctx.send("❌ Failed to get performance metrics.")

    def cog_unload(self):
        """Cleanup when cog is unloaded"""
        asyncio.create_task(monitor_manager.stop_monitoring())

async def setup(bot):
    await bot.add_cog(MonitorManagerCog(bot))