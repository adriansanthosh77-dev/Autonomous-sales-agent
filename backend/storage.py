from __future__ import annotations

from copy import deepcopy
from datetime import datetime
from typing import Any

from supabase import Client


class LeadStore:
    mode = "base"

    def create_lead(self, lead: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError

    def list_leads(self, *, status: str | None = None, limit: int = 50) -> list[dict[str, Any]]:
        raise NotImplementedError

    def get_lead(self, lead_id: int) -> dict[str, Any] | None:
        raise NotImplementedError

    def update_lead(self, lead_id: int, values: dict[str, Any]) -> dict[str, Any] | None:
        raise NotImplementedError

    def create_outcome(self, outcome: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError

    def count_leads_by_status(self, status: str) -> int:
        raise NotImplementedError


class InMemoryLeadStore(LeadStore):
    mode = "memory"

    def __init__(self) -> None:
        self._leads: list[dict[str, Any]] = []
        self._outcomes: list[dict[str, Any]] = []
        self._next_lead_id = 1
        self._next_outcome_id = 1

    def create_lead(self, lead: dict[str, Any]) -> dict[str, Any]:
        now = datetime.utcnow().isoformat()
        record = deepcopy(lead)
        record["id"] = self._next_lead_id
        record.setdefault("created_at", now)
        record.setdefault("updated_at", now)
        self._next_lead_id += 1
        self._leads.append(record)
        return deepcopy(record)

    def list_leads(self, *, status: str | None = None, limit: int = 50) -> list[dict[str, Any]]:
        leads = self._leads
        if status:
            leads = [lead for lead in leads if lead.get("status") == status]
        return deepcopy(leads[:limit])

    def get_lead(self, lead_id: int) -> dict[str, Any] | None:
        for lead in self._leads:
            if lead["id"] == lead_id:
                return deepcopy(lead)
        return None

    def update_lead(self, lead_id: int, values: dict[str, Any]) -> dict[str, Any] | None:
        for index, lead in enumerate(self._leads):
            if lead["id"] == lead_id:
                updated = deepcopy(lead)
                updated.update(values)
                updated["updated_at"] = datetime.utcnow().isoformat()
                self._leads[index] = updated
                return deepcopy(updated)
        return None

    def create_outcome(self, outcome: dict[str, Any]) -> dict[str, Any]:
        record = deepcopy(outcome)
        record["id"] = self._next_outcome_id
        self._next_outcome_id += 1
        self._outcomes.append(record)
        return deepcopy(record)

    def count_leads_by_status(self, status: str) -> int:
        return sum(1 for lead in self._leads if lead.get("status") == status)


class SupabaseLeadStore(LeadStore):
    mode = "supabase"

    def __init__(self, client: Client) -> None:
        self.client = client

    def create_lead(self, lead: dict[str, Any]) -> dict[str, Any]:
        return self.client.table("leads").insert(lead).execute().data[0]

    def list_leads(self, *, status: str | None = None, limit: int = 50) -> list[dict[str, Any]]:
        query = self.client.table("leads").select("*").limit(limit)
        if status:
            query = query.eq("status", status)
        return query.execute().data

    def get_lead(self, lead_id: int) -> dict[str, Any] | None:
        response = self.client.table("leads").select("*").eq("id", lead_id).limit(1).execute()
        return response.data[0] if response.data else None

    def update_lead(self, lead_id: int, values: dict[str, Any]) -> dict[str, Any] | None:
        response = self.client.table("leads").update(values).eq("id", lead_id).execute()
        return response.data[0] if response.data else self.get_lead(lead_id)

    def create_outcome(self, outcome: dict[str, Any]) -> dict[str, Any]:
        return self.client.table("outcomes").insert(outcome).execute().data[0]

    def count_leads_by_status(self, status: str) -> int:
        response = self.client.table("leads").select("id", count="exact").eq("status", status).execute()
        return response.count or 0
