from __future__ import annotations

from dataclasses import dataclass


class MissingProviderConfiguration(RuntimeError):
    """Raised when a live provider call is requested without credentials."""


@dataclass(frozen=True)
class AuthHeader:
    name: str
    value: str


def bearer(token: str | None) -> dict[str, str]:
    if not token:
        return {}
    return {"Authorization": f"Bearer {token}"}


def api_key_header(name: str, token: str | None) -> dict[str, str]:
    if not token:
        return {}
    return {name: token}


def require_configured(provider: str, **values: str | None) -> None:
    missing = [name for name, value in values.items() if not value]
    if missing:
        missing_text = ", ".join(missing)
        raise MissingProviderConfiguration(f"{provider} is missing required configuration: {missing_text}")

