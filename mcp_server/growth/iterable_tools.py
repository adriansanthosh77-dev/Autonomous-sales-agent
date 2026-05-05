from typing import Any

from mcp_server.config import MCPSettings
from mcp_server.utils.auth import api_key_header, require_configured
from mcp_server.utils.helpers import dry_run_response, request_json


def register(mcp: Any, settings: MCPSettings) -> None:
    @mcp.tool()
    async def create_iterable_email_journey(
        journey_name: str,
        audience_segment: str,
        trigger_event: str,
        steps: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Create or stage an Iterable lifecycle journey for lead nurture and activation."""
        payload = {
            "journey_name": journey_name,
            "audience_segment": audience_segment,
            "trigger_event": trigger_event,
            "steps": steps,
        }
        if settings.dry_run:
            return dry_run_response("iterable.create_journey", payload)

        require_configured("Iterable", iterable_api_key=settings.iterable_api_key)
        url = f"{settings.iterable_base_url.rstrip('/')}/workflows"
        return await request_json("POST", url, settings=settings, headers=api_key_header("Api-Key", settings.iterable_api_key), json=payload)

    @mcp.tool()
    async def create_iterable_journey(
        journey_name: str,
        audience_segment: str,
        trigger_event: str,
        steps: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Alias for lifecycle journey creation using the naming recruiters and product teams recognize."""
        return await create_iterable_email_journey(journey_name, audience_segment, trigger_event, steps)
