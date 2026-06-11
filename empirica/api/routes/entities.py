"""Entity mint endpoint — daemon HTTP surface over the workspace entity registry.

POST /api/v1/entities mints a contact into workspace.db entity_registry,
idempotently: re-creating with the same identity (email first, then the
deterministic name/company slug) returns the existing entity_id with
created=false. The returned id is the canonical contact_id that external
consumers (e.g. a CRM MCP server on the same box) carry as their FK and
that the knowledge-graph traversal resolves.

The daemon binds localhost-only; no bearer auth is enforced (consistent
with the other /api/v1 routes — transport security is the loopback
boundary).
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api/v1", tags=["entities"])


class EntityCreateRequest(BaseModel):
    type: str = Field(description="Entity type — v1 mints contacts only")
    name: str = Field(min_length=1, description="Contact display name")
    email: str | None = None
    phone: str | None = None
    role: str | None = None
    company_name: str | None = None
    description: str | None = None
    metadata: dict | None = Field(
        default=None, description="Extra metadata merged into the registry row",
    )


@router.post("/entities")
async def create_entity(req: EntityCreateRequest):
    """Idempotent contact mint. Returns the canonical entity_id.

    Response: ``{ok, entity_id, created, matched_by}`` — ``created`` is
    false when the identity resolved to an existing row (verified no-op).
    """
    if req.type != "contact":
        raise HTTPException(
            status_code=422,
            detail=f"entity create v1 mints contacts only (got {req.type!r}). "
                   "Other entity types are written by their owning pipelines.",
        )

    from empirica.cli.command_handlers.entity_commands import mint_contact

    result = mint_contact(
        name=req.name,
        email=req.email,
        phone=req.phone,
        role=req.role,
        company_name=req.company_name,
        description=req.description,
        extra_metadata=req.metadata,
    )
    if not result.get("ok"):
        raise HTTPException(status_code=400, detail=result.get("error", "mint failed"))
    return result
