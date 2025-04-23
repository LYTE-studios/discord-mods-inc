import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock
import os
import sys
from typing import AsyncGenerator
from cryptography.fernet import Fernet

# Add project root to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from database.supabase_client import get_test_db

@pytest.fixture
def mock_bot():
    """Mock Discord bot"""
    bot = MagicMock()
    bot.loop = asyncio.get_event_loop()
    bot.user = MagicMock()
    bot.user.name = "TestBot"
    bot.user.id = 123456789
    return bot

@pytest.fixture
async def test_db():
    """Get test database instance"""
    db = get_test_db()
    
    # Create a proper mock chain
    mock_chain = MagicMock()
    mock_chain.table = MagicMock(return_value=mock_chain)
    mock_chain.select = MagicMock(return_value=mock_chain)
    mock_chain.insert = MagicMock(return_value=mock_chain)
    mock_chain.update = MagicMock(return_value=mock_chain)
    mock_chain.delete = MagicMock(return_value=mock_chain)
    mock_chain.eq = MagicMock(return_value=mock_chain)
    mock_chain.execute = AsyncMock(return_value=MagicMock(data=[]))
    
    # Add the mock chain to the test database
    db.table = mock_chain.table
    db.select = mock_chain.select
    db.insert = mock_chain.insert
    db.update = mock_chain.update
    db.delete = mock_chain.delete
    db.eq = mock_chain.eq
    db.execute = mock_chain.execute
    
    return db

@pytest.fixture
def mock_ctx():
    """Mock Discord context"""
    ctx = MagicMock()
    ctx.author = MagicMock()
    ctx.author.id = 123456789
    ctx.author.name = "TestUser"
    ctx.guild = MagicMock()
    ctx.guild.id = 987654321
    ctx.channel = MagicMock()
    ctx.channel.id = 456789123
    ctx.send = AsyncMock()
    return ctx

@pytest.fixture(autouse=True)
def mock_env_vars(monkeypatch):
    """Mock environment variables"""
    # Generate a valid Fernet key for testing
    test_key = Fernet.generate_key()
    
    env_vars = {
        'DISCORD_TOKEN': 'test_token',
        'DISCORD_GUILD_ID': '123456789',
        'SUPABASE_URL': 'https://test.supabase.co',
        'SUPABASE_KEY': 'test_key',
        'OPENAI_API_KEY': 'test_openai_key',
        'GITHUB_TOKEN': 'test_github_token',
        'ENCRYPTION_KEY': test_key.decode(),  # Use the generated Fernet key
        'LOG_LEVEL': 'DEBUG'
    }
    for key, value in env_vars.items():
        monkeypatch.setenv(key, value)

@pytest.fixture
def mock_openai():
    """Mock OpenAI client"""
    openai = MagicMock()
    openai.ChatCompletion.acreate = AsyncMock(return_value=MagicMock(
        choices=[MagicMock(message=MagicMock(content="Test response"))],
        usage=MagicMock(
            prompt_tokens=10,
            completion_tokens=20,
            total_tokens=30
        )
    ))
    return openai

@pytest.fixture
def mock_github():
    """Mock GitHub client"""
    github = MagicMock()
    github.get_repo = MagicMock(return_value=MagicMock())
    github.create_repo = AsyncMock()
    github.get_user = MagicMock(return_value=MagicMock())
    return github

@pytest.fixture
def mock_psutil():
    """Mock psutil for monitoring"""
    psutil = MagicMock()
    psutil.cpu_percent.return_value = 50.0
    psutil.virtual_memory.return_value = MagicMock(
        percent=60.0,
        available=1000000000
    )
    psutil.disk_usage.return_value = MagicMock(
        percent=70.0
    )
    return psutil

# Event loop is provided by pytest-asyncio

@pytest.fixture
async def mock_discord_message():
    """Mock Discord message"""
    message = MagicMock()
    message.content = "Test message"
    message.author = MagicMock()
    message.author.id = 123456789
    message.author.name = "TestUser"
    message.channel = MagicMock()
    message.channel.id = 456789123
    message.guild = MagicMock()
    message.guild.id = 987654321
    return message

@pytest.fixture
def mock_discord_role():
    """Mock Discord role"""
    role = MagicMock()
    role.id = 123456789
    role.name = "TestRole"
    role.permissions = MagicMock()
    return role

@pytest.fixture
def mock_discord_channel():
    """Mock Discord channel"""
    channel = MagicMock()
    channel.id = 123456789
    channel.name = "test-channel"
    channel.send = AsyncMock()
    return channel

# Cleanup function
@pytest.fixture(autouse=True)
async def cleanup():
    yield
    # Add any cleanup code here if needed