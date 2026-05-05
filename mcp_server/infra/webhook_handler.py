from typing import Any

from fastapi import APIRouter, Header, HTTPException, Request

from mcp_server.config import MCPSettings
from mcp_server.utils.helpers import utc_now_iso, verify_hmac_signature

router = APIRouter(prefix="/mcp-webhooks", tags=["mcp-webhooks"])
_webhook_events: list[dict[str, Any]] = []


def create_webhook_router(settings: MCPSettings) -> APIRouter:
    @router.post("/{source}")
    async def receive_webhook(
        source: str,
        request: Request,
        x_signature: str | None = Header(default=None),
    ) -> dict[str, Any]:
        if settings.allowed_webhook_sources and source not in settings.allowed_webhook_sources:
            raise HTTPException(status_code=403, detail="Webhook source is not allowed.")

        body = await request.body()
        if settings.webhook_signing_secret:
            if not x_signature or not verify_hmac_signature(settings.webhook_signing_secret, body, x_signature):
                raise HTTPException(status_code=401, detail="Invalid webhook signature.")

        event = {
            "id": len(_webhook_events) + 1,
            "source": source,
            "received_at": utc_now_iso(),
            "payload": await request.json(),
        }
        _webhook_events.insert(0, event)
        del _webhook_events[500:]
        return {"status": "accepted", "event_id": event["id"]}

    return router


def register(mcp: Any, settings: MCPSettings) -> None:
    @mcp.tool()
    async def list_recent_webhook_events(source: str | None = None, limit: int = 25) -> list[dict[str, Any]]:
        """Inspect recent inbound provider webhooks for workflow debugging and event-driven automation."""
        events = _webhook_events
        if source:
            events = [event for event in events if event["source"] == source]
        return events[:limit]
