# Autonomous Sales & GTM Agent System

An AI-powered go-to-market automation system built on Claude, MCP, and Trigger.dev. Connects a 30-agent registry to your marketing and sales stack — turning data into action without manual execution.

---

## What It Does

Most sales and marketing tools tell you what happened. This system makes something happen about it.

- **Lead generation** — scrapes YC, Hunter, Apollo, LinkedIn, and Clearbit in parallel
- **Outbound engine** — Claude-generated drafts with operator approval before any send
- **Inbound engine** — classifies replies, routes interested leads to booking, respects unsubscribes
- **Growth automation** — Google Ads, Meta, GA4, GSC, GTM, Contentful, Iterable connected via MCP
- **Founder reporting** — weekly decision reports pushed to Slack, not dashboards
- **Self-improving** — agent loop learning refines ICP and messaging from outcomes

---

## Architecture

Three layers that don't bleed into each other:

```
┌─────────────────────────────────────────────┐
│           AGENT REGISTRY                    │
│  30 business agents with missions,          │
│  handoffs, guardrails, and routing logic    │
│  agents/registry.py + api_catalog.py        │
└──────────────────┬──────────────────────────┘
                   │ Claude calls tools
┌──────────────────▼──────────────────────────┐
│           MCP SERVER                        │
│  Business-oriented tool surface             │
│  core/ growth/ infra/ utils/                │
│  Dry-run safe. Provider-agnostic contracts. │
└──────────────────┬──────────────────────────┘
                   │ HTTP to backend + providers
┌──────────────────▼──────────────────────────┐
│           FASTAPI BACKEND                   │
│  Lead store, draft queue, job queue,        │
│  delivery, metrics, operator console        │
│  backend/api.py + storage.py                │
└─────────────────────────────────────────────┘
```

The agent registry owns business logic. The MCP server owns provider contracts. The backend owns data and delivery. A SendGrid API change never touches agent prompts. An ICP strategy change never touches tool implementations.

---

## Project Structure

```
autonomous-sales-system/
│
├── agents/
│   ├── registry.py          # 30 agent specs — missions, tools, handoffs, guardrails
│   ├── api_catalog.py       # 30 provider contracts — tool name, env vars, side-effect flag
│   └── __init__.py
│
├── mcp_server/
│   ├── server.py            # FastMCP entrypoint — registers all tool modules
│   ├── config.py            # Environment-driven provider configuration (60+ env vars)
│   ├── core/
│   │   ├── gmail_tools.py       # send_followup_email, search_gmail_replies
│   │   ├── leads_tools.py       # fetch_leads, fetch_high_intent_leads, create_or_import_lead, enrich_lead
│   │   ├── crm_tools.py         # update_pipeline_stage, get_campaign_performance
│   │   ├── sheets_tools.py      # fetch_leads (sheets view), update_google_sheet
│   │   └── whatsapp_tools.py    # send_whatsapp_message (Meta Graph API — live)
│   ├── growth/
│   │   ├── google_ads_tools.py  # launch_google_ads_campaign, get_google_ads_performance
│   │   ├── meta_ads_tools.py    # create_retargeting_campaign
│   │   ├── ga4_tools.py         # pull_ga4_conversion_report, get_top_converting_pages
│   │   ├── gsc_tools.py         # get_gsc_keyword_opportunities, get_seo_opportunities
│   │   ├── gtm_tools.py         # validate_gtm_tracking_setup, analyze_gtm_tracking
│   │   ├── contentful_tools.py  # update_contentful_page, optimize_contentful_landing_page
│   │   └── iterable_tools.py    # create_iterable_email_journey, create_iterable_journey
│   ├── infra/
│   │   ├── agent_tools.py       # list_business_agents, get_business_agent, route_agent_task
│   │   ├── agent_api_tools.py   # 30 provider-specific API tools with readiness checks
│   │   ├── triggerdev_tools.py  # trigger_background_workflow, get_background_job_status
│   │   ├── scheduler.py         # schedule_workflow, list_scheduled_workflows
│   │   ├── webhook_handler.py   # list_recent_webhook_events
│   │   └── retry_manager.py     # async_retry decorator with configurable backoff
│   └── utils/
│       ├── helpers.py       # dry_run_response, backend_request, request_json, HMAC verify
│       ├── validators.py    # Pydantic models — LeadInput, EmailPayload, WhatsAppPayload, etc.
│       ├── auth.py          # bearer token helpers, require_configured guard
│       └── logger.py        # structured logging
│
├── backend/
│   ├── api.py               # FastAPI app — leads, drafts, jobs, replies, metrics, delivery
│   ├── storage.py           # LeadStore abstraction — InMemoryLeadStore + SupabaseLeadStore
│   └── config.py            # Settings dataclass — env vars, feature flags, SMTP config
│
├── scrapers/
│   └── multi_source_scraper.py  # Parallel async scraper — YC, Hunter, Apollo, LinkedIn, Clearbit
│
├── frontend/
│   └── src/
│       └── App.jsx          # Operator console — pipeline view, draft approval, job queue, activity log
│
├── migrations/
│   └── 001_initial_schema.sql   # 11 tables, 15 indexes, RLS, audit log — production-grade schema
│
├── tests/
│   ├── test_api.py              # Integration tests — full request lifecycle
│   ├── test_agents_registry.py  # Agent routing and registry tests
│   └── test_mcp_server.py       # MCP tool smoke tests
│
├── config/
│   └── icp_profiles.json        # ICP definitions — B2B SaaS, FinTech, AI startups, and more
│
├── .env.example             # All 60+ environment variables documented
├── docker-compose.yml       # Local dev — backend + frontend
├── Dockerfile               # Production image
└── requirements.txt         # Python dependencies
```

