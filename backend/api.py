from __future__ import annotations

import csv
import io
import json
import logging
from datetime import datetime, timedelta
from typing import Any

from anthropic import Anthropic
from fastapi import BackgroundTasks, FastAPI, File, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ConfigDict, EmailStr, Field
from supabase import create_client

from backend.config import settings
from backend.storage import InMemoryLeadStore, LeadStore, SupabaseLeadStore

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Lead(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    name: str = Field(min_length=1)
    email: EmailStr
    company: str = Field(min_length=1)
    phone: str | None = None
    website: str | None = None
    title: str | None = None
    industry: str | None = None
    source: str = "manual"
    status: str = "pending"


class OutboundDraft(BaseModel):
    lead_id: int
    email_subject: str
    email_body: str
    whatsapp: str
    confidence_score: float
    channel: str = "email"


class EmailReply(BaseModel):
    lead_id: int
    from_email: EmailStr
    subject: str
    body: str
    received_at: datetime


class LeadOutcome(BaseModel):
    lead_id: int
    status: str
    notes: str = Field(min_length=1)
    deal_size: float | None = None


app = FastAPI(
    title="Autonomous Sales System API",
    description="Production-oriented API for autonomous sales workflows",
    version="1.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

_draft_cache: dict[str, dict[str, str]] = {}


def get_store() -> LeadStore:
    store = getattr(app.state, "store", None)
    if store is None:
        if settings.has_supabase:
            store = SupabaseLeadStore(create_client(settings.supabase_url, settings.supabase_key))
        else:
            store = InMemoryLeadStore()
        app.state.store = store
    return store


def get_anthropic_client() -> Anthropic | None:
    client = getattr(app.state, "anthropic_client", None)
    if client is None and settings.has_anthropic:
        client = Anthropic(api_key=settings.claude_api_key)
        app.state.anthropic_client = client
    return client


def build_fallback_draft(lead: dict[str, Any]) -> dict[str, str]:
    first_name = lead.get("name", "there").split()[0]
    company = lead.get("company", "your team")
    title = lead.get("title") or "your role"
    return {
        "email_subject": f"Idea for {company}'s pipeline",
        "email_body": (
            f"Hi {first_name},\n\n"
            f"I noticed your work as {title} at {company}. We help teams save time on outbound prospecting and follow-up.\n\n"
            "If useful, I can share a short breakdown of how teams automate lead research and first-touch drafting without losing personalization.\n\n"
            "Would a quick look be helpful?"
        ),
        "whatsapp": (
            f"Hi {first_name}, quick idea for helping {company} automate lead follow-up "
            "without sounding robotic. Worth sending details?"
        ),
    }


async def generate_draft(lead: dict[str, Any]) -> OutboundDraft:
    cache_key = f"{lead.get('title', '')}:{lead.get('industry', '')}:{lead.get('source', '')}"
    if cache_key in _draft_cache:
        template = _draft_cache[cache_key]
        return OutboundDraft(
            lead_id=lead.get("id", 0),
            email_subject=template["email_subject"],
            email_body=template["email_body"].replace("[NAME]", lead.get("name", "")).replace("[COMPANY]", lead.get("company", "")),
            whatsapp=template["whatsapp"].replace("[NAME]", lead.get("name", "")).replace("[COMPANY]", lead.get("company", "")),
            confidence_score=8.2,
        )

    client = get_anthropic_client()
    if client is None:
        template = build_fallback_draft(lead)
    else:
        response = client.messages.create(
            model="claude-3-5-sonnet-latest",
            max_tokens=300,
            system=(
                "You write concise B2B outbound copy. "
                "Return valid JSON with email_subject, email_body, whatsapp. "
                "Use [NAME] and [COMPANY] as placeholders."
            ),
            messages=[
                {
                    "role": "user",
                    "content": (
                        f"Name: {lead.get('name')}\n"
                        f"Title: {lead.get('title')}\n"
                        f"Company: {lead.get('company')}\n"
                        f"Industry: {lead.get('industry')}"
                    ),
                }
            ],
        )
        text = response.content[0].text.replace("```json", "").replace("```", "").strip()
        template = json.loads(text)

    normalized_template = {
        "email_subject": template["email_subject"],
        "email_body": template["email_body"].replace(lead.get("name", ""), "[NAME]").replace(lead.get("company", ""), "[COMPANY]"),
        "whatsapp": template["whatsapp"].replace(lead.get("name", ""), "[NAME]").replace(lead.get("company", ""), "[COMPANY]"),
    }
    _draft_cache[cache_key] = normalized_template

    return OutboundDraft(
        lead_id=lead.get("id", 0),
        email_subject=template["email_subject"],
        email_body=template["email_body"],
        whatsapp=template["whatsapp"],
        confidence_score=7.8 if client else 6.5,
    )


async def classify_reply(reply: EmailReply) -> dict[str, Any]:
    body = reply.body.lower()
    sentiment = "objection"
    confidence = 0.65
    suggested_response = "Acknowledge the concern and ask one clarifying question."

    if any(token in body for token in ["interested", "sounds good", "let's talk", "book", "meeting"]):
        sentiment = "interested"
        confidence = 0.9
        suggested_response = "Offer two concrete meeting times and include a booking link."
    elif any(token in body for token in ["later", "next quarter", "not now"]):
        sentiment = "not_now"
        confidence = 0.84
        suggested_response = "Thank them, ask for timing, and schedule a lighter follow-up."
    elif any(token in body for token in ["unsubscribe", "stop", "remove me"]):
        sentiment = "spam"
        confidence = 0.95
        suggested_response = "Do not follow up again."

    return {
        "sentiment": sentiment,
        "confidence": confidence,
        "key_points": [reply.subject.strip() or "No subject"],
        "suggested_response": suggested_response,
    }


async def score_lead(lead: dict[str, Any]) -> float:
    score = 5.0
    if lead.get("last_reply_sentiment") == "interested":
        score += 3.0
    elif lead.get("last_reply_sentiment") == "not_now":
        score -= 1.0

    last_reply_at = lead.get("last_reply_at")
    if last_reply_at:
        parsed = datetime.fromisoformat(str(last_reply_at).replace("Z", "+00:00"))
        if datetime.utcnow() - parsed.replace(tzinfo=None) < timedelta(hours=24):
            score += 2.0

    if str(lead.get("status", "")).startswith("replied"):
        score += 1.0

    return max(0.0, min(10.0, score))


async def send_email_stub(draft_id: int) -> None:
    logger.info("Queued draft %s for delivery", draft_id)


@app.get("/health")
async def health() -> dict[str, Any]:
    store = get_store()
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "environment": settings.environment,
        "storage_mode": store.mode,
        "anthropic_configured": settings.has_anthropic,
        "supabase_configured": settings.has_supabase,
    }


@app.post("/leads")
async def create_lead(lead: Lead) -> dict[str, Any]:
    record = get_store().create_lead(lead.model_dump())
    return {"status": "success", "id": record["id"], "lead": record}


@app.get("/leads")
async def list_leads(status: str | None = None, limit: int = Query(default=50, ge=1, le=500)) -> list[dict[str, Any]]:
    return get_store().list_leads(status=status, limit=limit)


@app.get("/leads/hot")
async def get_hot_leads(limit: int = Query(default=20, ge=1, le=100)) -> list[dict[str, Any]]:
    return get_store().list_leads(status="qualified", limit=limit)


@app.post("/leads/import")
async def import_leads_csv(file: UploadFile = File(...)) -> dict[str, Any]:
    contents = await file.read()
    reader = csv.DictReader(io.StringIO(contents.decode()))
    imported = 0
    for row in reader:
        if not row.get("email"):
            continue
        lead = Lead(
            name=row.get("name") or "Unknown",
            email=row["email"],
            company=row.get("company") or "Unknown",
            title=row.get("title"),
            industry=row.get("industry"),
            source="csv_import",
        )
        get_store().create_lead(lead.model_dump())
        imported += 1
    return {"status": "imported", "count": imported}


@app.post("/drafts/generate")
async def generate_draft_endpoint(lead_id: int) -> dict[str, Any]:
    lead = get_store().get_lead(lead_id)
    if lead is None:
        raise HTTPException(status_code=404, detail="Lead not found")

    draft = await generate_draft(lead)
    return {
        "draft": draft.model_dump(),
        "auto_approved": draft.confidence_score >= 8.0,
        "provider": "anthropic" if settings.has_anthropic else "fallback",
    }


@app.post("/drafts/{draft_id}/approve")
async def approve_draft(draft_id: int, approved: bool, background_tasks: BackgroundTasks) -> dict[str, str]:
    if approved:
        background_tasks.add_task(send_email_stub, draft_id)
        return {"status": "approved"}
    return {"status": "rejected"}


@app.post("/replies/classify")
async def classify_reply_endpoint(reply: EmailReply) -> dict[str, Any]:
    lead = get_store().get_lead(reply.lead_id)
    if lead is None:
        raise HTTPException(status_code=404, detail="Lead not found")

    result = await classify_reply(reply)
    new_status = "replied_interested" if result["sentiment"] == "interested" else f"replied_{result['sentiment']}"
    get_store().update_lead(
        reply.lead_id,
        {
            "status": new_status,
            "last_reply_sentiment": result["sentiment"],
            "last_reply_at": reply.received_at.isoformat(),
        },
    )
    return result


@app.get("/replies")
async def list_replies(limit: int = Query(default=20, ge=1, le=100)) -> list[dict[str, Any]]:
    replied_statuses = ["replied_interested", "replied_not_now", "replied_objection", "replied_spam"]
    results: list[dict[str, Any]] = []
    for status in replied_statuses:
        results.extend(get_store().list_leads(status=status, limit=limit))
    return results[:limit]


@app.post("/leads/{lead_id}/score")
async def score_lead_endpoint(lead_id: int) -> dict[str, Any]:
    lead = get_store().get_lead(lead_id)
    if lead is None:
        raise HTTPException(status_code=404, detail="Lead not found")

    lead_score = await score_lead(lead)
    status = "qualified" if lead_score > 7 else "pending"
    get_store().update_lead(lead_id, {"qualification_score": lead_score, "status": status})
    return {"lead_id": lead_id, "score": lead_score, "status": status}


@app.post("/outcomes")
async def log_outcome(outcome: LeadOutcome) -> dict[str, Any]:
    lead = get_store().get_lead(outcome.lead_id)
    if lead is None:
        raise HTTPException(status_code=404, detail="Lead not found")

    closed_status = f"closed_{outcome.status}"
    get_store().update_lead(outcome.lead_id, {"status": closed_status, "closed_at": datetime.utcnow().isoformat()})
    get_store().create_outcome(
        {
            "lead_id": outcome.lead_id,
            "status": outcome.status,
            "deal_size": outcome.deal_size,
            "notes": outcome.notes,
            "timestamp": datetime.utcnow().isoformat(),
        }
    )
    return {"status": "logged", "lead_id": outcome.lead_id}


@app.get("/metrics/funnel")
async def get_funnel_metrics() -> dict[str, int]:
    statuses = ["outreach_sent", "replied_interested", "qualified", "booked", "closed_won"]
    return {status: get_store().count_leads_by_status(status) for status in statuses}


@app.get("/metrics/conversion")
async def get_conversion_rates() -> dict[str, float]:
    metrics = await get_funnel_metrics()
    total = sum(metrics.values())
    return {
        "reply_rate": round((metrics["replied_interested"] / (metrics["outreach_sent"] or 1)) * 100, 2),
        "qualify_rate": round((metrics["qualified"] / (metrics["replied_interested"] or 1)) * 100, 2),
        "close_rate": round((metrics["closed_won"] / (metrics["booked"] or 1)) * 100, 2),
        "total_leads": total,
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=settings.backend_port)
