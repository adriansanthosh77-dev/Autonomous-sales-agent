from typing import Any

from mcp_server.config import MCPSettings
from mcp_server.utils.auth import bearer, require_configured
from mcp_server.utils.helpers import dry_run_response, request_json


def register(mcp: Any, settings: MCPSettings) -> None:
    @mcp.tool()
    async def update_contentful_page(
        entry_id: str,
        fields: dict[str, Any],
        publish: bool = False,
        locale: str = "en-US",
    ) -> dict[str, Any]:
        """Update a Contentful landing page with Claude-approved conversion or SEO changes."""
        payload = {"entry_id": entry_id, "fields": fields, "publish": publish, "locale": locale}
        if settings.dry_run:
            return dry_run_response("contentful.update_page", payload)

        require_configured(
            "Contentful",
            contentful_space_id=settings.contentful_space_id,
            contentful_management_token=settings.contentful_management_token,
        )
        url = (
            "https://api.contentful.com/spaces/"
            f"{settings.contentful_space_id}/environments/{settings.contentful_environment}/entries/{entry_id}"
        )
        return await request_json("PUT", url, settings=settings, headers=bearer(settings.contentful_management_token), json={"fields": fields})

    @mcp.tool()
    async def optimize_contentful_landing_page(
        entry_id: str,
        target_keyword: str,
        conversion_goal: str,
        publish: bool = False,
    ) -> dict[str, Any]:
        """Prepare a landing page optimization payload for SEO and conversion experiments."""
        fields = {
            "targetKeyword": {"en-US": target_keyword},
            "conversionGoal": {"en-US": conversion_goal},
            "lastOptimizationSource": {"en-US": "claude_mcp"},
        }
        return await update_contentful_page(entry_id=entry_id, fields=fields, publish=publish)
