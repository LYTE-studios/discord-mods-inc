from datetime import datetime, timedelta
import hmac
import hashlib
from typing import Optional, Dict, List
from cryptography.fernet import Fernet
from collections import defaultdict
from config import settings
from utils.logger import logger
from database.supabase_client import db

class AuthManager:
    """Manages authentication and authorization"""
    
    def __init__(self):
        """Initialize AuthManager"""
        self.rate_limits = defaultdict(list)
        self.fernet = Fernet(settings.ENCRYPTION_KEY.encode())

    async def verify_permissions(self, user_id: str, required_roles: List[str]) -> bool:
        """Verify user permissions"""
        try:
            if not user_id or not required_roles:
                return False
            
            # Get user roles from database
            result = await db.table('users').select('roles').eq('id', user_id).execute()
            
            if not result.data:
                return False
            
            user_roles = result.data[0]['roles']
            
            # Check if user has any of the required roles
            return any(role in user_roles for role in required_roles)

        except Exception as e:
            logger.error(f"Failed to verify permissions: {str(e)}")
            return False

    async def check_rate_limit(self, user_id: str) -> bool:
        """Check rate limiting for a user"""
        try:
            if not user_id:
                return False
            
            now = datetime.utcnow()
            window_start = now - timedelta(seconds=settings.RATE_LIMIT_PERIOD)
            
            # Clean up old entries
            self.rate_limits[user_id] = [
                ts for ts in self.rate_limits[user_id]
                if ts > window_start
            ]
            
            # Check if under limit
            if len(self.rate_limits[user_id]) < settings.RATE_LIMIT_CALLS:
                self.rate_limits[user_id].append(now)
                return True
            
            return False

        except Exception as e:
            logger.error(f"Failed to check rate limit: {str(e)}")
            return False

    def encrypt_data(self, data: str) -> bytes:
        """Encrypt sensitive data"""
        try:
            if not data:
                raise ValueError("Data cannot be empty")
            
            return self.fernet.encrypt(data.encode())

        except Exception as e:
            logger.error(f"Failed to encrypt data: {str(e)}")
            raise

    def decrypt_data(self, encrypted_data: bytes) -> str:
        """Decrypt encrypted data"""
        try:
            if not encrypted_data:
                raise ValueError("Encrypted data cannot be empty")
            
            return self.fernet.decrypt(encrypted_data).decode()

        except Exception as e:
            logger.error(f"Failed to decrypt data: {str(e)}")
            raise

    def verify_signature(self, payload: bytes, signature: str, secret: str) -> bool:
        """Verify webhook signature"""
        try:
            if not payload or not signature or not secret:
                return False
            
            expected_signature = hmac.new(
                secret.encode(),
                payload,
                hashlib.sha256
            ).hexdigest()
            
            return hmac.compare_digest(signature, expected_signature)

        except Exception as e:
            logger.error(f"Failed to verify signature: {str(e)}")
            return False