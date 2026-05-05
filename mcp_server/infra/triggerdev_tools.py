from typing import Any

from mcp_server.config import MCPSettings
from mcp_server.utils.auth import bearer, require_configured
from mcp_server.utils.helpers import dry_run_response, request_json


def register(mcp: Any, settings: MCPSettings) -> None:
    @mcp.tool()
    async def trigger_background_workflow(
        workflow_id: str,
        payload: dict[str, Any],
        idempotency_key: str | None = None,
    ) -> dict[str, Any]:
        """Trigger a durable background workflow through Trigger.dev."""
        body = {"payload": payload}
        if idempotency_key:
            body["idempotencyKey"] = idempotency_key
        if settings.dry_run:
            return dry_run_response("triggerdev.trigger_workflow", {"workflow_id": workflow_id, **body})

        require_configured("Trigger.dev", triggerdev_api_key=settings.triggerdev_api_key)
        url = f"{settings.triggerdev_base_url.rstrip('/')}/api/v1/tasks/{workflow_id}/trigger"
        return await request_json("POST", url, settings=settings, headers=bearer(settings.triggerdev_api_key), json=body)

    @mcp.tool()
    async def trigger_background_sales_workflow(
        lead_id: int,
        workflow_type: str = "follow_up_sequence",
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Trigger a sales automation workflow such as enrichment, follow-up, scoring, or handoff."""
        payload = {"lead_id": lead_id, "workflow_type": workflow_type, "context": context or {}}
        return await trigger_background_workflow(
            workflow_id=workflow_type,
            payload=payload,
            idempotency_key=f"{workflow_type}:{lead_id}",
        )

    @mcp.tool()
    async def get_background_job_status(run_id: str) -> dict[str, Any]:
        """Fetch Trigger.dev run state so Claude can decide whether to continue, retry, or alert an operator."""
        if settings.dry_run:
            return dry_run_response("triggerdev.get_run", {"run_id": run_id})
        require_configured("Trigger.dev", triggerdev_api_key=settings.triggerdev_api_key)
        url = f"{settings.triggerdev_base_url.rstrip('/')}/api/v1/runs/{run_id}"
        return await request_json("GET", url, settings=settings, headers=bearer(settings.triggerdev_api_key))
