from __future__ import annotations

from pydantic import BaseModel


class DatabricksStatusRead(BaseModel):
    configured: bool
    reachable: bool
    host: str | None = None
    warehouse_id: str | None = None
    detail: str


class DatabricksCasePreviewRead(BaseModel):
    case_id: str
    configured: bool
    query_templates: dict[str, str]