---

## The 30-Agent Registry

Agents are typed dataclasses with missions, MCP tools, handoffs, trigger keywords, and guardrails. Claude inspects the registry at runtime to route tasks.

### Outbound Engine
| Agent | Mission |
|-------|---------|
| Lead Sourcing | Find net-new accounts matching the current ICP |
| Lead Qualification | Score fit, intent, timing, and routing priority |
| Personalization | Create account-specific messaging angles |
| Outreach Execution | Send approved email and WhatsApp outreach |
| Follow-Up Strategy | Choose timing, channel, and sequence variant |
| Meeting Booking | Turn interested replies into booked meetings |
| ICP Refinement | Refine ICP criteria from reply and close rate data |

### Inbound Engine
| Agent | Mission |
|-------|---------|
| Reply Classification | Classify replies — interested, not now, objection, unsubscribe |
| Revenue Friction Detection | Find objections, checkout friction, and handoff failures |
| Churn Prevention | Detect churn risk and trigger retention playbooks |
| Expansion Revenue | Find upsell, renewal, and expansion moments |
| Lifecycle Automation | Build activation, nurture, and retention journeys |

### Growth
| Agent | Mission |
|-------|---------|
| Google Ads Optimization | Analyse spend, keywords, and conversion quality |
| Meta Ads Optimization | Optimise creatives, audiences, and lead quality |
| Retargeting | Build audiences from CRM and website intent |
| Email Campaign Optimization | Improve subject lines, copy, and reply rates |
| GSC SEO Opportunity | Surface keyword gaps and quick-win ranking opportunities |
| Content Performance | Identify which content and offers produce pipeline |
| Channel Performance | Compare channels by CAC, LTV, and pipeline impact |
| Contentful Optimization | Update landing pages for conversion and SEO experiments |
| A/B Testing | Design and evaluate experiments across copy and pages |

### Analytics
| Agent | Mission |
|-------|---------|
| GA4 Intelligence | Explain which channels, pages, and journeys are working |
| GTM Validation | Validate tag, trigger, and conversion measurement integrity |
| Revenue Leak Detection | Detect broken attribution, missing follow-ups, funnel loss |

### Strategy
| Agent | Mission |
|-------|---------|
| GTM Strategy | Plan go-to-market motion across ICP, channel, and offer |
| Founder Decision Report | Summarise what changed and what to decide next |

### Operations
| Agent | Mission |
|-------|---------|
| CRM Update | Keep pipeline stages, records, and sheets clean |
| Trigger.dev Workflow | Create and manage durable background jobs |
| Orchestrator | Route work, sequence multi-agent plans, enforce approvals |
| Agent Loop Learning | Learn from outcomes, recommend system improvements |

Each agent has one canonical external provider in `api_catalog.py` — the tool name, required env vars, and a `side_effect` flag. Run `check_agent_api_readiness()` to see which integrations are live vs missing credentials.

---

## MCP Tool Surface

### Core (sales + CRM)
`send_followup_email` · `search_gmail_replies` · `fetch_leads` · `fetch_high_intent_leads` · `create_or_import_lead` · `enrich_lead` · `update_pipeline_stage` · `get_campaign_performance` · `update_google_sheet` · `send_whatsapp_message`

### Growth (ads + analytics + lifecycle)
`launch_google_ads_campaign` · `get_google_ads_performance` · `create_retargeting_campaign` · `pull_ga4_conversion_report` · `get_top_converting_pages` · `get_gsc_keyword_opportunities` · `get_seo_opportunities` · `validate_gtm_tracking_setup` · `analyze_gtm_tracking` · `update_contentful_page` · `optimize_contentful_landing_page` · `create_iterable_email_journey` · `create_iterable_journey`

