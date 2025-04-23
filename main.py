import discord
from discord.ext import commands
import asyncio
import os
from config import settings
from utils.logger import setup_logger, logger
from database.supabase_client import db

# Initialize logger
logger = setup_logger()

# Bot setup with intents
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True

bot = commands.Bot(
    command_prefix="!",
    intents=intents,
    help_command=commands.DefaultHelpCommand()
)

# Error handling
@bot.event
async def on_error(event, *args, **kwargs):
    logger.error(f"Error in {event}: {args} {kwargs}")

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.errors.MissingPermissions):
        await ctx.send("❌ You don't have permission to use this command.")
    elif isinstance(error, commands.errors.MissingRequiredArgument):
        await ctx.send("❌ Missing required argument. Please check the command usage.")
    elif isinstance(error, commands.errors.CommandNotFound):
        await ctx.send("❌ Command not found. Use !help to see available commands.")
    else:
        logger.error(f"Command error: {str(error)}")
        await ctx.send("❌ An error occurred while executing the command.")

@bot.event
async def on_ready():
    logger.info(f"Bot is ready! Logged in as {bot.user.name}")
    
    # Set bot status
    await bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.watching,
            name="AI development teams"
        )
    )
    
    try:
        # Load all cogs
        cogs_dir = "cogs"
        for filename in os.listdir(cogs_dir):
            if filename.endswith(".py"):
                cog_name = f"{cogs_dir}.{filename[:-3]}"
                try:
                    await bot.load_extension(cog_name)
                    logger.info(f"Loaded extension: {cog_name}")
                except Exception as e:
                    logger.error(f"Failed to load extension {cog_name}: {str(e)}")
    except Exception as e:
        logger.error(f"Error loading cogs: {str(e)}")

@bot.event
async def on_member_join(member):
    try:
        # Create user record in database
        await db.create_user(str(member.id), member.name)
        
        # Log the event
        await db.log_activity(
            str(member.id),
            "member_join",
            f"User {member.name} joined the server"
        )
        
        # Send welcome message
        welcome_channel = discord.utils.get(member.guild.channels, name="general")
        if welcome_channel:
            await welcome_channel.send(f"Welcome {member.mention} to the AI Development Team! 🚀")
    except Exception as e:
        logger.error(f"Error handling member join: {str(e)}")

@bot.command(name="ping")
async def ping(ctx):
    """Check bot's latency"""
    try:
        latency = round(bot.latency * 1000)
        await ctx.send(f"🏓 Pong! Latency: {latency}ms")
    except Exception as e:
        logger.error(f"Error in ping command: {str(e)}")
        await ctx.send("❌ Failed to get latency.")

def main():
    try:
        logger.info("Starting bot...")
        bot.run(settings.DISCORD_TOKEN)
    except Exception as e:
        logger.error(f"Failed to start bot: {str(e)}")
        raise

if __name__ == "__main__":
    main()