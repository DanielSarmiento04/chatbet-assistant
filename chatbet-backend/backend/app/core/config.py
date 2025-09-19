"""
Configuration management for the ChatBet application.

Hey there! This is our central configuration hub. I'm using Pydantic Settings
here because it gives us type safety, validation, and automatic environment
variable loading out of the box. Much cleaner than manually parsing env vars!

The neat thing about this approach is that we can have different settings
for different environments (dev, staging, prod) and they'll all be validated
the same way. Plus, the IDE gets full autocomplete on our settings.
"""

import secrets
from typing import Literal, Optional, List, Union
from functools import lru_cache

from pydantic import Field, field_validator, AnyHttpUrl
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings with environment variable support.
    
    This class automatically loads configuration from environment variables,
    .env files, and provides sensible defaults for development.
    """
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # === Application Settings ===
    app_name: str = "ChatBet Assistant"
    app_version: str = "1.0.0"
    debug: bool = Field(default=False, description="Enable debug mode")
    environment: Literal["development", "staging", "production"] = "development"
    
    # === API Configuration ===
    api_v1_prefix: str = "/api/v1"
    allowed_hosts: Union[List[str], str] = Field(default=["*"], description="Allowed hosts")
    cors_origins: Union[List[str], str] = Field(default=[], description="CORS origins")
    
    # === ChatBet API Integration ===
    chatbet_api_base_url: str = Field(
        default="https://v46fnhvrjvtlrsmnismnwhdh5y0lckdl.lambda-url.us-east-1.on.aws",
        description="Base URL for the ChatBet sports betting API"
    )
    chatbet_api_timeout: int = Field(default=30, description="API request timeout in seconds")
    chatbet_api_max_retries: int = Field(default=3, description="Maximum retry attempts for API calls")
    
    # === Google AI Configuration ===
    google_api_key: Optional[str] = Field(default=None, description="Google AI API key for Gemini")
    gemini_model: str = Field(default="gemini-2.5-flash", description="Gemini model to use")
    gemini_temperature: float = Field(default=0.7, ge=0.0, le=2.0, description="LLM temperature")
    gemini_max_tokens: Optional[int] = Field(default=None, description="Maximum tokens for responses")
    gemini_timeout: int = Field(default=60, description="LLM request timeout in seconds")
    
    # === Redis Configuration ===
    redis_host: str = Field(default="localhost", description="Redis server host")
    redis_port: int = Field(default=6379, description="Redis server port")
    redis_db: int = Field(default=0, description="Redis database number")
    redis_password: Optional[str] = Field(default=None, description="Redis password")
    redis_url: Optional[str] = Field(default=None, description="Complete Redis URL (overrides individual settings)")
    
    # === Caching TTL Settings (in seconds) ===
    cache_ttl_tournaments: int = Field(default=86400, description="Tournament data cache TTL (24 hours)")
    cache_ttl_fixtures: int = Field(default=14400, description="Match fixtures cache TTL (4 hours)")
    cache_ttl_odds: int = Field(default=30, description="Live odds cache TTL (30 seconds)")
    cache_ttl_user_sessions: int = Field(default=3600, description="User session cache TTL (1 hour)")
    
    # === Security Settings ===
    secret_key: str = Field(
        default_factory=lambda: secrets.token_urlsafe(32),
        description="Secret key for session management"
    )
    access_token_expire_minutes: int = Field(default=60, description="Access token expiration time")
    
    # === Logging Configuration ===
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    enable_json_logs: bool = Field(default=False, description="Enable structured JSON logging")
    
    # === Rate Limiting ===
    rate_limit_requests: int = Field(default=100, description="Requests per minute per IP")
    rate_limit_window: int = Field(default=60, description="Rate limit window in seconds")
    
    # === Conversation Settings ===
    max_conversation_history: int = Field(default=10, description="Maximum messages in conversation memory")
    conversation_timeout: int = Field(default=1800, description="Conversation timeout in seconds (30 min)")
    
    @field_validator("gemini_max_tokens", mode="before")
    @classmethod
    def parse_optional_int(cls, v):
        """Convert empty string to None for optional integer fields."""
        if isinstance(v, str) and v.strip() == "":
            return None
        return v
    
    @field_validator("allowed_hosts", mode="before")
    @classmethod
    def assemble_allowed_hosts(cls, v):
        """Convert allowed hosts string to list if needed."""
        if isinstance(v, str) and v:
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, str) and not v:
            return ["*"]  # Default to allow all if empty string
        return v
    
    @field_validator("cors_origins", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v):
        """Convert CORS origins string to list if needed."""
        if isinstance(v, str) and v:
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, str) and not v:
            return []  # Default to empty list if empty string
        return v
    
    @field_validator("google_api_key")
    @classmethod
    def validate_google_api_key(cls, v, info):
        """Ensure Google API key is provided in production."""
        if hasattr(info, 'data') and info.data:
            environment = info.data.get("environment", "development")
            if environment == "production" and not v:
                raise ValueError("Google API key is required in production environment")
        return v
    
    @property
    def redis_dsn(self) -> str:
        """Build Redis connection string."""
        if self.redis_url:
            return self.redis_url
        
        auth = f":{self.redis_password}@" if self.redis_password else ""
        return f"redis://{auth}{self.redis_host}:{self.redis_port}/{self.redis_db}"
    
    @property
    def is_development(self) -> bool:
        """Check if running in development mode."""
        return self.environment == "development"
    
    @property
    def is_production(self) -> bool:
        """Check if running in production mode."""
        return self.environment == "production"


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached application settings.
    
    Using lru_cache here means we only create the settings object once
    and reuse it throughout the application lifecycle. This is both
    more efficient and ensures consistency.
    """
    return Settings()


# Global settings instance for easy importing
settings = get_settings()