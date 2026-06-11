"""
Entity Commands — CLI surface for workspace.db entity_registry.

Backs the Practice Model concept (see /empirica-constitution Section XIII):
entities (project, contact, organization, engagement, user) and their
membership edges are queryable without dropping into raw SQL.

Verbs:
- entity-list:   list entities, optionally filtered by type / status
- entity-show:   one entity + its membership edges
- entity-walk:   BFS the membership graph from a starting node
- entity-search: text-search display_name + description
"""

from __future__ import annotations

import json
import sys
from typing import Any

from ...data.repositories.workspace_db import WorkspaceDBRepository
from ..cli_utils import handle_cli_error


def _parse_entity_arg(args) -> tuple[str | None, str | None]:
    """Resolve the entity reference from positional 'type:id' or --type/--id.

    Returns (entity_type, entity_id). Either may be None if absent — the
    caller errors with a useful message.
    """
    et = getattr(args, 'entity_type', None)
    eid = getattr(args, 'entity_id', None)
    positional = getattr(args, 'entity', None)
    if positional and ':' in positional:
        p_type, p_id = positional.split(':', 1)
        et = et or p_type.strip() or None
        eid = eid or p_id.strip() or None
    elif positional and not et and not eid:
        # Treat as id when type/id flags absent — caller error
        eid = positional
    return et, eid


def _format_entity_line(e: dict[str, Any], indent: str = '') -> str:
    short_id = e['entity_id'][:8] if len(e['entity_id']) >= 8 else e['entity_id']
    name = e.get('display_name', '') or '(no name)'
    status = e.get('status', 'active')
    emoji = e.get('emoji_state') or ''
    suffix = f"  [{status}]" if status != 'active' else ''
    return f"{indent}{emoji}{' ' if emoji else ''}{e['entity_type']:13} {short_id}  {name}{suffix}"


def handle_entity_list_command(args):
    """Handle entity-list command."""
    try:
        entity_type = getattr(args, 'type', None)
        status = getattr(args, 'status', 'active')
        limit = getattr(args, 'limit', 100)
        output = getattr(args, 'output', 'human')
        with WorkspaceDBRepository.open() as repo:
            entities = repo.list_entities(entity_type=entity_type, status=status, limit=limit)
        if output == 'json':
            print(json.dumps({
                "ok": True,
                "count": len(entities),
                "entities": entities,
            }, indent=2, default=str))
            return
        if not entities:
            print(f"No entities found (type={entity_type or 'any'}, status={status})")
            return
        print(f"# {len(entities)} entit{'y' if len(entities) == 1 else 'ies'} "
              f"(type={entity_type or 'any'}, status={status})")
        for e in entities:
            print(_format_entity_line(e))
    except Exception as e:
        handle_cli_error(e, "entity-list", getattr(args, 'verbose', False))


def _slugify(text: str) -> str:
    """Lowercase, non-alphanumerics → '-', collapsed and trimmed."""
    out = []
    prev_dash = False
    for ch in text.lower():
        if ch.isalnum():
            out.append(ch)
            prev_dash = False
        elif not prev_dash:
            out.append('-')
            prev_dash = True
    return ''.join(out).strip('-')


