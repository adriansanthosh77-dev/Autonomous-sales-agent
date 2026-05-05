from agents.registry import ENGINES, get_agent, list_agents, route_task
from agents.api_catalog import list_agent_api_specs


def test_agent_registry_has_expected_count() -> None:
    assert len(list_agents()) == 30
    assert set(ENGINES) == {"outbound_engine", "inbound_engine"}


def test_can_get_outreach_agent() -> None:
    agent = get_agent("outreach_execution")
    assert agent["name"] == "Outreach Execution Agent"
    assert "send_followup_email" in agent["primary_tools"]
    assert agent["api_tools"] == ("send_sendgrid_outbound_email",)


def test_routes_google_ads_task() -> None:
    route = route_task("optimize google ads cost per lead from paid search")
    assert route["agent"]["slug"] == "google_ads_optimization"
    assert route["confidence"] > 0.5


def test_agent_api_catalog_has_one_api_per_agent() -> None:
    specs = list_agent_api_specs()
    assert len(specs) == 30
    assert {spec["agent_slug"] for spec in specs} == {agent["slug"] for agent in list_agents()}
