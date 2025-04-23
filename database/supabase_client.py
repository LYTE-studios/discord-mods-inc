from supabase import create_client, Client
import asyncpg
from typing import Optional, List, Dict
import os
from config import settings
from utils.logger import logger

class SupabaseManager:
    def __init__(self, is_test: bool = False):
        """Initialize database client"""
        try:
            if is_test:
                # Use mock client for testing
                self.client = None
                self.pool = None
                return

            # Check if we're using local PostgreSQL
            if settings.POSTGRES_HOST and settings.POSTGRES_PORT:
                self.use_local = True
                self.pool = None  # Will be initialized when needed
            else:
                self.use_local = False
                if not settings.SUPABASE_URL or not settings.SUPABASE_KEY:
                    logger.warning("Database credentials not provided, running in offline mode")
                    self.client = None
                    return

                self.client: Client = create_client(
                    settings.SUPABASE_URL,
                    settings.SUPABASE_KEY
                )
                logger.info("Supabase client initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize database client: {str(e)}")
            self.client = None
            self.pool = None

    async def get_pool(self):
        """Get or create connection pool for local PostgreSQL"""
        if not self.use_local:
            return None

        if self.pool is None:
            try:
                self.pool = await asyncpg.create_pool(
                    host=settings.POSTGRES_HOST,
                    port=settings.POSTGRES_PORT,
                    user=settings.POSTGRES_USER,
                    password=settings.POSTGRES_PASSWORD,
                    database=settings.POSTGRES_DB
                )
                logger.info("PostgreSQL connection pool initialized successfully")
            except Exception as e:
                logger.error(f"Failed to create PostgreSQL connection pool: {str(e)}")
                return None
        return self.pool

    async def create_user(self, discord_id: str, username: str) -> Optional[Dict]:
        """Create a new user in the database"""
        try:
            if self.use_local:
                pool = await self.get_pool()
                if not pool:
                    logger.warning("Database pool not initialized, skipping operation")
                    return None

                async with pool.acquire() as conn:
                    row = await conn.fetchrow(
                        """
                        INSERT INTO users (discord_id, username, created_at)
                        VALUES ($1, $2, NOW())
                        RETURNING *
                        """,
                        discord_id, username
                    )
                    return dict(row) if row else None
            else:
                if not self.client:
                    logger.warning("Database client not initialized, skipping operation")
                    return None

                response = await self.client.table('users').insert({
                    'discord_id': discord_id,
                    'username': username,
                    'created_at': 'now()'
                }).execute()
                return response.data[0] if response.data else None

        except Exception as e:
            logger.error(f"Failed to create user: {str(e)}")
            return None

    async def get_user(self, discord_id: str) -> Optional[Dict]:
        """Retrieve user data from the database"""
        try:
            if self.use_local:
                pool = await self.get_pool()
                if not pool:
                    logger.warning("Database pool not initialized, skipping operation")
                    return None

                async with pool.acquire() as conn:
                    row = await conn.fetchrow(
                        "SELECT * FROM users WHERE discord_id = $1",
                        discord_id
                    )
                    return dict(row) if row else None
            else:
                if not self.client:
                    logger.warning("Database client not initialized, skipping operation")
                    return None

                response = await self.client.table('users').select('*').eq('discord_id', discord_id).execute()
                return response.data[0] if response.data else None

        except Exception as e:
            logger.error(f"Failed to retrieve user: {str(e)}")
            return None

    async def log_activity(self, user_id: str, activity_type: str, details: str) -> Optional[Dict]:
        """Log user activity in the database"""
        try:
            if self.use_local:
                pool = await self.get_pool()
                if not pool:
                    logger.warning("Database pool not initialized, skipping operation")
                    return None

                async with pool.acquire() as conn:
                    row = await conn.fetchrow(
                        """
                        INSERT INTO activity_logs (user_id, activity_type, details, created_at)
                        VALUES ($1, $2, $3, NOW())
                        RETURNING *
                        """,
                        user_id, activity_type, details
                    )
                    return dict(row) if row else None
            else:
                if not self.client:
                    logger.warning("Database client not initialized, skipping operation")
                    return None

                response = await self.client.table('activity_logs').insert({
                    'user_id': user_id,
                    'activity_type': activity_type,
                    'details': details,
                    'created_at': 'now()'
                }).execute()
                return response.data[0] if response.data else None

        except Exception as e:
            logger.error(f"Failed to log activity: {str(e)}")
            return None

    async def create_team(self, name: str, owner_id: str) -> Optional[Dict]:
        """Create a new team in the database"""
        try:
            if self.use_local:
                pool = await self.get_pool()
                if not pool:
                    logger.warning("Database pool not initialized, skipping operation")
                    return None

                async with pool.acquire() as conn:
                    row = await conn.fetchrow(
                        """
                        INSERT INTO teams (name, owner_id, created_at)
                        VALUES ($1, $2, NOW())
                        RETURNING *
                        """,
                        name, owner_id
                    )
                    return dict(row) if row else None
            else:
                if not self.client:
                    logger.warning("Database client not initialized, skipping operation")
                    return None

                response = await self.client.table('teams').insert({
                    'name': name,
                    'owner_id': owner_id,
                    'created_at': 'now()'
                }).execute()
                return response.data[0] if response.data else None

        except Exception as e:
            logger.error(f"Failed to create team: {str(e)}")
            return None

    async def close(self):
        """Close database connections"""
        if self.pool:
            await self.pool.close()

# Initialize database client for production
db = SupabaseManager()

# Function to get test database client
def get_test_db() -> SupabaseManager:
    """Get a test database client"""
    return SupabaseManager(is_test=True)