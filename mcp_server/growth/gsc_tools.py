from typing import Any

from mcp_server.config import MCPSettings


def register(mcp: Any, settings: MCPSettings) -> None:
    @mcp.tool()
    async def get_gsc_keyword_opportunities(days: int = 28, min_impressions: int = 250) -> dict[str, Any]:
        """Find Search Console keywords with ranking upside and sales intent."""
        if settings.dry_run:
            return {
                "status": "dry_run",
                "site_url": settings.gsc_site_url,
                "days": days,
                "opportunities": [
                    {
                        "query": "ai sales agent",
                        "impressions": 4200,
                        "ctr": 0.018,
                        "avg_position": 8.7,
                        "recommended_action": "Refresh landing page H1 and add comparison FAQ.",
                    }
                ],
            }
        raise NotImplementedError("Wire Google Search Console searchanalytics.query calls here.")

    @mcp.tool()
    async def get_seo_opportunities(days: int = 28) -> dict[str, Any]:
        """Summarize SEO opportunities Claude can turn into page updates or content briefs."""
        return await get_gsc_keyword_opportunities(days=days)
