from pydantic_settings import BaseSettings
from typing import Optional, Dict
from dotenv import load_dotenv
import os

load_dotenv()

class Settings(BaseSettings):
    # Discord Configuration
    DISCORD_TOKEN: str = os.getenv("DISCORD_TOKEN", "")
    DISCORD_GUILD_ID: int = int(os.getenv("DISCORD_GUILD_ID", "0"))
    
    # Database Configuration
    POSTGRES_HOST: str = os.getenv("POSTGRES_HOST", "")
    POSTGRES_PORT: int = int(os.getenv("POSTGRES_PORT", "5432"))
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "discord_mods")
    POSTGRES_USER: str = os.getenv("POSTGRES_USER", "postgres")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "")
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
    SUPABASE_KEY: str = os.getenv("SUPABASE_KEY", "")
    
    # OpenAI Configuration
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4")
    OPENAI_MAX_TOKENS: int = int(os.getenv("OPENAI_MAX_TOKENS", "1000"))
    OPENAI_TEMPERATURE: float = float(os.getenv("OPENAI_TEMPERATURE", "0.7"))
    
    # GitHub Configuration
    GITHUB_TOKEN: str = os.getenv("GITHUB_TOKEN", "")
    GITHUB_ORG: str = os.getenv("GITHUB_ORG", "")
    GITHUB_WEBHOOK_SECRET: str = os.getenv("GITHUB_WEBHOOK_SECRET", "")
    GITHUB_NOTIFICATIONS_CHANNEL: str = os.getenv("GITHUB_NOTIFICATIONS_CHANNEL", "")
    
    # Webhook Server Configuration
    WEBHOOK_HOST: str = os.getenv("WEBHOOK_HOST", "0.0.0.0")
    WEBHOOK_PORT: int = int(os.getenv("WEBHOOK_PORT", "5000"))
    
    # Security Configuration
    ENCRYPTION_KEY: str = os.getenv("ENCRYPTION_KEY", "")
    RATE_LIMIT_CALLS: int = int(os.getenv("RATE_LIMIT_CALLS", "100"))
    RATE_LIMIT_PERIOD: int = int(os.getenv("RATE_LIMIT_PERIOD", "60"))
    
    # Monitoring Configuration
    MONITORING_INTERVAL: int = int(os.getenv("MONITORING_INTERVAL", "60"))
    MONITORING_NOTIFICATIONS_CHANNEL: str = os.getenv("MONITORING_NOTIFICATIONS_CHANNEL", "")
    METRICS_RETENTION_DAYS: int = int(os.getenv("METRICS_RETENTION_DAYS", "30"))

    @property
    def ALERT_THRESHOLDS(self) -> Dict[str, float]:
        """Get alert thresholds with environment variable overrides"""
        return {
            'cpu_usage': float(os.getenv("ALERT_THRESHOLD_CPU", "80.0")),
            'memory_usage': float(os.getenv("ALERT_THRESHOLD_MEMORY", "80.0")),
            'api_latency': float(os.getenv("ALERT_THRESHOLD_API_LATENCY", "2000.0")),
            'error_rate': float(os.getenv("ALERT_THRESHOLD_ERROR_RATE", "5.0")),
            'disk_usage': float(os.getenv("ALERT_THRESHOLD_DISK", "90.0"))
        }
    
    # Logging Configuration
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE: str = os.getenv("LOG_FILE", "bot.log")
    
    # Role Configuration
    DEFAULT_ROLES: list = [
        "AI CTO",
        "AI UX Designer",
        "AI UI Designer",
        "AI Developer",
        "AI Tester"
    ]
    
    # Channel Configuration
    DEFAULT_CHANNELS: list = [
        "general",
        "projects",
        "tasks",
        "development",
        "testing",
        "logs"
    ]

    model_config = {
        "case_sensitive": True,
        "env_file": ".env",
        "env_file_encoding": "utf-8"
    }

settings = Settings()