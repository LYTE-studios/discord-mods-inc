import pytest
from unittest.mock import patch, MagicMock, AsyncMock
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
    mock_settings.RATE_LIMIT_CALLS = 100
    mock_settings.RATE_LIMIT_PERIOD = 60
    
    # Patch the settings module
    with patch('security.auth_manager.settings', mock_settings):
        return AuthManager()

@pytest.mark.asyncio
async def test_verify_permissions(auth_manager):
    """Test permission verification"""
    # Mock database response
    mock_db = MagicMock()
    mock_db.table = MagicMock(return_value=mock_db)
    mock_db.select = MagicMock(return_value=mock_db)
    mock_db.eq = MagicMock(return_value=mock_db)
    mock_db.execute = AsyncMock(return_value=MagicMock(data=[{'roles': ['admin', 'developer']}]))

    with patch('security.auth_manager.db', mock_db):
        # Test valid permission
        assert await auth_manager.verify_permissions("test_user", ["admin"]) is True
        assert await auth_manager.verify_permissions("test_user", ["developer"]) is True
        
        # Test invalid permission
        assert await auth_manager.verify_permissions("test_user", ["moderator"]) is False
        
        # Test non-existent user
        mock_db.execute.return_value.data = []
        assert await auth_manager.verify_permissions("unknown_user", ["admin"]) is False
        
        # Test database error
        mock_db.execute.side_effect = Exception("Database error")
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