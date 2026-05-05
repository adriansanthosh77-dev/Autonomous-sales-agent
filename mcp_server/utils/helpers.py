from __future__ import annotations

import hashlib
import hmac
from datetime import datetime, timezone
from typing import Any

import aiohttp

from mcp_server.config import MCPSettings
from mcp_server.utils.auth import bearer


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def dry_run_response(action: str, payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "status": "dry_run",
        "action": action,
        "executed": False,
        "timestamp": utc_now_iso(),
        "payload": payload,
    }


def verify_hmac_signature(secret: str, body: bytes, signature: str) -> bool:
    expected = hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()
    provided = signature.replace("sha256=", "")
    return hmac.compare_digest(expected, provided)


async def request_json(
    method: str,
    url: str,
    *,
    settings: MCPSettings,
    headers: dict[str, str] | None = None,
    json: dict[str, Any] | None = None,
    params: dict[str, Any] | None = None,
) -> dict[str, Any]:
    timeout = aiohttp.ClientTimeout(total=settings.request_timeout_seconds)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        async with session.request(method, url, headers=headers, json=json, params=params) as response:
            text = await response.text()
            if response.status >= 400:
                raise RuntimeError(f"{method} {url} failed with {response.status}: {text[:500]}")
            if not text:
                return {}
            return await response.json()


async def backend_request(
    method: str,
    path: str,
    *,
    settings: MCPSettings,
    json: dict[str, Any] | None = None,
    params: dict[str, Any] | None = None,
) -> dict[str, Any] | list[dict[str, Any]]:
    headers = bearer(settings.backend_api_key)
    if settings.backend_api_key:
        headers["x-api-key"] = settings.backend_api_key
    url = f"{settings.backend_api_url.rstrip('/')}/{path.lstrip('/')}"
    return await request_json(method, url, settings=settings, headers=headers, json=json, params=params)

