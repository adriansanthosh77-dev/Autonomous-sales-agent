from typing import Any

from mcp_server.config import MCPSettings
from mcp_server.utils.helpers import backend_request, dry_run_response


def register(mcp: Any, settings: MCPSettings) -> None:
    @mcp.tool()
    async def fetch_leads(status: str | None = None, limit: int = 50) -> list[dict[str, Any]] | dict[str, Any]:
        """Fetch leads from the CRM store; mirrors the spreadsheet-facing lead table contract."""
        if settings.dry_run:
            return [
                {
                    "id": 1,
                    "name": "Sample Buyer",
                    "email": "buyer@example.com",
                    "company": "Acme Growth",
                    "status": status or "qualified",
                    "source": "mcp_dry_run",
                }
            ][:limit]
        result = await backend_request("GET", "/leads", settings=settings, params={"status": status, "limit": limit})
        return result

    @mcp.tool()
    async def update_google_sheet(
        spreadsheet_id: str | None,
        range_name: str,
        values: list[list[str | int | float | bool | None]],
    ) -> dict[str, Any]:
        """Write rows into Google Sheets for operator review, reporting, or CRM sync."""
        sheet_id = spreadsheet_id or settings.google_sheets_default_spreadsheet_id
        payload = {"spreadsheet_id": sheet_id, "range_name": range_name, "values": values}
        if settings.dry_run:
            return dry_run_response("sheets.update_values", payload)
        if not sheet_id:
            raise RuntimeError("Google Sheets spreadsheet id is required.")
        raise NotImplementedError("Live Sheets updates require Google Sheets API OAuth transport.")
