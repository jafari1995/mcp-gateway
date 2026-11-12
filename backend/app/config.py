from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "MCP Gateway"
    admin_username: str = "admin"
    admin_api_key: str = "dev-admin-key"
    database_url: str = "sqlite:///./data/gateway_v2.db"
    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"
    token_prefix: str = "mcpgw_"
    demo_mcp_url: str = "http://localhost:8100/mcp"


@lru_cache
def get_settings() -> Settings:
    return Settings()
