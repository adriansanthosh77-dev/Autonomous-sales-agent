from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import FastMCP

from mcp_server.config import MCPSettings, get_settings
from mcp_server.core import crm_tools, gmail_tools, leads_tools, sheets_tools, whatsapp_tools
from mcp_server.growth import (
    contentful_tools,
    ga4_tools,
    google_ads_tools,
    gsc_tools,
    gtm_tools,
    iterable_tools,
    meta_ads_tools,
)
from mcp_server.infra import agent_api_tools, agent_tools, scheduler, triggerdev_tools, webhook_handler
from mcp_server.utils.logger import configure_logging


def build_mcp_server(settings: MCPSettings | None = None) -> FastMCP:
    settings = settings or get_settings()
    configure_logging(settings.debug)
    mcp = FastMCP(settings.service_name)

    modules: list[Any] = [
        gmail_tools,
        sheets_tools,
        whatsapp_tools,
        leads_tools,
        crm_tools,
        google_ads_tools,
        meta_ads_tools,
        ga4_tools,
        gsc_tools,
        gtm_tools,
        contentful_tools,
        iterable_tools,
        agent_tools,
        agent_api_tools,
        triggerdev_tools,
        webhook_handler,
        scheduler,
    ]
    for module in modules:
        module.register(mcp, settings)

    return mcp


mcp = build_mcp_server()


if __name__ == "__main__":
    mcp.run()
