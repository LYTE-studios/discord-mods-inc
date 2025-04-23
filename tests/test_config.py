import pytest
from unittest.mock import patch
import os
from config import Settings

def test_settings_initialization(mock_env_vars):
    """Test settings initialization with environment variables"""
    settings = Settings()
    
    # Test Discord configuration
    assert settings.DISCORD_TOKEN == 'test_token'
    assert settings.DISCORD_GUILD_ID == 123456789
    
    # Test Supabase configuration
    assert settings.SUPABASE_URL == 'https://test.supabase.co'
    assert settings.SUPABASE_KEY == 'test_key'
    
    # Test OpenAI configuration
    assert settings.OPENAI_API_KEY == 'test_openai_key'
    assert settings.OPENAI_MODEL == 'gpt-4'
    assert settings.OPENAI_MAX_TOKENS == 1000
    assert settings.OPENAI_TEMPERATURE == 0.7

def test_settings_defaults():
    """Test default values for settings"""
    with patch.dict(os.environ, {}, clear=True):
        settings = Settings()
        
        # Test default values
        assert settings.OPENAI_MODEL == 'gpt-4'
        assert settings.OPENAI_MAX_TOKENS == 1000
        assert settings.OPENAI_TEMPERATURE == 0.7
        assert settings.LOG_LEVEL == 'INFO'
        assert settings.WEBHOOK_HOST == '0.0.0.0'
        assert settings.WEBHOOK_PORT == 5000

def test_alert_thresholds():
    """Test alert threshold configurations"""
    settings = Settings()
    
    # Test default thresholds
    assert 'cpu_usage' in settings.ALERT_THRESHOLDS
    assert 'memory_usage' in settings.ALERT_THRESHOLDS
    assert 'api_latency' in settings.ALERT_THRESHOLDS
    assert 'error_rate' in settings.ALERT_THRESHOLDS
    assert 'disk_usage' in settings.ALERT_THRESHOLDS
    
    # Test threshold values
    assert settings.ALERT_THRESHOLDS['cpu_usage'] == 80.0
    assert settings.ALERT_THRESHOLDS['memory_usage'] == 80.0
    assert settings.ALERT_THRESHOLDS['api_latency'] == 2000.0
    assert settings.ALERT_THRESHOLDS['error_rate'] == 5.0
    assert settings.ALERT_THRESHOLDS['disk_usage'] == 90.0

def test_role_configuration():
    """Test role configurations"""
    settings = Settings()
    
    # Test default roles
    assert "AI CTO" in settings.DEFAULT_ROLES
    assert "AI UX Designer" in settings.DEFAULT_ROLES
    assert "AI UI Designer" in settings.DEFAULT_ROLES
    assert "AI Developer" in settings.DEFAULT_ROLES
    assert "AI Tester" in settings.DEFAULT_ROLES
    assert len(settings.DEFAULT_ROLES) == 5

def test_channel_configuration():
    """Test channel configurations"""
    settings = Settings()
    
    # Test default channels
    assert "general" in settings.DEFAULT_CHANNELS
    assert "projects" in settings.DEFAULT_CHANNELS
    assert "tasks" in settings.DEFAULT_CHANNELS
    assert "development" in settings.DEFAULT_CHANNELS
    assert "testing" in settings.DEFAULT_CHANNELS
    assert "logs" in settings.DEFAULT_CHANNELS
    assert len(settings.DEFAULT_CHANNELS) == 6

def test_security_configuration():
    """Test security configurations"""
    settings = Settings()
    
    # Test security settings
    assert settings.JWT_SECRET_KEY == 'test_jwt_secret'
    assert settings.JWT_ALGORITHM == 'HS256'
    assert settings.JWT_EXPIRATION_HOURS == 24
    # Don't test the exact encryption key value as it's dynamically generated
    assert settings.ENCRYPTION_KEY is not None
    assert len(settings.ENCRYPTION_KEY) > 0
    assert settings.RATE_LIMIT_CALLS == 100
    assert settings.RATE_LIMIT_PERIOD == 60

def test_monitoring_configuration():
    """Test monitoring configurations"""
    settings = Settings()
    
    # Test monitoring settings
    assert settings.MONITORING_INTERVAL == 60
    assert settings.METRICS_RETENTION_DAYS == 30
    assert settings.LOG_LEVEL == 'DEBUG'  # From mock_env_vars

def test_webhook_configuration():
    """Test webhook configurations"""
    settings = Settings()
    
    # Test webhook settings
    assert settings.WEBHOOK_HOST == '0.0.0.0'
    assert settings.WEBHOOK_PORT == 5000

def test_custom_environment_variables():
    """Test setting custom environment variables"""
    with patch.dict(os.environ, {
        'DISCORD_TOKEN': 'custom_token',
        'OPENAI_MODEL': 'gpt-3.5-turbo',
        'LOG_LEVEL': 'WARNING',
        'ALERT_THRESHOLD_CPU': '90.0'
    }, clear=True):
        settings = Settings()
        assert settings.DISCORD_TOKEN == 'custom_token'
        assert settings.OPENAI_MODEL == 'gpt-3.5-turbo'
        assert settings.LOG_LEVEL == 'WARNING'
        assert float(os.getenv('ALERT_THRESHOLD_CPU')) == 90.0
        assert settings.ALERT_THRESHOLDS['cpu_usage'] == 90.0