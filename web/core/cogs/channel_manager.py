import discord
from discord.ext import commands
from config import settings
from utils.logger import logger
from database.supabase_client import db

class ChannelManager(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.has_permissions(manage_channels=True)
    @commands.command(name="create_channel")
    async def create_channel(self, ctx, channel_name: str, channel_type: str = "text"):
        """Create a new channel"""
        try:
            channel_types = {
                "text": discord.ChannelType.text,
                "voice": discord.ChannelType.voice,
                "category": discord.ChannelType.category
            }
            
            if channel_type not in channel_types:
                await ctx.send("❌ Invalid channel type. Use 'text', 'voice', or 'category'.")
                return

            channel = await ctx.guild.create_channel(
                name=channel_name,
                type=channel_types[channel_type],
                reason=f"Channel created by {ctx.author}"
            )
            
            await db.log_activity(
                str(ctx.author.id),
                "channel_create",
                f"Created {channel_type} channel: {channel_name}"
            )
            logger.info(f"Channel created: {channel_name} by {ctx.author}")
            await ctx.send(f"✅ Channel {channel.mention} created successfully!")
        except Exception as e:
            logger.error(f"Failed to create channel: {str(e)}")
            await ctx.send("❌ Failed to create channel. Please check the logs.")

    @commands.has_permissions(manage_channels=True)
    @commands.command(name="delete_channel")
    async def delete_channel(self, ctx, channel: discord.TextChannel):
        """Delete a channel"""
        try:
            channel_name = channel.name
            await channel.delete(reason=f"Channel deleted by {ctx.author}")
            await db.log_activity(
                str(ctx.author.id),
                "channel_delete",
                f"Deleted channel: {channel_name}"
            )
            logger.info(f"Channel deleted: {channel_name} by {ctx.author}")
            await ctx.send(f"✅ Channel #{channel_name} deleted successfully!")
        except Exception as e:
            logger.error(f"Failed to delete channel: {str(e)}")
            await ctx.send("❌ Failed to delete channel. Please check the logs.")

    @commands.has_permissions(manage_channels=True)
    @commands.command(name="setup_default_channels")
    async def setup_default_channels(self, ctx):
        """Create default channels for the AI team"""
        try:
            # Create a category for AI team channels
            category = await ctx.guild.create_category(
                name="AI Team",
                reason="Default AI team category setup"
            )
            
            created_channels = []
            for channel_name in settings.DEFAULT_CHANNELS:
                channel = await ctx.guild.create_text_channel(
                    name=channel_name,
                    category=category,
                    reason="Default AI team channel setup"
                )
                created_channels.append(channel)
            
            await db.log_activity(
                str(ctx.author.id),
                "default_channels_setup",
                "Created default AI team channels"
            )
            logger.info(f"Default channels created by {ctx.author}")
            
            channels_mention = ", ".join([channel.mention for channel in created_channels])
            await ctx.send(f"✅ Default AI team channels created under {category.name} category: {channels_mention}")
        except Exception as e:
            logger.error(f"Failed to setup default channels: {str(e)}")
            await ctx.send("❌ Failed to setup default channels. Please check the logs.")

    @commands.has_permissions(manage_channels=True)
    @commands.command(name="archive_channel")
    async def archive_channel(self, ctx, channel: discord.TextChannel):
        """Archive a channel by moving it to an Archive category"""
        try:
            # Find or create Archive category
            archive_category = discord.utils.get(ctx.guild.categories, name="Archive")
            if not archive_category:
                archive_category = await ctx.guild.create_category(
                    name="Archive",
                    reason="Archive category created for storing old channels"
                )
            
            await channel.edit(
                category=archive_category,
                reason=f"Channel archived by {ctx.author}"
            )
            
            await db.log_activity(
                str(ctx.author.id),
                "channel_archive",
                f"Archived channel: {channel.name}"
            )
            logger.info(f"Channel archived: {channel.name} by {ctx.author}")
            await ctx.send(f"✅ Channel {channel.mention} has been archived!")
        except Exception as e:
            logger.error(f"Failed to archive channel: {str(e)}")
            await ctx.send("❌ Failed to archive channel. Please check the logs.")

async def setup(bot):
    await bot.add_cog(ChannelManager(bot))