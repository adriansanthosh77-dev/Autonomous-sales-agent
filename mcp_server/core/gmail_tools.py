from typing import Any

from mcp_server.config import MCPSettings
from mcp_server.utils.helpers import dry_run_response
from mcp_server.utils.validators import EmailPayload


def register(mcp: Any, settings: MCPSettings) -> None:
    @mcp.tool()
    async def send_followup_email(
        to_email: str,
        subject: str,
        body: str,
        lead_id: int | None = None,
        campaign_id: str | None = None,
    ) -> dict[str, Any]:
        """Send a sales follow-up email through Gmail, with dry-run safety for local use."""
        payload = EmailPayload(
            to_email=to_email,
            subject=subject,
            body=body,
            lead_id=lead_id,
            campaign_id=campaign_id,
        )
        if settings.dry_run:
            return dry_run_response("gmail.send_followup_email", payload.model_dump(mode="json"))

        raise NotImplementedError(
            "Live Gmail sending requires wiring google-api-python-client OAuth credentials. "
            "The MCP contract is stable; implement provider transport here for production."
        )

    @mcp.tool()
    async def search_gmail_replies(query: str = "newer_than:14d", max_results: int = 25) -> dict[str, Any]:
        """Find recent Gmail replies that should be classified by the sales agent."""
        if settings.dry_run:
            return dry_run_response("gmail.search_replies", {"query": query, "max_results": max_results})
        raise NotImplementedError("Live Gmail search requires Gmail API OAuth transport.")