def mint_contact(
    name: str,
    email: str | None = None,
    phone: str | None = None,
    role: str | None = None,
    company_name: str | None = None,
    description: str | None = None,
    extra_metadata: dict | None = None,
    repo: WorkspaceDBRepository | None = None,
) -> dict[str, Any]:
    """Idempotent contact mint into workspace.db entity_registry.

    The directly-callable Python API behind `empirica entity-create` —
    consumers on the same box (e.g. a CRM MCP server) can import and call
    this instead of shelling out.

    Identity resolution, in order:
      1. **Email match** — an existing active contact whose metadata.email
         equals the normalized email wins. Email is the strongest identity
         key; the existing row is returned untouched (verified no-op).
      2. **Deterministic slug** — ``c-<name-slug>[-<company-slug>]``,
         matching the registry's existing human-readable convention
         (NOT an opaque hash; the live rows + the EKG traversal +
         extension rendering all use readable ids). Re-minting the same
         identity returns the existing row.
      3. **Collision disambiguation** — same slug but a DIFFERENT email
         on the existing row means a different person: the new id gains
         a deterministic 6-hex suffix derived from the new email/phone.

    Re-calling with the same identity always returns the same entity_id
    with created=False — double-execute is a verified no-op (the mesh
    idempotent-ask convention applied to the mint write).
    """
    import hashlib
    import time

    if not name or not name.strip():
        return {"ok": False, "error": "name is required"}
    name = name.strip()
    norm_email = email.strip().lower() if email else None

    def _resolve(repo: WorkspaceDBRepository) -> dict[str, Any]:
        contacts = repo.list_entities(entity_type='contact', status='active', limit=100000)

        if norm_email:
            for c in contacts:
                try:
                    meta = json.loads(c.get('metadata') or '{}')
                except json.JSONDecodeError:
                    continue
                if (meta.get('email') or '').strip().lower() == norm_email:
                    return {"ok": True, "entity_id": c['entity_id'],
                            "created": False, "matched_by": "email"}

        slug = f"c-{_slugify(name)}"
        if company_name:
            slug += f"-{_slugify(company_name)}"

        entity_id = slug
        existing = next((c for c in contacts if c['entity_id'] == slug), None)
        if existing:
            try:
                existing_email = (json.loads(existing.get('metadata') or '{}')
                                  .get('email') or '').strip().lower()
            except json.JSONDecodeError:
                existing_email = ''
            if norm_email and existing_email and existing_email != norm_email:
                # Same name/company, different person — disambiguate
                # deterministically off the new identity's strongest key.
                key = norm_email or (phone or '').strip()
                suffix = hashlib.sha256(key.encode()).hexdigest()[:6]
                entity_id = f"{slug}-{suffix}"
                if any(c['entity_id'] == entity_id for c in contacts):
                    return {"ok": True, "entity_id": entity_id,
                            "created": False, "matched_by": "slug+suffix"}
            else:
                return {"ok": True, "entity_id": slug,
                        "created": False, "matched_by": "slug"}

        metadata = {k: v for k, v in {
            "email": norm_email, "phone": phone, "role": role,
            "company_name": company_name,
            "minted_at": time.time(), "minted_by": "entity-create",
        }.items() if v is not None}
        if extra_metadata:
            metadata.update(extra_metadata)

        repo.upsert_entity(
            entity_type='contact',
            entity_id=entity_id,
            display_name=name,
            source_db='workspace',
            source_table='contacts',
            description=description,
            metadata=json.dumps(metadata),
        )
        return {"ok": True, "entity_id": entity_id, "created": True,
                "matched_by": None}

    if repo is not None:
        return _resolve(repo)
    with WorkspaceDBRepository.open() as opened:
        return _resolve(opened)


def handle_entity_create_command(args):
    """Handle entity-create command — idempotent contact mint (v1: contacts only)."""
    try:
        output = getattr(args, 'output', 'human')
        entity_type = getattr(args, 'type', 'contact')
        if entity_type != 'contact':
            err = {"ok": False, "error": "unsupported_entity_type",
                   "message": f"entity-create v1 mints contacts only (got {entity_type!r}). "
                              "Other entity types are written by their owning pipelines."}
            print(json.dumps(err, indent=2) if output == 'json'
                  else f"❌ {err['message']}", file=sys.stderr if output != 'json' else sys.stdout)
            sys.exit(1)

        extra = None
        raw_meta = getattr(args, 'metadata', None)
        if raw_meta:
            extra = json.loads(raw_meta)

        result = mint_contact(
            name=getattr(args, 'name', None),
            email=getattr(args, 'email', None),
            phone=getattr(args, 'phone', None),
            role=getattr(args, 'role', None),
            company_name=getattr(args, 'company', None),
            description=getattr(args, 'description', None),
            extra_metadata=extra,
        )
        if output == 'json':
            print(json.dumps(result, indent=2, default=str))
        elif result.get('ok'):
            verb = "created" if result['created'] else f"exists (matched by {result['matched_by']})"
            print(f"👤 Contact {verb}: {result['entity_id']}")
        else:
            print(f"❌ {result.get('error')}", file=sys.stderr)
        sys.exit(0 if result.get('ok') else 1)
    except SystemExit:
        raise
    except Exception as e:
        handle_cli_error(e, "entity-create", getattr(args, 'verbose', False))


