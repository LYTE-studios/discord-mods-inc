import jwt
from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import authentication
from rest_framework.exceptions import AuthenticationFailed

User = get_user_model()

class SupabaseAuthBackend(authentication.BaseAuthentication):
    """
    Custom authentication backend for Supabase JWT tokens
    """
    
    def authenticate(self, request):
        auth_header = request.META.get('HTTP_AUTHORIZATION')
        if not auth_header or not auth_header.startswith('Bearer '):
            return None

        token = auth_header.split(' ')[1]
        try:
            # Verify the JWT token using the Supabase JWT secret
            payload = jwt.decode(
                token,
                settings.SUPABASE_JWT_SECRET,
                algorithms=['HS256']
            )
            
            # Get or create user based on Supabase UID
            user, created = User.objects.get_or_create(
                supabase_uid=payload['sub'],
                defaults={
                    'username': payload.get('email', ''),
                    'email': payload.get('email', ''),
                }
            )
            
            # Update last login
            user.last_login_at = timezone.now()
            user.save(update_fields=['last_login_at'])
            
            return (user, token)
            
        except jwt.ExpiredSignatureError:
            raise AuthenticationFailed('Token has expired')
        except jwt.InvalidTokenError:
            raise AuthenticationFailed('Invalid token')
        except User.DoesNotExist:
            raise AuthenticationFailed('User not found')

    def authenticate_header(self, request):
        return 'Bearer'