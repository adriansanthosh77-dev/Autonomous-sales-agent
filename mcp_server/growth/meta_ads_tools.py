from typing import Any

from mcp_server.config import MCPSettings
from mcp_server.utils.auth import bearer, require_configured
from mcp_server.utils.helpers import dry_run_response, request_json


def register(mcp: Any, settings: MCPSettings) -> None:
    @mcp.tool()
    async def create_retargeting_campaign(
        campaign_name: str,
        audience_name: str,
        landing_page_url: str,
        daily_budget: float,
        objective: str = "OUTCOME_LEADS",
    ) -> dict[str, Any]:
        """Create a Meta retargeting campaign for high-intent site visitors or CRM audiences."""
        payload = {
            "name": campaign_name,
            "objective": objective,
            "audience_name": audience_name,
            "landing_page_url": landing_page_url,
            "daily_budget": daily_budget,
        }
        if settings.dry_run:
            return dry_run_response("meta_ads.create_retargeting_campaign", payload)

        require_configured(
            "Meta Ads",
            meta_ads_account_id=settings.meta_ads_account_id,
            meta_ads_access_token=settings.meta_ads_access_token,
        )
        url = f"https://graph.facebook.com/v19.0/act_{settings.meta_ads_account_id}/campaigns"
        return await request_json("POST", url, settings=settings, headers=bearer(settings.meta_ads_access_token), json=payload)
