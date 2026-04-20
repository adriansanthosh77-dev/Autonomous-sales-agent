"""
FastAPI Backend - Autonomous Sales System
==========================================
Main server handling all agents, integrations, and business logic.

Start: python -m uvicorn backend.api:app --reload --port 8000
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timedelta
import os
import json
import logging
from dotenv import load_dotenv

# Integrations
from anthropic import Anthropic
from supabase import create_client, Client
import aiohttp

load_dotenv()

# ─────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────

CLAUDE_API_KEY = os.getenv("CLAUDE_API_KEY")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
claude_client = Anthropic(api_key=CLAUDE_API_KEY)

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────
# PYDANTIC MODELS
# ─────────────────────────────────────────────

class Lead(BaseModel):
    name: str
    email: str
    phone: Optional[str] = None
    company: str
    website: Optional[str] = None
    title: Optional[str] = None
    industry: Optional[str] = None
    source: str = "manual"
    status: str = "pending"

class OutboundDraft(BaseModel):
    lead_id: int
    email_subject: str
    email_body: str
    whatsapp: str
    confidence_score: float
    channel: str

class EmailReply(BaseModel):
    lead_id: int
    from_email: str
    subject: str
    body: str
    received_at: datetime
    sentiment: Optional[str] = None

class LeadOutcome(BaseModel):
    lead_id: int
    status: str
    deal_size: Optional[float] = None
    notes: str

# ─────────────────────────────────────────────
# FASTAPI APP
# ─────────────────────────────────────────────

app = FastAPI(
    title="Autonomous Sales System API",
    description="AI-powered GTM automation",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─────────────────────────────────────────────
# DRAFT GENERATION (with caching)
# ─────────────────────────────────────────────

_draft_cache = {}  # In production: use Redis

async def generate_draft(lead: dict) -> OutboundDraft:
    """Generate email/WhatsApp draft with caching."""
    
    cache_key = f"{lead.get('title', '')}_{lead.get('industry', '')}"
    
    # Check cache (80-90% hit rate)
    if cache_key in _draft_cache:
        template = _draft_cache[cache_key]
        email_body = template["email_body"].replace("[NAME]", lead["name"]).replace("[COMPANY]", lead["company"])
        whatsapp = template["whatsapp"].replace("[NAME]", lead["name"]).replace("[COMPANY]", lead["company"])
        return OutboundDraft(
            lead_id=lead.get("id", 0),
            email_subject=template["email_subject"],
            email_body=email_body,
            whatsapp=whatsapp,
            confidence_score=8.5,
            channel="email"
        )
    
    # Generate new draft
    system_prompt = """You are an expert outbound sales copywriter.
    Write conversational, friendly messages. Never sound like a bot.
    Emails: <120 words. WhatsApp: <60 words.
    Use [NAME] and [COMPANY] for personalization.
    Respond ONLY with valid JSON."""
    
    user_prompt = f"""Write outbound messages for:
    Name: {lead.get('name')}
    Title: {lead.get('title')}
    Company: {lead.get('company')}
    Industry: {lead.get('industry')}
    
    Return ONLY:
    {{"email_subject": "...", "email_body": "...", "whatsapp": "..."}}"""
    
    try:
        response = claude_client.messages.create(
            model="claude-opus-4-20250805",
            max_tokens=500,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}]
        )
        
        text = response.content[0].text.replace("```json", "").replace("```", "").strip()
        data = json.loads(text)
        
        # Cache the template
        _draft_cache[cache_key] = data
        
        # Personalize
        email_body = data["email_body"].replace("[NAME]", lead.get("name", "")).replace("[COMPANY]", lead.get("company", ""))
        whatsapp = data["whatsapp"].replace("[NAME]", lead.get("name", "")).replace("[COMPANY]", lead.get("company", ""))
        
        return OutboundDraft(
            lead_id=lead.get("id", 0),
            email_subject=data["email_subject"],
            email_body=email_body,
            whatsapp=whatsapp,
            confidence_score=7.5,
            channel="email"
        )
    except Exception as e:
        logger.error(f"Draft generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ─────────────────────────────────────────────
# REPLY CLASSIFICATION
# ─────────────────────────────────────────────

async def classify_reply(reply: EmailReply) -> dict:
    """Classify email reply sentiment."""
    
    system_prompt = """Analyze email sentiment.
    Return JSON: {"sentiment": "interested|not_now|objection|spam", "confidence": 0-1, "key_points": ["..."], "suggested_response": "..."}"""
    
    user_prompt = f"""Classify this reply:
    From: {reply.from_email}
    Subject: {reply.subject}
    Body: {reply.body}"""
    
    try:
        response = claude_client.messages.create(
            model="claude-opus-4-20250805",
            max_tokens=300,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}]
        )
        
        text = response.content[0].text.replace("```json", "").replace("```", "").strip()
        data = json.loads(text)
        
        # Update lead status
        new_status = "replied_interested" if data["sentiment"] == "interested" else f"replied_{data['sentiment']}"
        supabase.table("leads").update({
            "status": new_status,
            "last_reply_sentiment": data["sentiment"],
            "last_reply_at": datetime.utcnow().isoformat()
        }).eq("id", reply.lead_id).execute()
        
        return data
    except Exception as e:
        logger.error(f"Classification failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ─────────────────────────────────────────────
# LEAD SCORING
# ─────────────────────────────────────────────

async def score_lead(lead: dict) -> float:
    """Score lead 0-10 based on engagement."""
    
    score = 5.0  # Base score
    
    # Engagement signals
    if lead.get("last_reply_sentiment") == "interested":
        score += 3.0
    elif lead.get("last_reply_sentiment") == "not_now":
        score -= 1.0
    
    # Activity recency (within 24h = +2)
    if lead.get("last_reply_at"):
        delta = datetime.utcnow() - datetime.fromisoformat(lead["last_reply_at"])
        if delta < timedelta(hours=24):
            score += 2.0
    
    # Replies received (+1)
    if lead.get("status", "").startswith("replied"):
        score += 1.0
    
    # Return bounded score
    return max(0, min(10, score))

# ─────────────────────────────────────────────
# ENDPOINTS
# ─────────────────────────────────────────────

@app.get("/health")
async def health():
    """Health check."""
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}

# ─────────────────────────────────────────────
# LEAD ENDPOINTS
# ─────────────────────────────────────────────

@app.post("/leads")
async def create_lead(lead: Lead):
    """Create a new lead."""
    try:
        response = supabase.table("leads").insert(lead.dict()).execute()
        return {"status": "success", "id": response.data[0]["id"]}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/leads")
async def list_leads(status: Optional[str] = None, limit: int = 50):
    """Get leads."""
    try:
        query = supabase.table("leads").select("*").limit(limit)
        if status:
            query = query.eq("status", status)
        response = query.execute()
        return response.data
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/leads/hot")
async def get_hot_leads(limit: int = 20):
    """Get hot leads (qualified)."""
    try:
        response = supabase.table("leads").select("*").eq("status", "qualified").limit(limit).execute()
        return response.data
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/leads/{lead_id}/import")
async def import_leads_csv(file: UploadFile = File(...)):
    """Bulk import leads from CSV."""
    import csv
    try:
        contents = await file.read()
        lines = contents.decode().split('\n')
        reader = csv.DictReader(lines)
        
        leads = []
        for row in reader:
            if row.get('email'):
                leads.append({
                    "name": row.get('name', ''),
                    "email": row.get('email'),
                    "company": row.get('company', ''),
                    "title": row.get('title', ''),
                    "industry": row.get('industry', ''),
                    "source": "csv_import"
                })
        
        supabase.table("leads").insert(leads).execute()
        return {"status": "imported", "count": len(leads)}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# ─────────────────────────────────────────────
# DRAFT ENDPOINTS
# ─────────────────────────────────────────────

@app.post("/drafts/generate")
async def generate_draft_endpoint(lead_id: int):
    """Generate draft for a lead."""
    try:
        # Get lead
        response = supabase.table("leads").select("*").eq("id", lead_id).execute()
        if not response.data:
            raise HTTPException(status_code=404, detail="Lead not found")
        
        lead = response.data[0]
        draft = await generate_draft(lead)
        
        # Auto-approve if high confidence
        if draft.confidence_score > 8.0:
            return {"draft": draft.dict(), "auto_approved": True}
        
        return {"draft": draft.dict(), "awaiting_approval": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/drafts/{draft_id}/approve")
async def approve_draft(draft_id: int, approved: bool, background_tasks: BackgroundTasks):
    """Approve or reject a draft."""
    if approved:
        # Queue for sending (TODO: Gmail integration)
        background_tasks.add_task(send_email_stub, draft_id)
        return {"status": "approved"}
    else:
        return {"status": "rejected"}

async def send_email_stub(draft_id: int):
    """Stub for sending email (TODO: integrate Gmail API)."""
    logger.info(f"Sending draft {draft_id}")
    # TODO: Implement Gmail API send

# ─────────────────────────────────────────────
# REPLY ENDPOINTS
# ─────────────────────────────────────────────

@app.post("/replies/classify")
async def classify_reply_endpoint(reply: EmailReply):
    """Classify an incoming reply."""
    try:
        result = await classify_reply(reply)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/replies")
async def list_replies(limit: int = 20):
    """Get recent replies."""
    try:
        response = supabase.table("leads").select("*").eq("status", "replied").limit(limit).execute()
        return response.data
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# ─────────────────────────────────────────────
# SCORING ENDPOINTS
# ─────────────────────────────────────────────

@app.post("/leads/{lead_id}/score")
async def score_lead_endpoint(lead_id: int):
    """Score a lead."""
    try:
        response = supabase.table("leads").select("*").eq("id", lead_id).execute()
        if not response.data:
            raise HTTPException(status_code=404, detail="Lead not found")
        
        lead = response.data[0]
        score = await score_lead(lead)
        
        # Update lead
        supabase.table("leads").update({
            "qualification_score": score,
            "status": "qualified" if score > 7 else "pending"
        }).eq("id", lead_id).execute()
        
        return {"lead_id": lead_id, "score": score, "status": "qualified" if score > 7 else "pending"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ─────────────────────────────────────────────
# OUTCOME ENDPOINTS
# ─────────────────────────────────────────────

@app.post("/outcomes")
async def log_outcome(outcome: LeadOutcome):
    """Log deal outcome."""
    try:
        supabase.table("leads").update({
            "status": f"closed_{outcome.status}",
            "closed_at": datetime.utcnow().isoformat()
        }).eq("id", outcome.lead_id).execute()
        
        supabase.table("outcomes").insert({
            "lead_id": outcome.lead_id,
            "status": outcome.status,
            "deal_size": outcome.deal_size,
            "notes": outcome.notes,
            "timestamp": datetime.utcnow().isoformat()
        }).execute()
        
        return {"status": "logged"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ─────────────────────────────────────────────
# METRICS ENDPOINTS
# ─────────────────────────────────────────────

@app.get("/metrics/funnel")
async def get_funnel_metrics():
    """Get conversion funnel."""
    try:
        statuses = ["outreach_sent", "replied_interested", "qualified", "booked", "closed_won"]
        funnel = {}
        
        for status in statuses:
            response = supabase.table("leads").select("id", count="exact").eq("status", status).execute()
            funnel[status] = response.count or 0
        
        return funnel
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/metrics/conversion")
async def get_conversion_rates():
    """Get conversion rates by stage."""
    try:
        metrics = await get_funnel_metrics()
        
        total = sum(metrics.values()) or 1
        reply_rate = (metrics.get("replied_interested", 0) / (metrics.get("outreach_sent", 0) or 1)) * 100
        qualify_rate = (metrics.get("qualified", 0) / (metrics.get("replied_interested", 0) or 1)) * 100
        close_rate = (metrics.get("closed_won", 0) / (metrics.get("booked", 0) or 1)) * 100
        
        return {
            "reply_rate": round(reply_rate, 2),
            "qualify_rate": round(qualify_rate, 2),
            "close_rate": round(close_rate, 2),
            "total_leads": total
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ─────────────────────────────────────────────
# RUN
# ─────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
