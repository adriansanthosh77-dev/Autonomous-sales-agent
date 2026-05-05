from mcp_server.config import MCPSettings
from mcp_server.server import build_mcp_server


def test_mcp_server_builds_with_dry_run_settings() -> None:
    settings = MCPSettings(dry_run=True)
    server = build_mcp_server(settings)
    assert server is not None
