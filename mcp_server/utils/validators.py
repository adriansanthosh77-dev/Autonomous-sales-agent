from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class LeadInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    name: str = Field(min_length=1)
    email: EmailStr
    company: str = Field(min_length=1)
    title: str | None = None
    phone: str | None = None
    website: str | None = None
    industry: str | None = None
    source: str = "mcp"
    status: str = "pending"


class EmailPayload(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    to_email: EmailStr
    subject: str = Field(min_length=1)
    body: str = Field(min_length=1)
    lead_id: int | None = None
    campaign_id: str | None = None


class WhatsAppPayload(BaseModel):
    to_phone: str = Field(min_length=6)
    message: str = Field(min_length=1, max_length=4096)
    lead_id: int | None = None
    template_name: str | None = None


class PipelineStageUpdate(BaseModel):
    lead_id: int = Field(gt=0)
    stage: Literal[
        "pending",
        "outreach_sent",
        "replied_interested",
        "replied_not_now",
        "qualified",
        "booked",
        "closed_won",
        "closed_lost",
    ]
    notes: str | None = None


class CampaignBudget(BaseModel):
    daily_budget: float = Field(gt=0)
    currency: str = Field(default="USD", min_length=3, max_length=3)


def compact_payload(payload: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in payload.items() if value is not None}

