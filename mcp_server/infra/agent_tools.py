from typing import Any

from agents.registry import ENGINES, get_agent, list_agents, route_task
from mcp_server.config import MCPSettings


def register(mcp: Any, settings: MCPSettings) -> None:
    @mcp.tool()
    async def list_business_agents(category: str | None = None, engine: str | None = None) -> list[dict[str, Any]]:
        """List the business agents Claude can route work to."""
        return list_agents(category=category, engine=engine)

    @mcp.tool()
    async def get_business_agent(agent_slug: str) -> dict[str, Any]:
        """Inspect one agent's mission, tool permissions, handoffs, and guardrails."""
        return get_agent(agent_slug)

    @mcp.tool()
    async def route_agent_task(task: str) -> dict[str, Any]:
        """Choose the best agent for a natural-language task."""
        return route_task(task)

    @mcp.tool()
    async def list_agent_engines() -> dict[str, dict[str, Any]]:
        """List high-level engines such as inbound and outbound."""
        return ENGINES
