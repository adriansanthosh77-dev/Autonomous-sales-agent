from __future__ import annotations

import csv
import io
import json
import logging
from datetime import datetime, timedelta
from itertools import count
from typing import Any

from anthropic import Anthropic
from fastapi import BackgroundTasks, Depends, FastAPI, File, Header, HTTPException, Query, UploadFile
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


class DraftApprovalRequest(BaseModel):
    approved: bool = True


class QueueJobRequest(BaseModel):
    lead_id: int
    send_at: datetime | None = None
    channel: str = "email"
    reason: str = "follow_up"


class OperatorActivity(BaseModel):
    timestamp: str
    type: str
    message: str
    lead_id: int | None = None


class QueuedJob(BaseModel):
    id: int
    type: str
    status: str
    created_at: str
    send_at: str | None = None
    lead_id: int | None = None
    payload: dict[str, Any] = Field(default_factory=dict)


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


def get_runtime_drafts() -> dict[int, dict[str, Any]]:
    drafts = getattr(app.state, "drafts", None)
    if drafts is None:
        drafts = {}
        app.state.drafts = drafts
        app.state.draft_ids = count(1)
    return drafts


def next_draft_id() -> int:
    get_runtime_drafts()
    return next(app.state.draft_ids)


def get_runtime_jobs() -> list[dict[str, Any]]:
    jobs = getattr(app.state, "jobs", None)
    if jobs is None:
        jobs = []
        app.state.jobs = jobs
        app.state.job_ids = count(1)
    return jobs


def next_job_id() -> int:
    get_runtime_jobs()
    return next(app.state.job_ids)


def get_activity_log() -> list[dict[str, Any]]:
    activities = getattr(app.state, "activities", None)
    if activities is None:
        activities = []
        app.state.activities = activities
    return activities


def record_activity(activity_type: str, message: str, lead_id: int | None = None) -> None:
    activity = OperatorActivity(
        timestamp=datetime.utcnow().isoformat(),
        type=activity_type,
        message=message,
        lead_id=lead_id,
    )
    activities = get_activity_log()
    activities.insert(0, activity.model_dump())
    del activities[100:]


def require_operator(x_api_key: str | None = Header(default=None)) -> None:
    if settings.auth_enabled and x_api_key != settings.secret_key:
        raise HTTPException(status_code=401, detail="Invalid API key")


def queue_job(job_type: str, lead_id: int | None, payload: dict[str, Any], send_at: datetime | None = None) -> dict[str, Any]:
    job = QueuedJob(
        id=next_job_id(),
        type=job_type,
        status="queued",
        created_at=datetime.utcnow().isoformat(),
        send_at=send_at.isoformat() if send_at else None,
        lead_id=lead_id,
        payload=payload,
    )
    jobs = get_runtime_jobs()
    jobs.insert(0, job.model_dump())
    record_activity("job_queued", f"Queued {job_type.replace('_', ' ')}", lead_id=lead_id)
    return job.model_dump()


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
        "auth_enabled": settings.auth_enabled,
    }


@app.get("/dashboard/summary")
async def get_dashboard_summary() -> dict[str, Any]:
    leads = get_store().list_leads(limit=500)
    replied = [lead for lead in leads if str(lead.get("status", "")).startswith("replied")]
    qualified = [lead for lead in leads if lead.get("status") == "qualified"]
    jobs = get_runtime_jobs()
    return {
        "totals": {
            "leads": len(leads),
            "replied": len(replied),
            "qualified": len(qualified),
            "jobs_queued": len([job for job in jobs if job.get("status") == "queued"]),
        },
        "conversion": await get_conversion_rates(),
        "recent_activity": get_activity_log()[:8],
    }


@app.post("/leads")
async def create_lead(lead: Lead, _: None = Depends(require_operator)) -> dict[str, Any]:
    record = get_store().create_lead(lead.model_dump())
    record_activity("lead_created", f"Added lead for {record['company']}", lead_id=record["id"])
    return {"status": "success", "id": record["id"], "lead": record}


@app.get("/leads")
async def list_leads(status: str | None = None, limit: int = Query(default=50, ge=1, le=500)) -> list[dict[str, Any]]:
    return get_store().list_leads(status=status, limit=limit)


@app.get("/leads/hot")
async def get_hot_leads(limit: int = Query(default=20, ge=1, le=100)) -> list[dict[str, Any]]:
    return get_store().list_leads(status="qualified", limit=limit)


@app.post("/leads/import")
async def import_leads_csv(file: UploadFile = File(...), _: None = Depends(require_operator)) -> dict[str, Any]:
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
    record_activity("leads_imported", f"Imported {imported} leads from CSV")
    return {"status": "imported", "count": imported}


