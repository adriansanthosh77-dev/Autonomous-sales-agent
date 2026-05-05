from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from agents.api_catalog import API_SPECS_BY_AGENT


@dataclass(frozen=True)
class AgentSpec:
    slug: str
    name: str
    category: str
    engine: str | None
    mission: str
    triggers: tuple[str, ...]
    primary_tools: tuple[str, ...]
    handoffs: tuple[str, ...]
    guardrails: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        api_spec = API_SPECS_BY_AGENT.get(self.slug)
        data["api_tools"] = (api_spec.tool_name,) if api_spec else ()
        data["api_provider"] = api_spec.provider if api_spec else None
        return data


ENGINES: dict[str, dict[str, Any]] = {
    "outbound_engine": {
        "name": "Outbound Engine",
        "mission": "Turns ICP strategy into sourced, qualified, personalized, approved outreach sequences.",
        "agents": (
            "lead_sourcing",
            "lead_qualification",
            "personalization",
            "outreach_execution",
            "follow_up_strategy",
            "meeting_booking",
            "crm_update",
            "icp_refinement",
        ),
    },
    "inbound_engine": {
        "name": "Inbound Engine",
        "mission": "Processes replies, inbound intent, lifecycle signals, churn risk, and expansion opportunities.",
        "agents": (
            "reply_classification",
            "crm_update",
            "revenue_friction_detection",
            "churn_prevention",
            "expansion_revenue",
            "lifecycle_automation",
        ),
    },
}


COMMON_GUARDRAILS = (
    "Prefer dry-run or approval-required actions for external sends, spend changes, and page publishing.",
    "Log the reason for every state-changing action.",
    "Hand off when the next action belongs to a more specific agent.",
)


