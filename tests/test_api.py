"""
Basic tests for the autonomous sales system
Run with: pytest
"""

import pytest
from fastapi.testclient import TestClient
from backend.api import app

client = TestClient(app)

def test_health():
    """Test health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_list_leads_empty():
    """Test listing leads when empty"""
    response = client.get("/leads")
    assert response.status_code == 200

def test_funnel_metrics():
    """Test funnel metrics endpoint"""
    response = client.get("/metrics/funnel")
    assert response.status_code == 200
    data = response.json()
    assert "outreach_sent" in data

# TODO: Add more tests for:
# - Lead creation
# - Draft generation
# - Reply classification
# - Lead scoring
# - Outcome logging
