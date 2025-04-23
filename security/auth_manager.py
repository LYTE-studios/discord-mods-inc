import jwt
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
        self.token_blacklist = set()
        self.rate_limits = defaultdict(list)
        self.fernet = Fernet(settings.ENCRYPTION_KEY.encode())

    async def create_token(self, user_id: str, roles: List[str]) -> str:
        """Create a JWT token"""
        try:
            if not user_id or not roles:
                logger.error("Invalid user_id or roles for token creation")
                return None
            
            payload = {
                'user_id': user_id,
                'roles': roles,
                'exp': datetime.utcnow() + timedelta(hours=settings.JWT_EXPIRATION_HOURS),
                'iat': datetime.utcnow()
            }
            
            token = jwt.encode(
                payload,
                settings.JWT_SECRET_KEY,
                algorithm=settings.JWT_ALGORITHM
            )
            
            await self.log_auth_event(
                user_id=user_id,
                event_type='token_created',
                details='JWT token created successfully'
            )
            
            return token

        except Exception as e:
            logger.error(f"Failed to create token: {str(e)}")
            return None

    async def verify_token(self, token: str) -> Optional[Dict]:
        """Verify a JWT token"""
        try:
            if not token or token in self.token_blacklist:
                return None
            
            payload = jwt.decode(
                token,
                settings.JWT_SECRET_KEY,
                algorithms=[settings.JWT_ALGORITHM]
            )
            
            return payload

        except jwt.ExpiredSignatureError:
            logger.warning("Token has expired")
            return None
        except jwt.InvalidTokenError:
            logger.warning("Invalid token")
            return None
        except Exception as e:
            logger.error(f"Failed to verify token: {str(e)}")
            return None

    async def revoke_token(self, token: str) -> bool:
        """Revoke a JWT token"""
        try:
            if not token:
                return False
            
            # Verify token is valid before revoking
            if await self.verify_token(token):
                self.token_blacklist.add(token)
                return True
            
            return False

        except Exception as e:
            logger.error(f"Failed to revoke token: {str(e)}")
            return False

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

    async def log_auth_event(
        self,
        user_id: str,
        event_type: str,
        details: str
    ) -> None:
        """Log authentication events"""
        try:
            if not user_id or not event_type or not details:
                return
            
            event = {
                'user_id': user_id,
                'event_type': event_type,
                'details': details,
                'timestamp': datetime.utcnow().isoformat()
            }
            
            await db.table('auth_logs').insert(event).execute()

        except Exception as e:
            logger.error(f"Failed to log auth event: {str(e)}")

    async def get_auth_logs(
        self,
        user_id: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> List[Dict]:
        """Get authentication logs with optional filters"""
        try:
            query = db.table('auth_logs').select('*')
            
            if user_id:
                query = query.eq('user_id', user_id)
            
            if start_time:
                query = query.gte('timestamp', start_time.isoformat())
            
            if end_time:
                query = query.lte('timestamp', end_time.isoformat())
            
            result = await query.execute()
            return result.data

        except Exception as e:
            logger.error(f"Failed to get auth logs: {str(e)}")
            return []