from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class AgentApiSpec:
    agent_slug: str
    tool_name: str
    provider: str
    purpose: str
    env_keys: tuple[str, ...]
    side_effect: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


AGENT_API_SPECS: tuple[AgentApiSpec, ...] = (
    AgentApiSpec("lead_sourcing", "search_apollo_prospects", "Apollo", "Search ICP-matched B2B contacts and accounts.", ("APOLLO_API_KEY",)),
    AgentApiSpec("lead_qualification", "enrich_clearbit_company", "Clearbit", "Enrich company firmographics for fit scoring.", ("CLEARBIT_API_KEY",)),
    AgentApiSpec("personalization", "research_company_context", "SerpAPI", "Fetch recent account context for personalized outreach.", ("SERPAPI_API_KEY",)),
    AgentApiSpec("outreach_execution", "send_sendgrid_outbound_email", "SendGrid", "Send approved outbound email at scale.", ("SENDGRID_API_KEY",), True),
    AgentApiSpec("reply_classification", "fetch_gmail_reply_threads", "Gmail", "Fetch reply threads for intent classification.", ("GMAIL_CREDENTIALS_JSON",)),
    AgentApiSpec("follow_up_strategy", "upsert_customerio_followup_campaign", "Customer.io", "Create or update follow-up campaign logic.", ("CUSTOMERIO_API_KEY",), True),
    AgentApiSpec("meeting_booking", "create_calendly_invite", "Calendly", "Create or prepare a booking link for interested prospects.", ("CALENDLY_API_KEY",), True),
    AgentApiSpec("crm_update", "sync_hubspot_contact", "HubSpot", "Sync lead, lifecycle, and deal fields to CRM.", ("HUBSPOT_ACCESS_TOKEN",), True),
    AgentApiSpec("google_ads_optimization", "pull_google_ads_recommendations", "Google Ads", "Pull optimization recommendations and wasted-spend signals.", ("GOOGLE_ADS_DEVELOPER_TOKEN", "GOOGLE_ADS_CUSTOMER_ID")),
    AgentApiSpec("meta_ads_optimization", "pull_meta_ads_insights", "Meta Ads", "Pull ad set, creative, and audience performance.", ("META_ADS_ACCESS_TOKEN", "META_ADS_ACCOUNT_ID")),
    AgentApiSpec("retargeting", "sync_meta_custom_audience", "Meta Custom Audiences", "Sync high-intent CRM or site audiences for retargeting.", ("META_ADS_ACCESS_TOKEN", "META_ADS_ACCOUNT_ID"), True),
    AgentApiSpec("lifecycle_automation", "sync_iterable_lifecycle_event", "Iterable", "Send lifecycle events that trigger journeys.", ("ITERABLE_API_KEY",), True),
    AgentApiSpec("email_campaign_optimization", "pull_mailchimp_campaign_report", "Mailchimp", "Analyze campaign opens, clicks, replies, and list quality.", ("MAILCHIMP_API_KEY",)),
    AgentApiSpec("ga4_intelligence", "pull_ga4_funnel_paths", "GA4", "Analyze conversion paths and page-to-lead behavior.", ("GA4_PROPERTY_ID",)),
    AgentApiSpec("gsc_seo_opportunity", "pull_ahrefs_keyword_gaps", "Ahrefs", "Find ranking and backlink opportunities beyond GSC.", ("AHREFS_API_KEY",)),
    AgentApiSpec("gtm_validation", "inspect_gtm_container_versions", "Google Tag Manager", "Inspect container versions, tags, triggers, and variables.", ("GTM_ACCOUNT_ID", "GTM_CONTAINER_ID")),
    AgentApiSpec("revenue_leak_detection", "pull_stripe_revenue_events", "Stripe", "Find failed payments, refunds, plan changes, and revenue leakage.", ("STRIPE_API_KEY",)),
    AgentApiSpec("contentful_optimization", "audit_contentful_entry_health", "Contentful", "Audit CMS fields, publish state, and optimization readiness.", ("CONTENTFUL_SPACE_ID", "CONTENTFUL_MANAGEMENT_TOKEN")),
    AgentApiSpec("ab_testing", "create_optimizely_experiment", "Optimizely", "Create or stage an approved page or messaging experiment.", ("OPTIMIZELY_API_KEY",), True),
    AgentApiSpec("triggerdev_workflow", "trigger_triggerdev_durable_job", "Trigger.dev", "Run durable jobs for enrichment, follow-up, reporting, or sync.", ("TRIGGERDEV_API_KEY",), True),
    AgentApiSpec("icp_refinement", "pull_linkedin_company_signals", "LinkedIn", "Collect company and role signals that refine ICP criteria.", ("LINKEDIN_EMAIL", "LINKEDIN_PASSWORD")),
    AgentApiSpec("gtm_strategy", "pull_crunchbase_market_signals", "Crunchbase", "Read market, funding, and category signals for GTM strategy.", ("CRUNCHBASE_API_KEY",)),
    AgentApiSpec("revenue_friction_detection", "pull_hotjar_friction_signals", "Hotjar", "Find page friction from heatmaps, recordings, and surveys.", ("HOTJAR_API_KEY", "HOTJAR_SITE_ID")),
    AgentApiSpec("churn_prevention", "pull_zendesk_churn_risk_tickets", "Zendesk", "Find support-ticket patterns that indicate churn risk.", ("ZENDESK_SUBDOMAIN", "ZENDESK_API_TOKEN")),
    AgentApiSpec("expansion_revenue", "pull_salesforce_expansion_opportunities", "Salesforce", "Find expansion, renewal, and upsell opportunities.", ("SALESFORCE_INSTANCE_URL", "SALESFORCE_ACCESS_TOKEN")),
    AgentApiSpec("founder_decision_report", "send_slack_founder_report", "Slack", "Send concise decision reports to the founder or revenue channel.", ("SLACK_BOT_TOKEN", "SLACK_REVENUE_CHANNEL_ID"), True),
    AgentApiSpec("content_performance", "pull_semrush_content_opportunities", "Semrush", "Analyze competing pages and content gaps.", ("SEMRUSH_API_KEY",)),
    AgentApiSpec("channel_performance", "pull_mixpanel_channel_cohorts", "Mixpanel", "Compare channel cohorts by activation and conversion quality.", ("MIXPANEL_API_SECRET",)),
    AgentApiSpec("orchestrator", "publish_segment_orchestration_event", "Segment", "Emit orchestration events for downstream systems.", ("SEGMENT_WRITE_KEY",), True),
    AgentApiSpec("agent_loop_learning", "pull_posthog_learning_signals", "PostHog", "Learn from product behavior, experiments, and funnel usage.", ("POSTHOG_API_KEY",)),
)


API_SPECS_BY_AGENT = {spec.agent_slug: spec for spec in AGENT_API_SPECS}
API_SPECS_BY_TOOL = {spec.tool_name: spec for spec in AGENT_API_SPECS}


def list_agent_api_specs(agent_slug: str | None = None) -> list[dict[str, Any]]:
    specs = AGENT_API_SPECS
    if agent_slug:
        specs = tuple(spec for spec in specs if spec.agent_slug == agent_slug)
    return [spec.to_dict() for spec in specs]


def get_agent_api_spec(tool_name: str) -> dict[str, Any]:
    try:
        return API_SPECS_BY_TOOL[tool_name].to_dict()
    except KeyError as error:
        raise ValueError(f"Unknown agent API tool: {tool_name}") from error
