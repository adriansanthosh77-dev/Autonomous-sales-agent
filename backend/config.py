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
    email_delivery_mode: str = os.getenv("EMAIL_DELIVERY_MODE", "dry_run")
    smtp_host: str | None = os.getenv("SMTP_HOST")
    smtp_port: int = int(os.getenv("SMTP_PORT", "587"))
    smtp_username: str | None = os.getenv("SMTP_USERNAME")
    smtp_password: str | None = os.getenv("SMTP_PASSWORD")
    smtp_from_email: str | None = os.getenv("SMTP_FROM_EMAIL")
    smtp_from_name: str = os.getenv("SMTP_FROM_NAME", "Autonomous Sales")
    smtp_use_tls: bool = os.getenv("SMTP_USE_TLS", "true").lower() == "true"
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

    @property
    def smtp_ready(self) -> bool:
        return bool(
            self.smtp_host
            and self.smtp_username
            and self.smtp_password
            and self.smtp_from_email
        )


settings = Settings()
