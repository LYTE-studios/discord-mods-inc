import pytest
from unittest.mock import patch, MagicMock, AsyncMock
import jwt
from datetime import datetime, timedelta
from security.auth_manager import AuthManager
from config import settings, Settings
from cryptography.fernet import Fernet

@pytest.fixture(autouse=True)
def setup_env(mock_env_vars):
    """Ensure environment variables are set up"""
    pass

@pytest.fixture
def auth_manager():
    """Create AuthManager instance for testing"""
    # Generate a valid Fernet key for testing
    test_key = Fernet.generate_key()
    
    # Create a mock settings instance
    mock_settings = MagicMock(spec=Settings)
    mock_settings.ENCRYPTION_KEY = test_key.decode()
    mock_settings.JWT_SECRET_KEY = 'test_jwt_secret'
    mock_settings.JWT_ALGORITHM = 'HS256'
    mock_settings.JWT_EXPIRATION_HOURS = 24
    mock_settings.RATE_LIMIT_CALLS = 100
    mock_settings.RATE_LIMIT_PERIOD = 60
    
    # Patch the settings module
    with patch('security.auth_manager.settings', mock_settings):
        return AuthManager()

@pytest.mark.asyncio
async def test_create_token(auth_manager):
    """Test JWT token creation"""
    user_id = "test_user"
    roles = ["admin", "developer"]
    
    token = await auth_manager.create_token(user_id, roles)
    assert token is not None
    
    # Decode and verify token
    payload = jwt.decode(
        token,
        settings.JWT_SECRET_KEY,
        algorithms=['HS256']
    )
    
    assert payload['user_id'] == user_id
    assert payload['roles'] == roles
    assert 'exp' in payload
    assert 'iat' in payload
    
    # Test token creation with invalid inputs
    assert await auth_manager.create_token(None, roles) is None
    assert await auth_manager.create_token(user_id, None) is None
    assert await auth_manager.create_token("", []) is None

@pytest.mark.asyncio
async def test_verify_token(auth_manager):
    """Test JWT token verification"""
    # Create a valid token
    payload = {
        'user_id': 'test_user',
        'roles': ['admin'],
        'exp': datetime.utcnow() + timedelta(hours=1),
        'iat': datetime.utcnow()
    }
    token = jwt.encode(
        payload,
        settings.JWT_SECRET_KEY,
        algorithm='HS256'
    )
    
    # Test valid token
    result = await auth_manager.verify_token(token)
    assert result is not None
    assert result['user_id'] == 'test_user'
    assert result['roles'] == ['admin']
    
    # Test expired token
    expired_payload = payload.copy()
    expired_payload['exp'] = datetime.utcnow() - timedelta(hours=1)
    expired_token = jwt.encode(
        expired_payload,
        settings.JWT_SECRET_KEY,
        algorithm='HS256'
    )
    
    result = await auth_manager.verify_token(expired_token)
    assert result is None
    
    # Test invalid token
    result = await auth_manager.verify_token("invalid_token")
    assert result is None
    
    # Test blacklisted token
    auth_manager.token_blacklist.add(token)
    result = await auth_manager.verify_token(token)
    assert result is None
    
    # Test token with invalid signature
    invalid_token = jwt.encode(
        payload,
        'wrong_secret',
        algorithm='HS256'
    )
    result = await auth_manager.verify_token(invalid_token)
    assert result is None
    
    # Test empty token
    result = await auth_manager.verify_token("")
    assert result is None
    result = await auth_manager.verify_token(None)
    assert result is None

@pytest.mark.asyncio
async def test_revoke_token(auth_manager):
    """Test token revocation"""
    # Create a token
    token = await auth_manager.create_token("test_user", ["admin"])
    assert token is not None
    
    # Verify token works
    assert await auth_manager.verify_token(token) is not None
    
    # Revoke token
    assert await auth_manager.revoke_token(token) is True
    
    # Verify token no longer works
    assert await auth_manager.verify_token(token) is None
    
    # Test revoking invalid token
    assert await auth_manager.revoke_token("invalid_token") is False
    
    # Test revoking empty token
    assert await auth_manager.revoke_token("") is False
    assert await auth_manager.revoke_token(None) is False

