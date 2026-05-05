from typing import Any

from mcp_server.config import MCPSettings


def register(mcp: Any, settings: MCPSettings) -> None:
    @mcp.tool()
    async def pull_ga4_conversion_report(days: int = 30, conversion_event: str = "generate_lead") -> dict[str, Any]:
        """Analyze GA4 conversion performance by source, landing page, and funnel event."""
        if settings.dry_run:
            return {
                "status": "dry_run",
                "property_id": settings.ga4_property_id,
                "days": days,
                "conversion_event": conversion_event,
                "top_sources": [
                    {"source": "google / cpc", "conversions": 18, "conversion_rate": 0.041},
                    {"source": "linkedin / referral", "conversions": 9, "conversion_rate": 0.063},
                ],
            }
        raise NotImplementedError("Wire GA4 Data API runReport calls with service account credentials.")

    @mcp.tool()
    async def get_top_converting_pages(days: int = 30, limit: int = 10) -> dict[str, Any]:
        """Find landing pages with the strongest lead or revenue conversion rate."""
        if settings.dry_run:
            return {
                "status": "dry_run",
                "days": days,
                "pages": [
                    {"path": "/ai-sales-agent", "conversion_rate": 0.072, "leads": 31},
                    {"path": "/pricing", "conversion_rate": 0.055, "leads": 24},
                ][:limit],
            }
        raise NotImplementedError("Wire GA4 landing page report here.")