def handle_entity_show_command(args):
    """Handle entity-show command."""
    try:
        et, eid = _parse_entity_arg(args)
        output = getattr(args, 'output', 'human')
        if not et or not eid:
            err = {
                "ok": False,
                "error": "entity_reference_required",
                "message": "Pass entity as 'type:id' (e.g. 'project:f73f3708') or use --type + --id",
                "hint": "List available entities: empirica entity-list --type <type> --limit 5",
            }
            if output == 'json':
                print(json.dumps(err, indent=2))
            else:
                print(f"❌ {err['message']}", file=sys.stderr)
                print(f"   {err['hint']}", file=sys.stderr)
            sys.exit(1)
        with WorkspaceDBRepository.open() as repo:
            entity = repo.get_entity(et, eid)
            if not entity:
                err = {
                    "ok": False,
                    "error": "entity_not_found",
                    "message": f"No entity matches {et}:{eid} (full id or unambiguous prefix required)",
                    "hint": f"List candidates: empirica entity-list --type {et}",
                }
                if output == 'json':
                    print(json.dumps(err, indent=2))
                else:
                    print(f"❌ {err['message']}", file=sys.stderr)
                    print(f"   {err['hint']}", file=sys.stderr)
                sys.exit(1)
            memberships = repo.get_entity_memberships(entity['entity_type'], entity['entity_id'])
        if output == 'json':
            print(json.dumps({
                "ok": True,
                "entity": entity,
                "memberships": memberships,
            }, indent=2, default=str))
            return
        print(f"# {entity['entity_type']}:{entity['entity_id']}")
        print(f"  display_name: {entity.get('display_name', '')}")
        if entity.get('description'):
            print(f"  description:  {entity['description']}")
        print(f"  status:       {entity.get('status', 'active')}")
        print(f"  source:       {entity['source_db']}.{entity['source_table']}")
        if memberships['member_of']:
            print(f"\n## member_of ({len(memberships['member_of'])})")
            for m in memberships['member_of']:
                role = f" ({m['role']})" if m.get('role') else ""
                print(f"  → {m['group_type']}:{m['group_id'][:8]}{role}")
        if memberships['members']:
            print(f"\n## members ({len(memberships['members'])})")
            for m in memberships['members']:
                role = f" ({m['role']})" if m.get('role') else ""
                print(f"  ← {m['entity_type']}:{m['entity_id'][:8]}{role}")
        if not memberships['member_of'] and not memberships['members']:
            print("\n  (no membership edges)")
    except Exception as e:
        handle_cli_error(e, "entity-show", getattr(args, 'verbose', False))


def handle_entity_walk_command(args):
    """Handle entity-walk command."""
    try:
        et, eid = _parse_entity_arg(args)
        depth = getattr(args, 'depth', 2)
        output = getattr(args, 'output', 'human')
        if not et or not eid:
            err = {
                "ok": False,
                "error": "entity_reference_required",
                "message": "Pass start entity as 'type:id' or use --type + --id",
                "hint": "List available entities: empirica entity-list --type <type> --limit 5",
            }
            if output == 'json':
                print(json.dumps(err, indent=2))
            else:
                print(f"❌ {err['message']}", file=sys.stderr)
                print(f"   {err['hint']}", file=sys.stderr)
            sys.exit(1)
        with WorkspaceDBRepository.open() as repo:
            result = repo.walk_entity_graph(et, eid, max_depth=depth)
        if result['root'] is None:
            err = {
                "ok": False,
                "error": "entity_not_found",
                "message": f"No entity matches {et}:{eid}",
                "hint": f"List candidates: empirica entity-list --type {et}",
            }
            if output == 'json':
                print(json.dumps(err, indent=2))
            else:
                print(f"❌ {err['message']}", file=sys.stderr)
                print(f"   {err['hint']}", file=sys.stderr)
            sys.exit(1)
        if output == 'json':
            print(json.dumps({
                "ok": True,
                "root": result['root'],
                "nodes": result['nodes'],
                "edges": result['edges'],
                "truncated": result['truncated'],
                "max_depth": depth,
            }, indent=2, default=str))
            return
        root = result['root']
        print(f"# walk from {root['entity_type']}:{root['entity_id'][:8]} "
              f"(depth ≤ {depth}, {len(result['nodes'])} node{'s' if len(result['nodes']) != 1 else ''}, "
              f"{len(result['edges'])} edge{'s' if len(result['edges']) != 1 else ''})")
        # Group nodes by depth for tree-style output
        by_depth: dict[int, list[dict[str, Any]]] = {}
        for n in result['nodes']:
            by_depth.setdefault(n['depth'], []).append(n)
        for d in sorted(by_depth.keys()):
            indent = '  ' * d
            for n in by_depth[d]:
                print(_format_entity_line(n, indent=indent))
        if result['truncated']:
            print(f"\n  ⚠ Walk truncated at depth {depth} (more edges beyond)")
    except Exception as e:
        handle_cli_error(e, "entity-walk", getattr(args, 'verbose', False))


def handle_entity_search_command(args):
    """Handle entity-search command."""
    try:
        query = args.query
        entity_type = getattr(args, 'type', None)
        status = getattr(args, 'status', 'active')
        limit = getattr(args, 'limit', 50)
        output = getattr(args, 'output', 'human')
        with WorkspaceDBRepository.open() as repo:
            results = repo.search_entities(
                query=query, entity_type=entity_type, status=status, limit=limit
            )
        if output == 'json':
            print(json.dumps({
                "ok": True,
                "query": query,
                "count": len(results),
                "entities": results,
            }, indent=2, default=str))
            return
        if not results:
            print(f"No entities match '{query}' (type={entity_type or 'any'}, status={status})")
            return
        print(f"# {len(results)} match{'es' if len(results) != 1 else ''} for '{query}'")
        for e in results:
            print(_format_entity_line(e))
    except Exception as e:
        handle_cli_error(e, "entity-search", getattr(args, 'verbose', False))
