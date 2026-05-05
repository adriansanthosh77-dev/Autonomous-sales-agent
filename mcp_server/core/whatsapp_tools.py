from typing import Any

from mcp_server.config import MCPSettings
from mcp_server.utils.auth import bearer, require_configured
from mcp_server.utils.helpers import dry_run_response, request_json
from mcp_server.utils.validators import WhatsAppPayload


def register(mcp: Any, settings: MCPSettings) -> None:
    @mcp.tool()
    async def send_whatsapp_message(
        to_phone: str,
        message: str,
        lead_id: int | None = None,
        template_name: str | None = None,
    ) -> dict[str, Any]:
        """Send a WhatsApp Business message for approved sales or lifecycle outreach."""
        payload = WhatsAppPayload(to_phone=to_phone, message=message, lead_id=lead_id, template_name=template_name)
        provider_payload: dict[str, Any] = {
            "messaging_product": "whatsapp",
            "to": payload.to_phone,
            "type": "text",
            "text": {"body": payload.message},
        }
        if settings.dry_run:
            return dry_run_response("whatsapp.send_message", payload.model_dump())

        require_configured(
            "WhatsApp Business API",
            whatsapp_phone_number_id=settings.whatsapp_phone_number_id,
            whatsapp_access_token=settings.whatsapp_access_token,
        )
        url = f"{settings.whatsapp_api_url.rstrip('/')}/{settings.whatsapp_phone_number_id}/messages"
        return await request_json("POST", url, settings=settings, headers=bearer(settings.whatsapp_access_token), json=provider_payload)
