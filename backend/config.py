from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass
class Settings:
    environment: str = os.getenv("ENVIRONMENT", "development")
    debug: bool = os.getenv("DEBUG", "false").lower() == "true"
    backend_port: int = int(os.getenv("BACKEND_PORT", "8000"))
    frontend_url: str = os.getenv("FRONTEND_URL", "http://localhost:3000")
    secret_key: str | None = os.getenv("SECRET_KEY")
    claude_api_key: str | None = os.getenv("CLAUDE_API_KEY")
    supabase_url: str | None = os.getenv("SUPABASE_URL")
    supabase_key: str | None = os.getenv("SUPABASE_KEY")

    @property
    def cors_origins(self) -> list[str]:
        raw_origins = os.getenv("CORS_ORIGINS")
        if raw_origins:
            return [origin.strip() for origin in raw_origins.split(",") if origin.strip()]
        return [self.frontend_url]

    @property
    def has_supabase(self) -> bool:
        return bool(self.supabase_url and self.supabase_key)

    @property
    def has_anthropic(self) -> bool:
        return bool(self.claude_api_key)

    @property
    def auth_enabled(self) -> bool:
        return bool(self.secret_key)


settings = Settings()
