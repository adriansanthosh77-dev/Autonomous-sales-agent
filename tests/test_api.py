from fastapi.testclient import TestClient

from backend.api import app
from backend.storage import InMemoryLeadStore


def build_client() -> TestClient:
    app.state.store = InMemoryLeadStore()
    app.state.jobs = []
    app.state.activities = []
    app.state.drafts = {}
    app.state.job_ids = iter(range(1, 10_000))
    app.state.draft_ids = iter(range(1, 10_000))
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


def test_approve_draft_creates_job() -> None:
    client = build_client()
    lead = client.post(
        "/leads",
        json={"name": "Maya Cruz", "email": "maya@example.com", "company": "Relay", "title": "CEO"},
    ).json()["lead"]
    draft = client.post("/drafts/generate", params={"lead_id": lead["id"]}).json()["draft"]

    approve_response = client.post(f"/drafts/{draft['id']}/approve", json={"approved": True})
    assert approve_response.status_code == 200
    assert approve_response.json()["job"]["type"] == "send_outbound"

    jobs_response = client.get("/jobs")
    assert jobs_response.status_code == 200
    assert len(jobs_response.json()) == 1
    assert jobs_response.json()[0]["status"] in {"simulated", "sent"}

    outbound_response = client.get("/messages/outbound")
    assert outbound_response.status_code == 200
    assert len(outbound_response.json()) == 1


def test_dashboard_summary() -> None:
    client = build_client()
    client.post("/leads", json={"name": "June Park", "email": "june@example.com", "company": "Helio"})
    response = client.get("/dashboard/summary")
    assert response.status_code == 200
    assert response.json()["totals"]["leads"] == 1
    assert "email_delivery_mode" not in response.json()


def test_funnel_metrics() -> None:
    client = build_client()
    response = client.get("/metrics/funnel")
    assert response.status_code == 200
    assert "outreach_sent" in response.json()