@pytest.mark.asyncio
async def test_verify_permissions(auth_manager, test_db):
    """Test permission verification"""
    with patch('security.auth_manager.db', test_db):
        # Configure mock
        test_db.table = MagicMock(return_value=test_db)
        test_db.select = MagicMock(return_value=test_db)
        test_db.eq = MagicMock(return_value=test_db)
        test_db.execute = AsyncMock(return_value=MagicMock(data=[{'roles': ['admin', 'developer']}]))
        
        # Test valid permission
        assert await auth_manager.verify_permissions("test_user", ["admin"]) is True
        assert await auth_manager.verify_permissions("test_user", ["developer"]) is True
        
        # Test invalid permission
        assert await auth_manager.verify_permissions("test_user", ["moderator"]) is False
        
        # Test non-existent user
        test_db.execute.return_value.data = []
        assert await auth_manager.verify_permissions("unknown_user", ["admin"]) is False
        
        # Test database error
        test_db.execute.side_effect = Exception("Database error")
        assert await auth_manager.verify_permissions("test_user", ["admin"]) is False
        
        # Test invalid inputs
        assert await auth_manager.verify_permissions(None, ["admin"]) is False
        assert await auth_manager.verify_permissions("test_user", None) is False
        assert await auth_manager.verify_permissions("", []) is False

@pytest.mark.asyncio
async def test_rate_limiting(auth_manager):
    """Test rate limiting functionality"""
    user_id = "test_user"
    
    # Should allow initial requests
    for _ in range(settings.RATE_LIMIT_CALLS):
        assert await auth_manager.check_rate_limit(user_id) is True
    
    # Should block after limit
    assert await auth_manager.check_rate_limit(user_id) is False
    
    # Test rate limit cleanup
    auth_manager.rate_limits[user_id] = [
        datetime.utcnow() - timedelta(minutes=2)
    ]
    assert await auth_manager.check_rate_limit(user_id) is True
    
    # Test invalid inputs
    assert await auth_manager.check_rate_limit(None) is False
    assert await auth_manager.check_rate_limit("") is False

def test_encryption(auth_manager):
    """Test data encryption/decryption"""
    test_data = [
        "sensitive_data",
        "special!@#$%^&*()chars",
        "unicode_data_🚀",
        "1234567890",
        """multi
        line
        data"""
    ]
    
    for original_data in test_data:
        # Encrypt data
        encrypted = auth_manager.encrypt_data(original_data)
        assert encrypted != original_data
        
        # Decrypt data
        decrypted = auth_manager.decrypt_data(encrypted)
        assert decrypted == original_data
    
    # Test encryption error
    with patch.object(auth_manager.fernet, 'encrypt', side_effect=Exception("Encryption error")):
        with pytest.raises(Exception):
            auth_manager.encrypt_data("test")
    
    # Test decryption error
    with patch.object(auth_manager.fernet, 'decrypt', side_effect=Exception("Decryption error")):
        with pytest.raises(Exception):
            auth_manager.decrypt_data(encrypted)
    
    # Test invalid inputs
    with pytest.raises(ValueError):
        auth_manager.encrypt_data(None)
    with pytest.raises(ValueError):
        auth_manager.encrypt_data("")
    with pytest.raises(ValueError):
        auth_manager.decrypt_data(None)
    with pytest.raises(ValueError):
        auth_manager.decrypt_data(b"")

