from fastapi.testclient import TestClient

from backend.api import app
from backend.storage import InMemoryLeadStore


def build_client() -> TestClient:
    app.state.store = InMemoryLeadStore()
    if hasattr(app.state, "anthropic_client"):
        delattr(app.state, "anthropic_client")
    return TestClient(app)


def test_health() -> None:
    client = build_client()
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
    assert response.json()["storage_mode"] == "memory"


def test_create_and_list_leads() -> None:
    client = build_client()
    payload = {
        "name": "Ava Patel",
        "email": "ava@example.com",
        "company": "Orbit Labs",
        "title": "Founder",
        "industry": "SaaS",
    }
    create_response = client.post("/leads", json=payload)
    assert create_response.status_code == 200
    assert create_response.json()["lead"]["email"] == payload["email"]

    list_response = client.get("/leads")
    assert list_response.status_code == 200
    assert len(list_response.json()) == 1


def test_generate_draft_and_classify_reply() -> None:
    client = build_client()
    lead = client.post(
        "/leads",
        json={"name": "Sam Lee", "email": "sam@example.com", "company": "Northstar", "title": "CEO"},
    ).json()["lead"]

    draft_response = client.post("/drafts/generate", params={"lead_id": lead["id"]})
    assert draft_response.status_code == 200
    assert "draft" in draft_response.json()

    reply_response = client.post(
        "/replies/classify",
        json={
            "lead_id": lead["id"],
            "from_email": "sam@example.com",
            "subject": "Interested",
            "body": "This sounds good. Let's talk next week.",
            "received_at": "2026-04-26T10:00:00",
        },
    )
    assert reply_response.status_code == 200
    assert reply_response.json()["sentiment"] == "interested"


def test_funnel_metrics() -> None:
    client = build_client()
    response = client.get("/metrics/funnel")
    assert response.status_code == 200
    assert "outreach_sent" in response.json()