### Infrastructure
`trigger_background_workflow` · `trigger_background_sales_workflow` · `get_background_job_status` · `schedule_workflow` · `list_scheduled_workflows` · `list_recent_webhook_events` · `list_business_agents` · `get_business_agent` · `route_agent_task` · `list_agent_engines` · `check_agent_api_readiness`

---

## Safety Model

Every tool that mutates external state — sends emails, spends ad budget, publishes CMS content, syncs audiences — is approval-gated.

**`MCP_DRY_RUN=true` by default.** Claude can exercise every tool with production-shaped payloads without sending real emails, launching ads, or editing Contentful. Set `MCP_DRY_RUN=false` and provide provider credentials to go live.

**`EMAIL_DELIVERY_MODE=dry_run` by default.** Outbound email logs delivery without hitting SMTP. Set to `smtp` with credentials configured for real sends.

**Operator approval gates** sit in the FastAPI layer — every draft requires explicit approval before the send job is queued.

---

## Quick Start

### 1. Setup

```bash
git clone <repo>
cd autonomous-sales-system
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

### 2. Run backend

```bash
python -m uvicorn backend.api:app --reload --port 8000
```

Without `SUPABASE_URL` and `SUPABASE_KEY` set, the backend uses an in-memory store — fully functional for local development and tests.

### 3. Run MCP server

```bash
python -m mcp_server.server
```

Configure Claude Desktop or your MCP client to launch this command from the repo root. The server registers all tools on startup.

### 4. Run frontend

```bash
cd frontend && npm install && npm start
```

Visit `http://localhost:3000` for the operator console.

### 5. Generate leads

```bash
python scrapers/multi_source_scraper.py --limit 20 --sources yc,hunter
```

### 6. Check integration readiness

Ask Claude: `"Which agent API integrations are configured?"` — it will call `check_agent_api_readiness()` and show you exactly what's live vs missing credentials.

---

## Database

PostgreSQL schema with 11 tables, 15+ indexes, Row Level Security, and an audit log. Run against Supabase or any PostgreSQL instance:

```bash
psql $DATABASE_URL < migrations/001_initial_schema.sql
```

Tables: `leads` · `outbound_messages` · `inbound_replies` · `meetings` · `outcomes` · `ab_test_variants` · `variant_performance` · `metrics` · `audit_log`

---

## What's Live vs What's Stubbed

Being explicit about build state:

| Component | Status |
|-----------|--------|
| FastAPI backend — leads, drafts, jobs, delivery | ✅ Live |
| In-memory + Supabase storage | ✅ Live |
| SMTP email delivery | ✅ Live |
| WhatsApp Business API send | ✅ Live |
| MCP server — all tool contracts | ✅ Live |
| Agent registry — 30 agents with routing | ✅ Live |
| Operator console (React) | ✅ Live |
| Multi-source lead scraper | ✅ Live |
| Integration tests | ✅ Live |
| Gmail OAuth transport | 🔧 Stubbed — contract defined, OAuth wiring next |
| Google Sheets OAuth transport | 🔧 Stubbed — contract defined, OAuth wiring next |
| Lead enrichment (Hunter/Apollo/Clearbit) | 🔧 Stubbed — provider priority logic next |
| 30 agent API integrations (Apollo, HubSpot, etc.) | 🔧 Stubbed — env vars mapped, HTTP adapters next |

Stubbed tools return `NotImplementedError` in live mode with a clear message about what needs wiring. All stubbed tools work fully in dry-run mode.

---

## Deployment

### Local

```bash
docker-compose up
```

Starts backend and frontend. Uses in-memory store unless Supabase credentials are set.

### Production

- **Backend** — Railway or Fly.io with `Dockerfile`
- **Frontend** — Vercel
- **Database** — Supabase (run migrations first)
- **MCP server** — same process as backend or separate deployment
- **Background jobs** — Trigger.dev workers

Production checklist:
- Set `MCP_DRY_RUN=false`
- Set `EMAIL_DELIVERY_MODE=smtp` with SMTP credentials
- Set `SECRET_KEY` to enable API auth
- Store all secrets in Railway / Doppler / AWS Secrets Manager
- Set `WEBHOOK_SIGNING_SECRET` for HMAC-validated webhooks

---

## Tests

```bash
pytest tests/
```

Tests use `InMemoryLeadStore` — no database required. Coverage includes full request lifecycle: create lead → generate draft → approve → send → verify outbound message logged.

---

## Extending

Add a new provider integration:

1. Create or edit one module in `mcp_server/core`, `mcp_server/growth`, or `mcp_server/infra`
2. Register it in `mcp_server/server.py`
3. Add the agent-to-provider contract in `agents/api_catalog.py`

Keep tools business-oriented. `get_seo_opportunities` not `query_search_console_rows`. `create_retargeting_campaign` not `post_to_meta_endpoint`. Claude sees business actions — engineers see isolated provider transports.

---

## License

MIT — use freely, modify, deploy, sell.
