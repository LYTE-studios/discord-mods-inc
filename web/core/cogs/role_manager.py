import discord
from discord.ext import commands
from config import settings
from utils.logger import logger
from database.supabase_client import db

class RoleManager(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.has_permissions(manage_roles=True)
    @commands.command(name="create_role")
    async def create_role(self, ctx, role_name: str, color: discord.Color = discord.Color.default()):
        """Create a new role"""
        try:
            role = await ctx.guild.create_role(
                name=role_name,
                color=color,
                reason=f"Role created by {ctx.author}"
            )
            await db.log_activity(
                str(ctx.author.id),
                "role_create",
                f"Created role: {role_name}"
            )
            logger.info(f"Role created: {role_name} by {ctx.author}")
            await ctx.send(f"✅ Role {role.mention} created successfully!")
        except Exception as e:
            logger.error(f"Failed to create role: {str(e)}")
            await ctx.send("❌ Failed to create role. Please check the logs.")

    @commands.has_permissions(manage_roles=True)
    @commands.command(name="assign_role")
    async def assign_role(self, ctx, member: discord.Member, role: discord.Role):
        """Assign a role to a member"""
        try:
            await member.add_roles(role)
            await db.log_activity(
                str(ctx.author.id),
                "role_assign",
                f"Assigned role {role.name} to {member.name}"
            )
            logger.info(f"Role {role.name} assigned to {member.name} by {ctx.author}")
            await ctx.send(f"✅ Role {role.mention} assigned to {member.mention}!")
        except Exception as e:
            logger.error(f"Failed to assign role: {str(e)}")
            await ctx.send("❌ Failed to assign role. Please check the logs.")

    @commands.has_permissions(manage_roles=True)
    @commands.command(name="remove_role")
    async def remove_role(self, ctx, member: discord.Member, role: discord.Role):
        """Remove a role from a member"""
        try:
            await member.remove_roles(role)
            await db.log_activity(
                str(ctx.author.id),
                "role_remove",
                f"Removed role {role.name} from {member.name}"
            )
            logger.info(f"Role {role.name} removed from {member.name} by {ctx.author}")
            await ctx.send(f"✅ Role {role.mention} removed from {member.mention}!")
        except Exception as e:
            logger.error(f"Failed to remove role: {str(e)}")
            await ctx.send("❌ Failed to remove role. Please check the logs.")

    @commands.has_permissions(manage_roles=True)
    @commands.command(name="setup_default_roles")
    async def setup_default_roles(self, ctx):
        """Create default AI team roles"""
        try:
            created_roles = []
            for role_name in settings.DEFAULT_ROLES:
                role = await ctx.guild.create_role(
                    name=role_name,
                    color=discord.Color.blue(),
                    reason="Default AI team role setup"
                )
                created_roles.append(role)
            
            await db.log_activity(
                str(ctx.author.id),
                "default_roles_setup",
                "Created default AI team roles"
            )
            logger.info(f"Default roles created by {ctx.author}")
            roles_mention = ", ".join([role.mention for role in created_roles])
            await ctx.send(f"✅ Default AI team roles created: {roles_mention}")
        except Exception as e:
            logger.error(f"Failed to setup default roles: {str(e)}")
            await ctx.send("❌ Failed to setup default roles. Please check the logs.")

async def setup(bot):
    await bot.add_cog(RoleManager(bot))