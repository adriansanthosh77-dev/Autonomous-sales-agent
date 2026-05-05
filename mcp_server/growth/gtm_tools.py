from typing import Any

from mcp_server.config import MCPSettings
from mcp_server.utils.helpers import dry_run_response


def register(mcp: Any, settings: MCPSettings) -> None:
    @mcp.tool()
    async def validate_gtm_tracking_setup(required_events: list[str] | None = None) -> dict[str, Any]:
        """Validate Google Tag Manager tags, triggers, and conversion event coverage."""
        events = required_events or ["page_view", "generate_lead", "book_demo", "purchase"]
        if settings.dry_run:
            return {
                "status": "dry_run",
                "container_id": settings.gtm_container_id,
                "required_events": events,
                "missing_events": ["book_demo"] if "book_demo" in events else [],
                "risk": "Demo bookings may not be attributed to paid campaigns.",
            }
        raise NotImplementedError("Wire GTM API container/workspace/tag/trigger inspection here.")

    @mcp.tool()
    async def analyze_gtm_tracking(page_url: str, expected_events: list[str] | None = None) -> dict[str, Any]:
        """Analyze a page's GTM tracking plan before launching campaigns."""
        payload = {"page_url": page_url, "expected_events": expected_events or ["generate_lead"]}
        if settings.dry_run:
            return dry_run_response("gtm.analyze_tracking", payload)
        raise NotImplementedError("Use GTM API plus browser/event validation in production.")
