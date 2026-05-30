"""
ghostrace.backend.config
~~~~~~~~~~~~~~~~~~~~~~~~
All configuration read from environment variables via pydantic-settings.
Never hardcode secrets — everything comes from the environment.
"""
from __future__ import annotations
from functools import lru_cache
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8', case_sensitive=False, extra='ignore')
    database_url: str = 'sqlite+aiosqlite:///./ghostrace_dev.db'
    secret_key: str = 'CHANGE-ME-IN-PRODUCTION-use-secrets-token-hex-32'
    algorithm: str = 'HS256'
    access_token_expire_minutes: int = 60 * 24
    refresh_token_expire_days: int = 30
    stripe_secret_key: str = ''
    stripe_webhook_secret: str = ''
    stripe_pro_price_id: str = ''
    stripe_team_price_id: str = ''
    allowed_origins: List[str] = ['http://localhost:3000', 'https://app.ghostrace.dev']
    environment: str = 'development'
    debug: bool = False
    plan_limits: dict = {'free': {'traces': 50000, 'retention_days': 7, 'projects': 1, 'api_keys': 1}, 'pro': {'traces': 500000, 'retention_days': 90, 'projects': 5, 'api_keys': 5}, 'team': {'traces': -1, 'retention_days': 365, 'projects': -1, 'api_keys': -1}, 'enterprise': {'traces': -1, 'retention_days': 365, 'projects': -1, 'api_keys': -1}}

@lru_cache
def get_settings() -> Settings:
    pass