def test_signature_verification(auth_manager):
    """Test webhook signature verification"""
    secret = "test_secret"
    test_payloads = [
        b"test_payload",
        b"special!@#$%^&*()chars",
        b"1234567890",
        b"unicode_data_\xf0\x9f\x9a\x80"
    ]
    
    for payload in test_payloads:
        # Create signature
        import hmac
        import hashlib
        expected_signature = hmac.new(
            secret.encode(),
            payload,
            hashlib.sha256
        ).hexdigest()
        
        # Test correct signature
        assert auth_manager.verify_signature(payload, expected_signature, secret) is True
        
        # Test incorrect signature
        assert auth_manager.verify_signature(payload, "wrong_signature", secret) is False
        assert auth_manager.verify_signature(payload, expected_signature, "wrong_secret") is False
    
    # Test verification error
    with patch('hmac.compare_digest', side_effect=Exception("Verification error")):
        assert auth_manager.verify_signature(b"test", "test", "test") is False
    
    # Test invalid inputs
    assert auth_manager.verify_signature(None, "test", "test") is False
    assert auth_manager.verify_signature(b"test", None, "test") is False
    assert auth_manager.verify_signature(b"test", "test", None) is False
    assert auth_manager.verify_signature(b"", "", "") is False

@pytest.mark.asyncio
async def test_auth_logging(auth_manager, test_db):
    """Test authentication event logging"""
    with patch('security.auth_manager.db', test_db):
        # Configure mock
        test_db.table = MagicMock(return_value=test_db)
        test_db.insert = MagicMock(return_value=test_db)
        test_db.execute = AsyncMock()
        
        # Test successful logging
        await auth_manager.log_auth_event(
            user_id="test_user",
            event_type="login",
            details="Test login event"
        )
        
        test_db.table.assert_called_with('auth_logs')
        test_db.insert.assert_called_once()
        test_db.execute.assert_called_once()
        
        # Test logging error
        test_db.execute.side_effect = Exception("Logging error")
        await auth_manager.log_auth_event(
            user_id="test_user",
            event_type="error",
            details="Test error event"
        )
        
        # Test invalid inputs
        await auth_manager.log_auth_event(None, "login", "test")
        await auth_manager.log_auth_event("test_user", None, "test")
        await auth_manager.log_auth_event("test_user", "login", None)
        await auth_manager.log_auth_event("", "", "")

@pytest.mark.asyncio
async def test_get_auth_logs(auth_manager, test_db):
    """Test retrieving authentication logs"""
    with patch('security.auth_manager.db', test_db):
        # Configure mock
        test_db.table = MagicMock(return_value=test_db)
        test_db.select = MagicMock(return_value=test_db)
        test_db.eq = MagicMock(return_value=test_db)
        test_db.gte = MagicMock(return_value=test_db)
        test_db.lte = MagicMock(return_value=test_db)
        test_db.execute = AsyncMock(return_value=MagicMock(data=[{
            'user_id': 'test_user',
            'event_type': 'login',
            'details': 'Test login event',
            'timestamp': datetime.utcnow().isoformat()
        }]))
        
        # Test without filters
        logs = await auth_manager.get_auth_logs()
        assert len(logs) == 1
        assert logs[0]['user_id'] == 'test_user'
        
        # Test with user filter
        logs = await auth_manager.get_auth_logs(user_id='test_user')
        assert len(logs) == 1
        
        # Test with time range
        start_time = datetime.utcnow() - timedelta(days=1)
        end_time = datetime.utcnow()
        logs = await auth_manager.get_auth_logs(
            start_time=start_time,
            end_time=end_time
        )
        assert len(logs) == 1
        
        # Test with all filters
        logs = await auth_manager.get_auth_logs(
            user_id='test_user',
            start_time=start_time,
            end_time=end_time
        )
        assert len(logs) == 1
        
        # Test database error
        test_db.execute.side_effect = Exception("Database error")
        logs = await auth_manager.get_auth_logs()
        assert len(logs) == 0
        
        # Test invalid inputs
        logs = await auth_manager.get_auth_logs(user_id=None)
        assert len(logs) == 0
        logs = await auth_manager.get_auth_logs(start_time="invalid")
        assert len(logs) == 0
        logs = await auth_manager.get_auth_logs(end_time="invalid")
        assert len(logs) == 0