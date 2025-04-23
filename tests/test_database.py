import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from datetime import datetime
from database.supabase_client import SupabaseManager, get_test_db

@pytest.fixture
def db_manager():
    """Create database manager instance for testing"""
    return SupabaseManager(is_test=True)

@pytest.mark.asyncio
async def test_create_user(db_manager):
    """Test user creation"""
    # Mock successful user creation
    db_manager.client = MagicMock()
    db_manager.client.table = MagicMock(return_value=db_manager.client)
    db_manager.client.insert = MagicMock(return_value=db_manager.client)
    db_manager.client.execute = AsyncMock(return_value=MagicMock(
        data=[{'id': 1, 'discord_id': 'test_id', 'username': 'test_user'}]
    ))

    result = await db_manager.create_user('test_id', 'test_user')
    assert result is not None
    assert result['discord_id'] == 'test_id'
    assert result['username'] == 'test_user'

    # Test creation with no client
    db_manager.client = None
    result = await db_manager.create_user('test_id', 'test_user')
    assert result is None

    # Test creation with database error
    db_manager.client = MagicMock()
    db_manager.client.table = MagicMock(side_effect=Exception("Database error"))
    result = await db_manager.create_user('test_id', 'test_user')
    assert result is None

@pytest.mark.asyncio
async def test_get_user(db_manager):
    """Test user retrieval"""
    # Mock successful user retrieval
    db_manager.client = MagicMock()
    db_manager.client.table = MagicMock(return_value=db_manager.client)
    db_manager.client.select = MagicMock(return_value=db_manager.client)
    db_manager.client.eq = MagicMock(return_value=db_manager.client)
    db_manager.client.execute = AsyncMock(return_value=MagicMock(
        data=[{'id': 1, 'discord_id': 'test_id', 'username': 'test_user'}]
    ))

    result = await db_manager.get_user('test_id')
    assert result is not None
    assert result['discord_id'] == 'test_id'
    assert result['username'] == 'test_user'

    # Test retrieval with no client
    db_manager.client = None
    result = await db_manager.get_user('test_id')
    assert result is None

    # Test retrieval with database error
    db_manager.client = MagicMock()
    db_manager.client.table = MagicMock(side_effect=Exception("Database error"))
    result = await db_manager.get_user('test_id')
    assert result is None

@pytest.mark.asyncio
async def test_log_activity(db_manager):
    """Test activity logging"""
    # Mock successful activity logging
    db_manager.client = MagicMock()
    db_manager.client.table = MagicMock(return_value=db_manager.client)
    db_manager.client.insert = MagicMock(return_value=db_manager.client)
    db_manager.client.execute = AsyncMock(return_value=MagicMock(
        data=[{
            'id': 1,
            'user_id': 'test_user',
            'activity_type': 'test_activity',
            'details': 'test details'
        }]
    ))

    result = await db_manager.log_activity(
        'test_user',
        'test_activity',
        'test details'
    )
    assert result is not None
    assert result['user_id'] == 'test_user'
    assert result['activity_type'] == 'test_activity'
    assert result['details'] == 'test details'

    # Test logging with no client
    db_manager.client = None
    result = await db_manager.log_activity(
        'test_user',
        'test_activity',
        'test details'
    )
    assert result is None

    # Test logging with database error
    db_manager.client = MagicMock()
    db_manager.client.table = MagicMock(side_effect=Exception("Database error"))
    result = await db_manager.log_activity(
        'test_user',
        'test_activity',
        'test details'
    )
    assert result is None

@pytest.mark.asyncio
async def test_create_team(db_manager):
    """Test team creation"""
    # Mock successful team creation
    db_manager.client = MagicMock()
    db_manager.client.table = MagicMock(return_value=db_manager.client)
    db_manager.client.insert = MagicMock(return_value=db_manager.client)
    db_manager.client.execute = AsyncMock(return_value=MagicMock(
        data=[{
            'id': 1,
            'name': 'test_team',
            'owner_id': 'test_owner'
        }]
    ))

    result = await db_manager.create_team('test_team', 'test_owner')
    assert result is not None
    assert result['name'] == 'test_team'
    assert result['owner_id'] == 'test_owner'

    # Test creation with no client
    db_manager.client = None
    result = await db_manager.create_team('test_team', 'test_owner')
    assert result is None

    # Test creation with database error
    db_manager.client = MagicMock()
    db_manager.client.table = MagicMock(side_effect=Exception("Database error"))
    result = await db_manager.create_team('test_team', 'test_owner')
    assert result is None

def test_test_db():
    """Test test database creation"""
    db = get_test_db()
    assert db.client is None

def test_supabase_initialization():
    """Test Supabase client initialization"""
    # Test initialization with missing credentials
    with patch('database.supabase_client.settings') as mock_settings:
        mock_settings.SUPABASE_URL = ''
        mock_settings.SUPABASE_KEY = ''
        db = SupabaseManager()
        assert db.client is None

    # Test initialization with invalid credentials
    with patch('database.supabase_client.create_client', side_effect=Exception("Invalid credentials")):
        db = SupabaseManager()
        assert db.client is None

    # Test initialization in test mode
    db = SupabaseManager(is_test=True)
    assert db.client is None