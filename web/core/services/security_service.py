"""
Security service module for authentication and security functionality
"""
from typing import Optional
from django.contrib.auth import get_user_model
from django.conf import settings
import jwt
from datetime import datetime, timedelta

User = get_user_model()

class SecurityService:
    def __init__(self):
        self.secret_key = settings.JWT_SECRET_KEY
        self.token_lifetime = timedelta(days=1)  # Token expires in 1 day

    def generate_token(self, user_id: int) -> str:
        """
        Generate JWT token for user
        """
        payload = {
            'user_id': user_id,
            'exp': datetime.utcnow() + self.token_lifetime,
            'iat': datetime.utcnow()
        }
        return jwt.encode(payload, self.secret_key, algorithm='HS256')

    def verify_token(self, token: str) -> Optional[dict]:
        """
        Verify JWT token and return payload if valid
        """
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=['HS256'])
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None

    def get_user_from_token(self, token: str) -> Optional[User]:
        """
        Get user from JWT token
        """
        payload = self.verify_token(token)
        if not payload:
            return None

        try:
            user = User.objects.get(id=payload['user_id'])
            return user
        except User.DoesNotExist:
            return None

    def check_password_strength(self, password: str) -> dict:
        """
        Check password strength
        """
        score = 0
        feedback = []

        if len(password) >= 8:
            score += 1
        else:
            feedback.append("Password should be at least 8 characters long")

        if any(c.isupper() for c in password):
            score += 1
        else:
            feedback.append("Password should contain at least one uppercase letter")

        if any(c.islower() for c in password):
            score += 1
        else:
            feedback.append("Password should contain at least one lowercase letter")

        if any(c.isdigit() for c in password):
            score += 1
        else:
            feedback.append("Password should contain at least one number")

        if any(not c.isalnum() for c in password):
            score += 1
        else:
            feedback.append("Password should contain at least one special character")

        return {
            'score': score,
            'strength': ['Very Weak', 'Weak', 'Fair', 'Good', 'Strong'][min(score, 4)],
            'feedback': feedback
        }

security_service = SecurityService()