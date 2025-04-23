from supabase import create_client, Client
from typing import Optional, List, Dict
import os
from config import settings
from utils.logger import logger

class SupabaseManager:
    def __init__(self, is_test: bool = False):
        """Initialize Supabase client"""
        try:
            if is_test:
                # Use mock client for testing
                self.client = None
                return

            if not settings.SUPABASE_URL or not settings.SUPABASE_KEY:
                logger.warning("Supabase credentials not provided, running in offline mode")
                self.client = None
                return

            self.client: Client = create_client(
                settings.SUPABASE_URL,
                settings.SUPABASE_KEY
            )
            logger.info("Supabase client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Supabase client: {str(e)}")
            self.client = None

    async def create_user(self, discord_id: str, username: str) -> Optional[Dict]:
        """Create a new user in the database"""
        try:
            if not self.client:
                logger.warning("Supabase client not initialized, skipping database operation")
                return None

            response = await self.client.table('users').insert({
                'discord_id': discord_id,
                'username': username,
                'created_at': 'now()'
            }).execute()
            logger.info(f"Created user record for {username}")
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Failed to create user: {str(e)}")
            return None

    async def get_user(self, discord_id: str) -> Optional[Dict]:
        """Retrieve user data from the database"""
        try:
            if not self.client:
                logger.warning("Supabase client not initialized, skipping database operation")
                return None

            response = await self.client.table('users').select('*').eq('discord_id', discord_id).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Failed to retrieve user: {str(e)}")
            return None

    async def log_activity(self, user_id: str, activity_type: str, details: str) -> Optional[Dict]:
        """Log user activity in the database"""
        try:
            if not self.client:
                logger.warning("Supabase client not initialized, skipping database operation")
                return None

            response = await self.client.table('activity_logs').insert({
                'user_id': user_id,
                'activity_type': activity_type,
                'details': details,
                'created_at': 'now()'
            }).execute()
            logger.debug(f"Logged activity for user {user_id}: {activity_type}")
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Failed to log activity: {str(e)}")
            return None

    async def create_team(self, name: str, owner_id: str) -> Optional[Dict]:
        """Create a new team in the database"""
        try:
            if not self.client:
                logger.warning("Supabase client not initialized, skipping database operation")
                return None

            response = await self.client.table('teams').insert({
                'name': name,
                'owner_id': owner_id,
                'created_at': 'now()'
            }).execute()
            logger.info(f"Created team: {name}")
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Failed to create team: {str(e)}")
            return None

# Initialize database client for production
db = SupabaseManager()

# Function to get test database client
def get_test_db() -> SupabaseManager:
    """Get a test database client"""
    return SupabaseManager(is_test=True)