@app.post("/drafts/generate")
async def generate_draft_endpoint(lead_id: int, _: None = Depends(require_operator)) -> dict[str, Any]:
    lead = get_store().get_lead(lead_id)
    if lead is None:
        raise HTTPException(status_code=404, detail="Lead not found")

    draft = await generate_draft(lead)
    draft_id = next_draft_id()
    runtime_draft = {
        "id": draft_id,
        "lead_id": lead_id,
        "email_subject": draft.email_subject,
        "email_body": draft.email_body,
        "whatsapp": draft.whatsapp,
        "confidence_score": draft.confidence_score,
        "channel": draft.channel,
        "created_at": datetime.utcnow().isoformat(),
        "status": "pending_approval",
    }
    get_runtime_drafts()[draft_id] = runtime_draft
    record_activity("draft_generated", f"Generated draft for {lead['company']}", lead_id=lead_id)
    return {
        "draft": runtime_draft,
        "auto_approved": draft.confidence_score >= 8.0,
        "provider": "anthropic" if settings.has_anthropic else "fallback",
    }


@app.post("/drafts/{draft_id}/approve")
async def approve_draft(
    draft_id: int,
    request: DraftApprovalRequest,
    background_tasks: BackgroundTasks,
    _: None = Depends(require_operator),
) -> dict[str, Any]:
    draft = get_runtime_drafts().get(draft_id)
    if draft is None:
        raise HTTPException(status_code=404, detail="Draft not found")

    if request.approved:
        draft["status"] = "approved"
        background_tasks.add_task(send_email_stub, draft_id)
        job = queue_job("send_outbound", draft["lead_id"], {"draft_id": draft_id, "channel": draft["channel"]})
        get_store().update_lead(draft["lead_id"], {"status": "outreach_sent"})
        record_activity("draft_approved", "Approved outbound draft", lead_id=draft["lead_id"])
        return {"status": "approved", "job": job}

    draft["status"] = "rejected"
    record_activity("draft_rejected", "Rejected outbound draft", lead_id=draft["lead_id"])
    return {"status": "rejected"}


@app.get("/drafts")
async def list_drafts() -> list[dict[str, Any]]:
    drafts = list(get_runtime_drafts().values())
    drafts.sort(key=lambda item: item["id"], reverse=True)
    return drafts[:50]


@app.post("/replies/classify")
async def classify_reply_endpoint(reply: EmailReply, _: None = Depends(require_operator)) -> dict[str, Any]:
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
    record_activity("reply_classified", f"Classified reply as {result['sentiment']}", lead_id=reply.lead_id)
    return result


@app.get("/replies")
async def list_replies(limit: int = Query(default=20, ge=1, le=100)) -> list[dict[str, Any]]:
    replied_statuses = ["replied_interested", "replied_not_now", "replied_objection", "replied_spam"]
    results: list[dict[str, Any]] = []
    for status in replied_statuses:
        results.extend(get_store().list_leads(status=status, limit=limit))
    return results[:limit]


@app.post("/leads/{lead_id}/score")
async def score_lead_endpoint(lead_id: int, _: None = Depends(require_operator)) -> dict[str, Any]:
    lead = get_store().get_lead(lead_id)
    if lead is None:
        raise HTTPException(status_code=404, detail="Lead not found")

    lead_score = await score_lead(lead)
    status = "qualified" if lead_score > 7 else "pending"
    get_store().update_lead(lead_id, {"qualification_score": lead_score, "status": status})
    record_activity("lead_scored", f"Scored lead {lead_score:.1f}", lead_id=lead_id)
    return {"lead_id": lead_id, "score": lead_score, "status": status}


@app.post("/outcomes")
async def log_outcome(outcome: LeadOutcome, _: None = Depends(require_operator)) -> dict[str, Any]:
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
    record_activity("outcome_logged", f"Logged outcome {outcome.status}", lead_id=outcome.lead_id)
    return {"status": "logged", "lead_id": outcome.lead_id}


@app.post("/jobs/follow-ups")
async def queue_follow_up(request: QueueJobRequest, _: None = Depends(require_operator)) -> dict[str, Any]:
    lead = get_store().get_lead(request.lead_id)
    if lead is None:
        raise HTTPException(status_code=404, detail="Lead not found")
    job = queue_job(
        "follow_up",
        request.lead_id,
        {"channel": request.channel, "reason": request.reason},
        send_at=request.send_at,
    )
    return {"status": "queued", "job": job}


@app.get("/jobs")
async def list_jobs() -> list[dict[str, Any]]:
    return get_runtime_jobs()[:100]


@app.get("/activities")
async def list_activities() -> list[dict[str, Any]]:
    return get_activity_log()[:100]


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
