from typing import Any

from mcp_server.config import MCPSettings
from mcp_server.utils.helpers import dry_run_response
from mcp_server.utils.validators import CampaignBudget


def register(mcp: Any, settings: MCPSettings) -> None:
    @mcp.tool()
    async def launch_google_ads_campaign(
        campaign_name: str,
        landing_page_url: str,
        keywords: list[str],
        daily_budget: float,
        currency: str = "USD",
        geo_targets: list[str] | None = None,
    ) -> dict[str, Any]:
        """Create a search campaign from Claude-approved growth strategy."""
        budget = CampaignBudget(daily_budget=daily_budget, currency=currency)
        payload = {
            "campaign_name": campaign_name,
            "landing_page_url": landing_page_url,
            "keywords": keywords,
            "budget": budget.model_dump(),
            "geo_targets": geo_targets or ["US"],
        }
        if settings.dry_run:
            return dry_run_response("google_ads.launch_campaign", payload)
        raise NotImplementedError("Use the official Google Ads client library with OAuth and manager account scoping.")

    @mcp.tool()
    async def get_google_ads_performance(campaign_id: str | None = None, days: int = 14) -> dict[str, Any]:
        """Pull campaign metrics for budget, keyword, and creative optimization."""
        if settings.dry_run:
            return {
                "status": "dry_run",
                "campaign_id": campaign_id,
                "days": days,
                "cpc": 4.2,
                "conversions": 18,
                "cost_per_lead": 42.0,
                "waste_flags": ["Pause broad match keywords with zero conversion value."],
            }
        raise NotImplementedError("Wire Google Ads GAQL reporting queries here.")
