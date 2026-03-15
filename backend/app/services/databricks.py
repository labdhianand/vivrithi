from __future__ import annotations

from dataclasses import dataclass

import httpx

from ..config import get_settings
from ..models.case import Case


@dataclass(slots=True)
class DatabricksHealth:
    configured: bool
    reachable: bool
    detail: str


class DatabricksService:
    def __init__(self) -> None:
        self.settings = get_settings()

    def is_configured(self) -> bool:
        return bool(
            self.settings.databricks_host
            and self.settings.databricks_token
            and self.settings.databricks_warehouse_id
        )

    def _base_url(self) -> str:
        host = (self.settings.databricks_host or "").rstrip("/")
        if not host:
            raise RuntimeError("Databricks host is not configured")
        if host.startswith("http://") or host.startswith("https://"):
            return host
        return f"https://{host}"

    def _headers(self) -> dict[str, str]:
        if not self.settings.databricks_token:
            raise RuntimeError("Databricks token is not configured")
        return {
            "Authorization": f"Bearer {self.settings.databricks_token}",
            "Content-Type": "application/json",
        }

    async def healthcheck(self) -> DatabricksHealth:
        if not self.is_configured():
            return DatabricksHealth(
                configured=False,
                reachable=False,
                detail="Databricks host, token, or warehouse ID is not configured.",
            )
        payload = {
            "statement": "SELECT 1 AS ok",
            "warehouse_id": self.settings.databricks_warehouse_id,
            "wait_timeout": f"{int(self.settings.databricks_timeout_seconds)}s",
            "disposition": "INLINE",
        }
        try:
            async with httpx.AsyncClient(timeout=self.settings.databricks_timeout_seconds) as client:
                response = await client.post(
                    f"{self._base_url()}/api/2.0/sql/statements",
                    headers=self._headers(),
                    json=payload,
                )
                response.raise_for_status()
        except Exception as exc:
            return DatabricksHealth(configured=True, reachable=False, detail=str(exc))
        return DatabricksHealth(configured=True, reachable=True, detail="Databricks SQL API reachable.")

    def build_case_query_templates(self, case: Case) -> dict[str, str]:
        cin = case.cin or "<cin>"
        pan = case.pan or "<pan>"
        company_name = (case.company_name or "").replace("'", "''") or "<company_name>"
        return {
            "gst_returns": (
                "SELECT * FROM gst_returns "
                f"WHERE cin = '{cin}' OR pan = '{pan}' "
                "ORDER BY filing_period DESC LIMIT 24"
            ),
            "bank_statements": (
                "SELECT * FROM bank_statements "
                f"WHERE pan = '{pan}' OR entity_name = '{company_name}' "
                "ORDER BY statement_period DESC LIMIT 24"
            ),
            "itr": (
                "SELECT * FROM income_tax_returns "
                f"WHERE pan = '{pan}' OR cin = '{cin}' "
                "ORDER BY assessment_year DESC LIMIT 8"
            ),
        }


_service: DatabricksService | None = None


def get_databricks_service() -> DatabricksService:
    global _service
    if _service is None:
        _service = DatabricksService()
    return _service
