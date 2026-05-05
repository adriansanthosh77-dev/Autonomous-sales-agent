# Agent Layer

This directory defines the business-agent layer above MCP tools. Agents own judgement, routing, guardrails, and handoffs. MCP tools own execution against Gmail, WhatsApp, Google Sheets, Ads, Analytics, Contentful, Iterable, Trigger.dev, and the backend CRM API.

## Count

- 30 business agents in `agents/registry.py`
- 2 engines: `outbound_engine` and `inbound_engine`
- 30 agent API integrations in `agents/api_catalog.py`
- 37 MCP agent/API tools: `list_business_agents`, `get_business_agent`, `route_agent_task`, `list_agent_engines`, `list_agent_api_integrations`, `get_agent_api_integration`, `check_agent_api_readiness`, plus 30 provider-specific API tools

## Engines

`Outbound Engine` handles lead sourcing, qualification, personalization, outreach execution, follow-up strategy, meeting booking, CRM updates, and ICP refinement.

`Inbound Engine` handles replies, inbound intent, revenue friction, churn prevention, expansion revenue, lifecycle automation, and CRM updates.

## Agents

| Agent | Category | Main job |
| --- | --- | --- |
| Lead Sourcing Agent | sales | Find net-new accounts and contacts that match the ICP. |
| Lead Qualification Agent | sales | Score lead fit, buying intent, timing, and priority. |
| Personalization Agent | sales | Create account-specific email and WhatsApp messaging angles. |
| Outreach Execution Agent | sales | Send approved outbound through controlled delivery tools. |
| Reply Classification Agent | sales | Classify replies and route next actions. |
| Follow-Up Strategy Agent | sales | Choose follow-up timing, channel, and sequence variant. |
| Meeting Booking Agent | sales | Convert interested replies into booked meetings. |
| CRM Update Agent | operations | Keep pipeline stages, outcomes, sheets, and reporting clean. |
| Google Ads Optimization Agent | growth | Optimize Google Ads spend, keywords, and conversion quality. |
| Meta Ads Optimization Agent | growth | Optimize Meta campaigns, creatives, and audiences. |
| Retargeting Agent | growth | Build retargeting audiences and campaigns from intent. |
| Lifecycle Automation Agent | lifecycle | Create activation, nurture, retention, and expansion journeys. |
| Email Campaign Optimization Agent | growth | Improve subject lines, body copy, and reply rates. |
| GA4 Intelligence Agent | analytics | Explain channel, page, and conversion performance. |
| GSC SEO Opportunity Agent | growth | Find SEO opportunities from Search Console data. |
| GTM Validation Agent | analytics | Validate Google Tag Manager events and conversion tracking. |
| Revenue Leak Detection Agent | analytics | Detect broken attribution, missed follow-ups, and funnel loss. |
| Contentful Optimization Agent | growth | Update CMS pages for SEO and conversion experiments. |
| A/B Testing Agent | growth | Design and evaluate experiments across copy, pages, and channels. |
| Trigger.dev Workflow Agent | operations | Trigger, inspect, and retry durable background workflows. |
| ICP Refinement Agent | strategy | Improve ICP criteria from performance and revenue signals. |
| GTM Strategy Agent | strategy | Plan go-to-market motion across ICP, offer, channel, and lifecycle. |
| Revenue Friction Detection Agent | analytics | Find objections, blockers, and failed handoffs. |
| Churn Prevention Agent | lifecycle | Identify churn signals and trigger retention playbooks. |
| Expansion Revenue Agent | lifecycle | Find upsell, cross-sell, renewal, and expansion opportunities. |
| Founder Decision Report Agent | strategy | Summarize decisions the founder should make next. |
| Content Performance Agent | growth | Identify which content, pages, angles, and offers create pipeline. |
| Channel Performance Agent | growth | Compare channels by CAC, conversion quality, and pipeline impact. |
| Orchestrator Agent | operations | Route work, sequence plans, and enforce approval boundaries. |
| Agent Loop Learning Agent | operations | Learn from outcomes and recommend system upgrades. |

## How Claude should use this

Claude should route the user's task with `route_agent_task`, inspect the selected agent with `get_business_agent`, then call only the MCP tools listed in that agent's `primary_tools` unless a handoff is needed.

Each agent also has one `api_tools` entry that represents its main provider API integration. These API tools are dry-run safe by default through `MCP_DRY_RUN=true`; live adapters should be implemented behind the existing function boundary once credentials, approval rules, and provider rate limits are finalized.
