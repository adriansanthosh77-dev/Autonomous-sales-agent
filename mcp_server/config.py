from __future__ import annotations

import os
from dataclasses import dataclass, field
from functools import lru_cache

from dotenv import load_dotenv

load_dotenv()


def _bool(name: str, default: bool = False) -> bool:
    return os.getenv(name, str(default)).strip().lower() in {"1", "true", "yes", "on"}


def _csv(name: str) -> list[str]:
    return [item.strip() for item in os.getenv(name, "").split(",") if item.strip()]


@dataclass(frozen=True)
class MCPSettings:
    service_name: str = os.getenv("MCP_SERVICE_NAME", "autonomous-sales-agent")
    environment: str = os.getenv("ENVIRONMENT", "development")
    debug: bool = _bool("DEBUG")
    dry_run: bool = _bool("MCP_DRY_RUN", True)
    request_timeout_seconds: float = float(os.getenv("MCP_REQUEST_TIMEOUT_SECONDS", "30"))
    max_retries: int = int(os.getenv("MCP_MAX_RETRIES", "3"))
    retry_backoff_seconds: float = float(os.getenv("MCP_RETRY_BACKOFF_SECONDS", "0.8"))
    allowed_webhook_sources: list[str] = field(default_factory=lambda: _csv("MCP_ALLOWED_WEBHOOK_SOURCES"))

    backend_api_url: str = os.getenv("BACKEND_API_URL", "http://localhost:8000")
    backend_api_key: str | None = os.getenv("SECRET_KEY")

    gmail_credentials_json: str | None = os.getenv("GMAIL_CREDENTIALS_JSON")
    gmail_delegated_user: str | None = os.getenv("GMAIL_DELEGATED_USER")
    google_sheets_credentials_json: str | None = os.getenv("GOOGLE_SHEETS_CREDENTIALS_JSON")
    google_sheets_default_spreadsheet_id: str | None = os.getenv("GOOGLE_SHEETS_DEFAULT_SPREADSHEET_ID")

    whatsapp_api_url: str = os.getenv("WHATSAPP_API_URL", "https://graph.facebook.com/v19.0")
    whatsapp_phone_number_id: str | None = os.getenv("WHATSAPP_PHONE_NUMBER_ID")
    whatsapp_access_token: str | None = os.getenv("WHATSAPP_ACCESS_TOKEN")

    hunter_api_key: str | None = os.getenv("HUNTER_API_KEY")
    apollo_api_key: str | None = os.getenv("APOLLO_API_KEY")
    clearbit_api_key: str | None = os.getenv("CLEARBIT_API_KEY")

    google_ads_developer_token: str | None = os.getenv("GOOGLE_ADS_DEVELOPER_TOKEN")
    google_ads_customer_id: str | None = os.getenv("GOOGLE_ADS_CUSTOMER_ID")
    google_ads_login_customer_id: str | None = os.getenv("GOOGLE_ADS_LOGIN_CUSTOMER_ID")

    meta_ads_access_token: str | None = os.getenv("META_ADS_ACCESS_TOKEN")
    meta_ads_account_id: str | None = os.getenv("META_ADS_ACCOUNT_ID")

    ga4_property_id: str | None = os.getenv("GA4_PROPERTY_ID")
    gsc_site_url: str | None = os.getenv("GSC_SITE_URL")
    gtm_account_id: str | None = os.getenv("GTM_ACCOUNT_ID")
    gtm_container_id: str | None = os.getenv("GTM_CONTAINER_ID")
    gtm_workspace_id: str | None = os.getenv("GTM_WORKSPACE_ID")

    contentful_space_id: str | None = os.getenv("CONTENTFUL_SPACE_ID")
    contentful_environment: str = os.getenv("CONTENTFUL_ENVIRONMENT", "master")
    contentful_management_token: str | None = os.getenv("CONTENTFUL_MANAGEMENT_TOKEN")

    iterable_api_key: str | None = os.getenv("ITERABLE_API_KEY")
    iterable_base_url: str = os.getenv("ITERABLE_BASE_URL", "https://api.iterable.com/api")

    triggerdev_api_key: str | None = os.getenv("TRIGGERDEV_API_KEY")
    triggerdev_base_url: str = os.getenv("TRIGGERDEV_BASE_URL", "https://api.trigger.dev")
    triggerdev_project_ref: str | None = os.getenv("TRIGGERDEV_PROJECT_REF")

    redis_url: str | None = os.getenv("REDIS_URL")
    webhook_signing_secret: str | None = os.getenv("WEBHOOK_SIGNING_SECRET")

    @property
    def is_production(self) -> bool:
        return self.environment.lower() == "production"


@lru_cache
def get_settings() -> MCPSettings:
    return MCPSettings()