AGENT_SPECS: tuple[AgentSpec, ...] = (
    AgentSpec(
        slug="lead_sourcing",
        name="Lead Sourcing Agent",
        category="sales",
        engine="outbound_engine",
        mission="Find net-new accounts and contacts that match the current ICP.",
        triggers=("source leads", "find prospects", "scrape", "yc", "apollo", "hunter", "linkedin", "clearbit"),
        primary_tools=("fetch_leads", "create_or_import_lead", "trigger_background_sales_workflow"),
        handoffs=("lead_qualification", "icp_refinement", "crm_update"),
        guardrails=COMMON_GUARDRAILS,
    ),
    AgentSpec(
        slug="lead_qualification",
        name="Lead Qualification Agent",
        category="sales",
        engine="outbound_engine",
        mission="Score lead fit, buying intent, timing, and routing priority.",
        triggers=("qualify", "score lead", "lead fit", "intent", "high intent", "pipeline priority"),
        primary_tools=("fetch_high_intent_leads", "enrich_lead", "update_pipeline_stage"),
        handoffs=("personalization", "crm_update", "icp_refinement"),
        guardrails=COMMON_GUARDRAILS,
    ),
    AgentSpec(
        slug="personalization",
        name="Personalization Agent",
        category="sales",
        engine="outbound_engine",
        mission="Create account-specific messaging angles for email, WhatsApp, and follow-up sequences.",
        triggers=("personalize", "write draft", "message angle", "email copy", "whatsapp copy", "outbound copy"),
        primary_tools=("fetch_high_intent_leads", "enrich_lead", "get_top_converting_pages"),
        handoffs=("outreach_execution", "follow_up_strategy"),
        guardrails=COMMON_GUARDRAILS,
    ),
    AgentSpec(
        slug="outreach_execution",
        name="Outreach Execution Agent",
        category="sales",
        engine="outbound_engine",
        mission="Send approved email and WhatsApp outreach through controlled delivery tools.",
        triggers=("send email", "send whatsapp", "outreach", "launch sequence", "execute outreach"),
        primary_tools=("send_followup_email", "send_whatsapp_message", "schedule_workflow"),
        handoffs=("follow_up_strategy", "crm_update", "reply_classification"),
        guardrails=COMMON_GUARDRAILS + ("Never send unapproved outreach when approval is required.",),
    ),
    AgentSpec(
        slug="reply_classification",
        name="Reply Classification Agent",
        category="sales",
        engine="inbound_engine",
        mission="Classify replies into interested, not now, objection, unsubscribe, or handoff-needed outcomes.",
        triggers=("reply", "classify", "inbound", "objection", "unsubscribe", "interested"),
        primary_tools=("search_gmail_replies", "list_recent_webhook_events", "update_pipeline_stage"),
        handoffs=("meeting_booking", "follow_up_strategy", "crm_update", "revenue_friction_detection"),
        guardrails=COMMON_GUARDRAILS + ("Respect unsubscribe and suppression signals immediately.",),
    ),
    AgentSpec(
        slug="follow_up_strategy",
        name="Follow-Up Strategy Agent",
        category="sales",
        engine="outbound_engine",
        mission="Choose follow-up timing, channel, sequence variant, and escalation path.",
        triggers=("follow up", "sequence", "reminder", "cadence", "nurture", "ab test followup"),
        primary_tools=("schedule_workflow", "trigger_background_sales_workflow", "send_followup_email"),
        handoffs=("outreach_execution", "crm_update", "email_campaign_optimization"),
        guardrails=COMMON_GUARDRAILS,
    ),
    AgentSpec(
        slug="meeting_booking",
        name="Meeting Booking Agent",
        category="sales",
        engine="outbound_engine",
        mission="Turn interested replies into booked meetings and pre-call context.",
        triggers=("book meeting", "calendar", "calendly", "demo", "schedule call", "meeting"),
        primary_tools=("trigger_background_sales_workflow", "update_pipeline_stage", "update_google_sheet"),
        handoffs=("crm_update", "founder_decision_report"),
        guardrails=COMMON_GUARDRAILS + ("Do not book meetings without explicit user or prospect intent.",),
    ),
    AgentSpec(
        slug="crm_update",
        name="CRM Update Agent",
        category="operations",
        engine=None,
        mission="Keep lead records, pipeline stages, outcomes, sheets, and reporting fields clean.",
        triggers=("crm", "pipeline", "stage", "update sheet", "record outcome", "revops"),
        primary_tools=("update_pipeline_stage", "update_google_sheet", "get_campaign_performance"),
        handoffs=("revenue_leak_detection", "founder_decision_report"),
        guardrails=COMMON_GUARDRAILS,
    ),
    AgentSpec(
        slug="google_ads_optimization",
        name="Google Ads Optimization Agent",
        category="growth",
        engine=None,
        mission="Analyze and optimize Google Ads spend, keywords, campaigns, and conversion quality.",
        triggers=("google ads", "search ads", "keywords", "cpc", "cost per lead", "paid search"),
        primary_tools=("get_google_ads_performance", "launch_google_ads_campaign", "pull_ga4_conversion_report"),
        handoffs=("gtm_validation", "ga4_intelligence", "retargeting"),
        guardrails=COMMON_GUARDRAILS + ("Require approval before launching campaigns or changing spend.",),
    ),
    AgentSpec(
        slug="meta_ads_optimization",
        name="Meta Ads Optimization Agent",
        category="growth",
        engine=None,
        mission="Optimize Meta campaigns, creatives, audiences, and lead quality.",
        triggers=("meta ads", "facebook ads", "instagram ads", "creative", "audience", "paid social"),
        primary_tools=("create_retargeting_campaign", "pull_ga4_conversion_report", "get_campaign_performance"),
        handoffs=("retargeting", "channel_performance", "content_performance"),
        guardrails=COMMON_GUARDRAILS + ("Require approval before launching campaigns or changing spend.",),
    ),
    AgentSpec(
        slug="retargeting",
        name="Retargeting Agent",
        category="growth",
        engine=None,
        mission="Build retargeting audiences and campaigns from CRM, website, and lifecycle intent.",
        triggers=("retarget", "remarketing", "visited pricing", "abandoned", "warm audience"),
        primary_tools=("create_retargeting_campaign", "analyze_gtm_tracking", "trigger_background_workflow"),
        handoffs=("meta_ads_optimization", "google_ads_optimization", "lifecycle_automation"),
        guardrails=COMMON_GUARDRAILS,
    ),
    AgentSpec(
        slug="lifecycle_automation",
        name="Lifecycle Automation Agent",
        category="lifecycle",
        engine="inbound_engine",
        mission="Create activation, nurture, retention, and expansion journeys across the customer lifecycle.",
        triggers=("lifecycle", "iterable", "journey", "nurture", "activation", "retention"),
        primary_tools=("create_iterable_journey", "trigger_background_workflow", "fetch_high_intent_leads"),
        handoffs=("churn_prevention", "expansion_revenue", "email_campaign_optimization"),
        guardrails=COMMON_GUARDRAILS,
    ),
    AgentSpec(
        slug="email_campaign_optimization",
        name="Email Campaign Optimization Agent",
        category="growth",
        engine=None,
        mission="Improve subject lines, body copy, sequence steps, and reply rates from campaign results.",
        triggers=("email campaign", "subject line", "reply rate", "open rate", "sequence performance"),
        primary_tools=("get_campaign_performance", "send_followup_email", "schedule_workflow"),
        handoffs=("ab_testing", "personalization", "follow_up_strategy"),
        guardrails=COMMON_GUARDRAILS,
    ),
    AgentSpec(
        slug="ga4_intelligence",
        name="GA4 Intelligence Agent",
        category="analytics",
        engine=None,
        mission="Read GA4 conversion data and explain what channels, pages, and journeys are working.",
        triggers=("ga4", "analytics", "conversion report", "landing page", "traffic source"),
        primary_tools=("pull_ga4_conversion_report", "get_top_converting_pages"),
        handoffs=("channel_performance", "content_performance", "revenue_leak_detection"),
        guardrails=COMMON_GUARDRAILS,
    ),
    AgentSpec(
        slug="gsc_seo_opportunity",
        name="GSC SEO Opportunity Agent",
        category="growth",
        engine=None,
        mission="Find SEO opportunities from Search Console query, page, CTR, and ranking data.",
        triggers=("gsc", "search console", "seo", "keyword", "organic", "ranking"),
        primary_tools=("get_gsc_keyword_opportunities", "get_seo_opportunities"),
        handoffs=("contentful_optimization", "content_performance", "gtm_strategy"),
        guardrails=COMMON_GUARDRAILS,
    ),
    AgentSpec(
        slug="gtm_validation",
        name="GTM Validation Agent",
        category="analytics",
        engine=None,
        mission="Validate Google Tag Manager events, tags, triggers, and conversion measurement integrity.",
        triggers=("google tag manager", "tracking", "tag", "trigger", "conversion event", "gtm validation"),
        primary_tools=("validate_gtm_tracking_setup", "analyze_gtm_tracking"),
        handoffs=("ga4_intelligence", "revenue_leak_detection", "google_ads_optimization"),
        guardrails=COMMON_GUARDRAILS,
    ),
    AgentSpec(
        slug="revenue_leak_detection",
        name="Revenue Leak Detection Agent",
        category="analytics",
        engine=None,
        mission="Detect broken attribution, low conversion handoffs, missing follow-ups, and funnel loss.",
        triggers=("revenue leak", "leak", "dropoff", "funnel loss", "missing attribution", "lost revenue"),
        primary_tools=("get_campaign_performance", "pull_ga4_conversion_report", "validate_gtm_tracking_setup"),
        handoffs=("revenue_friction_detection", "crm_update", "founder_decision_report"),
        guardrails=COMMON_GUARDRAILS,
    ),
    AgentSpec(
        slug="contentful_optimization",
        name="Contentful Optimization Agent",
        category="growth",
        engine=None,
        mission="Update landing pages and CMS content for conversion and SEO experiments.",
        triggers=("contentful", "landing page", "cms", "page update", "optimize page"),
        primary_tools=("update_contentful_page", "optimize_contentful_landing_page", "get_seo_opportunities"),
        handoffs=("content_performance", "ab_testing", "gtm_validation"),
        guardrails=COMMON_GUARDRAILS + ("Require approval before publishing live page changes.",),
    ),
    AgentSpec(
        slug="ab_testing",
        name="A/B Testing Agent",
        category="growth",
        engine=None,
        mission="Design and evaluate experiments across copy, landing pages, channels, and sequences.",
        triggers=("a/b", "ab test", "experiment", "variant", "test result", "winner"),
        primary_tools=("get_campaign_performance", "get_top_converting_pages", "schedule_workflow"),
        handoffs=("content_performance", "email_campaign_optimization", "channel_performance"),
        guardrails=COMMON_GUARDRAILS,
    ),
    AgentSpec(
        slug="triggerdev_workflow",
        name="Trigger.dev Workflow Agent",
        category="operations",
        engine=None,
        mission="Create, trigger, inspect, and retry durable background workflows.",
        triggers=("trigger.dev", "background job", "workflow", "retry", "schedule", "durable"),
        primary_tools=("trigger_background_workflow", "trigger_background_sales_workflow", "get_background_job_status"),
        handoffs=("orchestrator", "agent_loop_learning"),
        guardrails=COMMON_GUARDRAILS,
    ),
    AgentSpec(
        slug="icp_refinement",
        name="ICP Refinement Agent",
        category="strategy",
        engine="outbound_engine",
        mission="Refine ICP criteria using reply rates, conversion, close rate, channel fit, and customer quality.",
        triggers=("icp", "ideal customer", "persona", "segment", "target market", "refine audience"),
        primary_tools=("get_campaign_performance", "fetch_high_intent_leads", "pull_ga4_conversion_report"),
        handoffs=("lead_sourcing", "google_ads_optimization", "founder_decision_report"),
        guardrails=COMMON_GUARDRAILS,
    ),
    AgentSpec(
        slug="gtm_strategy",
        name="GTM Strategy Agent",
        category="strategy",
        engine=None,
        mission="Plan go-to-market motion across ICP, channel, offer, content, ads, lifecycle, and sales motion.",
        triggers=("gtm strategy", "go to market", "growth plan", "market motion", "positioning"),
        primary_tools=("get_campaign_performance", "get_seo_opportunities", "pull_ga4_conversion_report"),
        handoffs=("channel_performance", "icp_refinement", "founder_decision_report"),
        guardrails=COMMON_GUARDRAILS,
    ),
    AgentSpec(
        slug="revenue_friction_detection",
        name="Revenue Friction Detection Agent",
        category="analytics",
        engine="inbound_engine",
        mission="Find objections, checkout friction, sales-cycle blockers, and handoff failures.",
        triggers=("friction", "objection", "blocked", "sales cycle", "handoff", "why not converting"),
        primary_tools=("search_gmail_replies", "get_campaign_performance", "pull_ga4_conversion_report"),
        handoffs=("reply_classification", "contentful_optimization", "founder_decision_report"),
        guardrails=COMMON_GUARDRAILS,
    ),
    AgentSpec(
        slug="churn_prevention",
        name="Churn Prevention Agent",
        category="lifecycle",
        engine="inbound_engine",
        mission="Identify churn risk signals and trigger retention playbooks.",
        triggers=("churn", "cancel", "retention", "risk", "downgrade", "inactive"),
        primary_tools=("create_iterable_journey", "trigger_background_workflow", "update_pipeline_stage"),
        handoffs=("lifecycle_automation", "crm_update", "founder_decision_report"),
        guardrails=COMMON_GUARDRAILS,
    ),
    AgentSpec(
        slug="expansion_revenue",
        name="Expansion Revenue Agent",
        category="lifecycle",
        engine="inbound_engine",
        mission="Find upsell, cross-sell, renewal, and expansion moments from account behavior.",
        triggers=("expansion", "upsell", "cross-sell", "renewal", "upgrade", "account growth"),
        primary_tools=("create_iterable_journey", "get_campaign_performance", "update_pipeline_stage"),
        handoffs=("lifecycle_automation", "crm_update", "founder_decision_report"),
        guardrails=COMMON_GUARDRAILS,
    ),
    AgentSpec(
        slug="founder_decision_report",
        name="Founder Decision Report Agent",
        category="strategy",
        engine=None,
        mission="Summarize what changed, what matters, and what decisions a founder should make next.",
        triggers=("founder report", "decision report", "weekly report", "summary", "what should we do"),
        primary_tools=("get_campaign_performance", "pull_ga4_conversion_report", "get_seo_opportunities"),
        handoffs=("orchestrator", "gtm_strategy", "agent_loop_learning"),
        guardrails=COMMON_GUARDRAILS,
    ),
    AgentSpec(
        slug="content_performance",
        name="Content Performance Agent",
        category="growth",
        engine=None,
        mission="Determine which content, pages, angles, and offers produce pipeline.",
        triggers=("content works", "best content", "blog", "page performance", "offer performance"),
        primary_tools=("get_top_converting_pages", "get_seo_opportunities", "pull_ga4_conversion_report"),
        handoffs=("contentful_optimization", "ab_testing", "gtm_strategy"),
        guardrails=COMMON_GUARDRAILS,
    ),
    AgentSpec(
        slug="channel_performance",
        name="Channel Performance Agent",
        category="growth",
        engine=None,
        mission="Compare channels by conversion quality, CAC, payback, and pipeline impact.",
        triggers=("channel", "which channel", "paid vs organic", "cac", "source performance"),
        primary_tools=("pull_ga4_conversion_report", "get_campaign_performance", "get_google_ads_performance"),
        handoffs=("google_ads_optimization", "meta_ads_optimization", "gtm_strategy"),
        guardrails=COMMON_GUARDRAILS,
    ),
    AgentSpec(
        slug="orchestrator",
        name="Orchestrator Agent",
        category="operations",
        engine=None,
        mission="Route work to the right agent, sequence multi-agent plans, and enforce approval boundaries.",
        triggers=("orchestrate", "route", "run system", "coordinate", "which agent", "multi-agent"),
        primary_tools=("route_agent_task", "list_business_agents", "trigger_background_workflow"),
        handoffs=("triggerdev_workflow", "agent_loop_learning"),
        guardrails=COMMON_GUARDRAILS + ("Prefer the most specific agent for execution.",),
    ),
    AgentSpec(
        slug="agent_loop_learning",
        name="Agent Loop Learning Agent",
        category="operations",
        engine=None,
        mission="Learn from outcomes and recommend improvements to ICP, messaging, channels, and workflows.",
        triggers=("learn", "improve", "feedback loop", "self improving", "upgrade system", "what changed"),
        primary_tools=("get_campaign_performance", "pull_ga4_conversion_report", "list_recent_webhook_events"),
        handoffs=("icp_refinement", "email_campaign_optimization", "founder_decision_report"),
        guardrails=COMMON_GUARDRAILS + ("Recommend changes before applying high-impact changes.",),
    ),
)


