import os
from typing import Any

from agents.api_catalog import AGENT_API_SPECS, API_SPECS_BY_TOOL, get_agent_api_spec, list_agent_api_specs
from mcp_server.config import MCPSettings
from mcp_server.utils.helpers import dry_run_response, utc_now_iso


def _missing_env(env_keys: tuple[str, ...]) -> list[str]:
    return [key for key in env_keys if not os.getenv(key)]


def _api_response(settings: MCPSettings, tool_name: str, payload: dict[str, Any]) -> dict[str, Any]:
    spec = API_SPECS_BY_TOOL[tool_name]
    body = {
        "agent": spec.agent_slug,
        "provider": spec.provider,
        "tool_name": spec.tool_name,
        "purpose": spec.purpose,
        "side_effect": spec.side_effect,
        "missing_env": _missing_env(spec.env_keys),
        "payload": payload,
    }
    if settings.dry_run:
        return dry_run_response(f"agent_api.{tool_name}", body)
    if body["missing_env"]:
        raise RuntimeError(f"{spec.provider} is missing env vars: {', '.join(body['missing_env'])}")
    raise NotImplementedError(f"Live {spec.provider} adapter for {tool_name} should be implemented here.")


def register(mcp: Any, settings: MCPSettings) -> None:
    @mcp.tool()
    async def list_agent_api_integrations(agent_slug: str | None = None) -> list[dict[str, Any]]:
        """List the 30 agent-to-API integration contracts."""
        return list_agent_api_specs(agent_slug=agent_slug)

    @mcp.tool()
    async def get_agent_api_integration(tool_name: str) -> dict[str, Any]:
        """Inspect one agent API integration contract."""
        return get_agent_api_spec(tool_name)

    @mcp.tool()
    async def check_agent_api_readiness() -> dict[str, Any]:
        """Check which agent APIs have their required environment variables configured."""
        readiness = []
        for spec in AGENT_API_SPECS:
            missing = _missing_env(spec.env_keys)
            readiness.append(
                {
                    "agent": spec.agent_slug,
                    "tool_name": spec.tool_name,
                    "provider": spec.provider,
                    "ready": not missing,
                    "missing_env": missing,
                }
            )
        return {"checked_at": utc_now_iso(), "ready_count": sum(1 for item in readiness if item["ready"]), "items": readiness}

    @mcp.tool()
    async def search_apollo_prospects(query: str, limit: int = 25, icp: str | None = None) -> dict[str, Any]:
        """Apollo API for the Lead Sourcing Agent."""
        return _api_response(settings, "search_apollo_prospects", {"query": query, "limit": limit, "icp": icp})

    @mcp.tool()
    async def enrich_clearbit_company(domain: str, include_people: bool = False) -> dict[str, Any]:
        """Clearbit API for the Lead Qualification Agent."""
        return _api_response(settings, "enrich_clearbit_company", {"domain": domain, "include_people": include_people})

    @mcp.tool()
    async def research_company_context(company: str, domain: str | None = None) -> dict[str, Any]:
        """SerpAPI research for the Personalization Agent."""
        return _api_response(settings, "research_company_context", {"company": company, "domain": domain})

    @mcp.tool()
    async def send_sendgrid_outbound_email(to_email: str, subject: str, body: str, campaign_id: str | None = None) -> dict[str, Any]:
        """SendGrid API for the Outreach Execution Agent."""
        return _api_response(settings, "send_sendgrid_outbound_email", {"to_email": to_email, "subject": subject, "body": body, "campaign_id": campaign_id})

    @mcp.tool()
    async def fetch_gmail_reply_threads(query: str = "newer_than:14d", max_results: int = 25) -> dict[str, Any]:
        """Gmail API for the Reply Classification Agent."""
        return _api_response(settings, "fetch_gmail_reply_threads", {"query": query, "max_results": max_results})

    @mcp.tool()
    async def upsert_customerio_followup_campaign(campaign_name: str, steps: list[dict[str, Any]]) -> dict[str, Any]:
        """Customer.io API for the Follow-Up Strategy Agent."""
        return _api_response(settings, "upsert_customerio_followup_campaign", {"campaign_name": campaign_name, "steps": steps})

    @mcp.tool()
    async def create_calendly_invite(lead_email: str, event_type: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
        """Calendly API for the Meeting Booking Agent."""
        return _api_response(settings, "create_calendly_invite", {"lead_email": lead_email, "event_type": event_type, "context": context or {}})

    @mcp.tool()
    async def sync_hubspot_contact(email: str, properties: dict[str, Any]) -> dict[str, Any]:
        """HubSpot API for the CRM Update Agent."""
        return _api_response(settings, "sync_hubspot_contact", {"email": email, "properties": properties})

    @mcp.tool()
    async def pull_google_ads_recommendations(customer_id: str | None = None, days: int = 14) -> dict[str, Any]:
        """Google Ads API for the Google Ads Optimization Agent."""
        return _api_response(settings, "pull_google_ads_recommendations", {"customer_id": customer_id, "days": days})

    @mcp.tool()
    async def pull_meta_ads_insights(campaign_id: str | None = None, days: int = 14) -> dict[str, Any]:
        """Meta Ads API for the Meta Ads Optimization Agent."""
        return _api_response(settings, "pull_meta_ads_insights", {"campaign_id": campaign_id, "days": days})

    @mcp.tool()
    async def sync_meta_custom_audience(audience_name: str, identifiers: list[str]) -> dict[str, Any]:
        """Meta Custom Audiences API for the Retargeting Agent."""
        return _api_response(settings, "sync_meta_custom_audience", {"audience_name": audience_name, "identifiers_count": len(identifiers)})

    @mcp.tool()
    async def sync_iterable_lifecycle_event(email: str, event_name: str, data_fields: dict[str, Any]) -> dict[str, Any]:
        """Iterable API for the Lifecycle Automation Agent."""
        return _api_response(settings, "sync_iterable_lifecycle_event", {"email": email, "event_name": event_name, "data_fields": data_fields})

    @mcp.tool()
    async def pull_mailchimp_campaign_report(campaign_id: str, days: int = 30) -> dict[str, Any]:
        """Mailchimp API for the Email Campaign Optimization Agent."""
        return _api_response(settings, "pull_mailchimp_campaign_report", {"campaign_id": campaign_id, "days": days})

    @mcp.tool()
    async def pull_ga4_funnel_paths(conversion_event: str = "generate_lead", days: int = 30) -> dict[str, Any]:
        """GA4 API for the GA4 Intelligence Agent."""
        return _api_response(settings, "pull_ga4_funnel_paths", {"conversion_event": conversion_event, "days": days})

    @mcp.tool()
    async def pull_ahrefs_keyword_gaps(domain: str, competitors: list[str]) -> dict[str, Any]:
        """Ahrefs API for the GSC SEO Opportunity Agent."""
        return _api_response(settings, "pull_ahrefs_keyword_gaps", {"domain": domain, "competitors": competitors})

    @mcp.tool()
    async def inspect_gtm_container_versions(container_id: str | None = None) -> dict[str, Any]:
        """Google Tag Manager API for the GTM Validation Agent."""
        return _api_response(settings, "inspect_gtm_container_versions", {"container_id": container_id})

    @mcp.tool()
    async def pull_stripe_revenue_events(customer_id: str | None = None, days: int = 30) -> dict[str, Any]:
        """Stripe API for the Revenue Leak Detection Agent."""
        return _api_response(settings, "pull_stripe_revenue_events", {"customer_id": customer_id, "days": days})

    @mcp.tool()
    async def audit_contentful_entry_health(entry_id: str) -> dict[str, Any]:
        """Contentful API for the Contentful Optimization Agent."""
        return _api_response(settings, "audit_contentful_entry_health", {"entry_id": entry_id})

    @mcp.tool()
    async def create_optimizely_experiment(name: str, page_url: str, variants: list[dict[str, Any]]) -> dict[str, Any]:
        """Optimizely API for the A/B Testing Agent."""
        return _api_response(settings, "create_optimizely_experiment", {"name": name, "page_url": page_url, "variants": variants})

    @mcp.tool()
    async def trigger_triggerdev_durable_job(workflow_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        """Trigger.dev API for the Trigger.dev Workflow Agent."""
        return _api_response(settings, "trigger_triggerdev_durable_job", {"workflow_id": workflow_id, "payload": payload})

    @mcp.tool()
    async def pull_linkedin_company_signals(company: str, domain: str | None = None) -> dict[str, Any]:
        """LinkedIn API/scraping adapter for the ICP Refinement Agent."""
        return _api_response(settings, "pull_linkedin_company_signals", {"company": company, "domain": domain})

    @mcp.tool()
    async def pull_crunchbase_market_signals(company_or_category: str) -> dict[str, Any]:
        """Crunchbase API for the GTM Strategy Agent."""
        return _api_response(settings, "pull_crunchbase_market_signals", {"company_or_category": company_or_category})

    @mcp.tool()
    async def pull_hotjar_friction_signals(page_url: str, days: int = 30) -> dict[str, Any]:
        """Hotjar API for the Revenue Friction Detection Agent."""
        return _api_response(settings, "pull_hotjar_friction_signals", {"page_url": page_url, "days": days})

    @mcp.tool()
    async def pull_zendesk_churn_risk_tickets(query: str = "type:ticket status<solved", days: int = 30) -> dict[str, Any]:
        """Zendesk API for the Churn Prevention Agent."""
        return _api_response(settings, "pull_zendesk_churn_risk_tickets", {"query": query, "days": days})

    @mcp.tool()
    async def pull_salesforce_expansion_opportunities(account_id: str | None = None) -> dict[str, Any]:
        """Salesforce API for the Expansion Revenue Agent."""
        return _api_response(settings, "pull_salesforce_expansion_opportunities", {"account_id": account_id})

    @mcp.tool()
    async def send_slack_founder_report(channel_id: str | None, report: str) -> dict[str, Any]:
        """Slack API for the Founder Decision Report Agent."""
        return _api_response(settings, "send_slack_founder_report", {"channel_id": channel_id or settings.slack_revenue_channel_id, "report": report})

    @mcp.tool()
    async def pull_semrush_content_opportunities(domain: str, keyword: str | None = None) -> dict[str, Any]:
        """Semrush API for the Content Performance Agent."""
        return _api_response(settings, "pull_semrush_content_opportunities", {"domain": domain, "keyword": keyword})

    @mcp.tool()
    async def pull_mixpanel_channel_cohorts(event_name: str, days: int = 30) -> dict[str, Any]:
        """Mixpanel API for the Channel Performance Agent."""
        return _api_response(settings, "pull_mixpanel_channel_cohorts", {"event_name": event_name, "days": days})

    @mcp.tool()
    async def publish_segment_orchestration_event(user_id: str, event_name: str, properties: dict[str, Any]) -> dict[str, Any]:
        """Segment API for the Orchestrator Agent."""
        return _api_response(settings, "publish_segment_orchestration_event", {"user_id": user_id, "event_name": event_name, "properties": properties})

    @mcp.tool()
    async def pull_posthog_learning_signals(project_id: str | None = None, days: int = 30) -> dict[str, Any]:
        """PostHog API for the Agent Loop Learning Agent."""
        return _api_response(settings, "pull_posthog_learning_signals", {"project_id": project_id, "days": days})
