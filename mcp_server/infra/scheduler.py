from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field

from mcp_server.config import MCPSettings
from mcp_server.utils.helpers import dry_run_response

_scheduled_jobs: list[dict[str, Any]] = []


class ScheduledWorkflow(BaseModel):
    workflow_id: str = Field(min_length=1)
    run_at: datetime
    payload: dict[str, Any] = Field(default_factory=dict)
    idempotency_key: str | None = None


def register(mcp: Any, settings: MCPSettings) -> None:
    @mcp.tool()
    async def schedule_workflow(
        workflow_id: str,
        run_at_iso: str,
        payload: dict[str, Any],
        idempotency_key: str | None = None,
    ) -> dict[str, Any]:
        """Schedule a workflow for future execution; production can back this with Trigger.dev, Celery, or Redis."""
        run_at = datetime.fromisoformat(run_at_iso.replace("Z", "+00:00"))
        job = ScheduledWorkflow(
            workflow_id=workflow_id,
            run_at=run_at,
            payload=payload,
            idempotency_key=idempotency_key,
        )
        record = {
            "id": len(_scheduled_jobs) + 1,
            "status": "scheduled",
            "workflow_id": job.workflow_id,
            "run_at": job.run_at.astimezone(timezone.utc).isoformat(),
            "payload": job.payload,
            "idempotency_key": job.idempotency_key,
        }
        _scheduled_jobs.insert(0, record)
        if settings.dry_run:
            return dry_run_response("scheduler.schedule_workflow", record)
        return record

    @mcp.tool()
    async def list_scheduled_workflows(limit: int = 50) -> list[dict[str, Any]]:
        """List pending scheduled workflows for operator visibility."""
        return _scheduled_jobs[:limit]