AGENTS_BY_SLUG = {agent.slug: agent for agent in AGENT_SPECS}


def list_agents(category: str | None = None, engine: str | None = None) -> list[dict[str, Any]]:
    agents = AGENT_SPECS
    if category:
        agents = tuple(agent for agent in agents if agent.category == category)
    if engine:
        agents = tuple(agent for agent in agents if agent.engine == engine)
    return [agent.to_dict() for agent in agents]


def get_agent(slug: str) -> dict[str, Any]:
    try:
        return AGENTS_BY_SLUG[slug].to_dict()
    except KeyError as error:
        raise ValueError(f"Unknown agent: {slug}") from error


def route_task(task: str) -> dict[str, Any]:
    normalized = task.lower()
    ranked: list[tuple[int, AgentSpec]] = []
    for agent in AGENT_SPECS:
        score = sum(3 for trigger in agent.triggers if trigger in normalized)
        score += sum(1 for tool in agent.primary_tools if tool.replace("_", " ") in normalized)
        if agent.slug.replace("_", " ") in normalized:
            score += 4
        if score:
            ranked.append((score, agent))

    if not ranked:
        fallback = AGENTS_BY_SLUG["orchestrator"]
        return {
            "agent": fallback.to_dict(),
            "confidence": 0.35,
            "reason": "No specific trigger matched, so the orchestrator should clarify and route.",
            "alternates": [],
        }

    ranked.sort(key=lambda item: item[0], reverse=True)
    top_score, top_agent = ranked[0]
    alternates = [agent.to_dict() for _, agent in ranked[1:4]]
    confidence = min(0.95, 0.5 + (top_score * 0.08))
    return {
        "agent": top_agent.to_dict(),
        "confidence": round(confidence, 2),
        "reason": f"Matched task language to {top_agent.name} triggers.",
        "alternates": alternates,
    }
