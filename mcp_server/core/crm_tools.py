from typing import Any

from mcp_server.config import MCPSettings
from mcp_server.utils.helpers import backend_request, dry_run_response
from mcp_server.utils.validators import PipelineStageUpdate


def register(mcp: Any, settings: MCPSettings) -> None:
    @mcp.tool()
    async def update_pipeline_stage(lead_id: int, stage: str, notes: str | None = None) -> dict[str, Any]:
        """Move a lead through the CRM pipeline after Claude classifies intent or outcomes."""
        update = PipelineStageUpdate(lead_id=lead_id, stage=stage, notes=notes)
        if settings.dry_run:
            return dry_run_response("crm.update_pipeline_stage", update.model_dump())
        if stage == "qualified":
            return await backend_request("POST", f"/leads/{lead_id}/score", settings=settings)
        if stage in {"closed_won", "closed_lost"}:
            return await backend_request(
                "POST",
                "/outcomes",
                settings=settings,
                json={
                    "lead_id": lead_id,
                    "status": stage.removeprefix("closed_"),
                    "notes": notes or "Closed from MCP pipeline update.",
                },
            )
        raise RuntimeError("Live CRM stage updates require a backend PATCH /leads/{lead_id} endpoint or direct CRM adapter.")

    @mcp.tool()
    async def get_campaign_performance(campaign_id: str | None = None) -> dict[str, Any]:
        """Return sales funnel metrics and campaign conversion context for optimization decisions."""
        if settings.dry_run:
            return {
                "status": "dry_run",
                "campaign_id": campaign_id,
                "reply_rate": 11.8,
                "qualified_rate": 37.5,
                "closed_won_rate": 8.4,
                "recommendation": "Increase spend on high-intent founder audiences and pause low-reply templates.",
            }
        conversion = await backend_request("GET", "/metrics/conversion", settings=settings)
        funnel = await backend_request("GET", "/metrics/funnel", settings=settings)
        return {"campaign_id": campaign_id, "conversion": conversion, "funnel": funnel}
