from typing import Any

from mcp_server.config import MCPSettings
from mcp_server.utils.helpers import backend_request, dry_run_response
from mcp_server.utils.validators import LeadInput


def register(mcp: Any, settings: MCPSettings) -> None:
    @mcp.tool()
    async def fetch_high_intent_leads(limit: int = 25) -> list[dict[str, Any]] | dict[str, Any]:
        """Fetch leads that are qualified, recently replied, or otherwise ready for human-quality follow-up."""
        if settings.dry_run:
            return [
                {
                    "id": 101,
                    "name": "Priya Shah",
                    "email": "priya@example.com",
                    "company": "Northstar AI",
                    "title": "Head of Growth",
                    "intent_reason": "replied_interested and visited pricing page",
                    "qualification_score": 8.7,
                }
            ][:limit]
        return await backend_request("GET", "/leads/hot", settings=settings, params={"limit": limit})

    @mcp.tool()
    async def create_or_import_lead(
        name: str,
        email: str,
        company: str,
        title: str | None = None,
        phone: str | None = None,
        website: str | None = None,
        industry: str | None = None,
        source: str = "mcp",
    ) -> dict[str, Any]:
        """Create a CRM lead from Claude-discovered account intelligence."""
        lead = LeadInput(
            name=name,
            email=email,
            company=company,
            title=title,
            phone=phone,
            website=website,
            industry=industry,
            source=source,
        )
        if settings.dry_run:
            return dry_run_response("leads.create", lead.model_dump(mode="json"))
        return await backend_request("POST", "/leads", settings=settings, json=lead.model_dump(mode="json"))

    @mcp.tool()
    async def enrich_lead(email: str, company_domain: str | None = None) -> dict[str, Any]:
        """Enrich a lead using configured enrichment providers such as Hunter, Apollo, or Clearbit."""
        payload = {"email": email, "company_domain": company_domain}
        if settings.dry_run:
            return dry_run_response("leads.enrich", payload)
        raise NotImplementedError("Wire Hunter/Apollo/Clearbit enrichment here based on configured provider priority.")
