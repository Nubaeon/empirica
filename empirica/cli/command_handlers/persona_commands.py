"""
Persona Commands - CLI for emerged persona management

Commands:
- persona-list: List all emerged personas
- persona-show: Show details of a specific persona
- persona-promote: Promote emerged persona to MCO personas.yaml
"""

import json
import logging
from typing import Optional

logger = logging.getLogger(__name__)


def handle_persona_list_command(args):
    """Handle persona-list command - list all emerged personas."""
    try:
        from empirica.core.emerged_personas import EmergedPersonaStore

        output_format = getattr(args, 'output', 'human')
        domain_filter = getattr(args, 'domain', None)

        store = EmergedPersonaStore()

        if domain_filter:
            personas = store.find_by_domain(domain_filter)
        else:
            personas = store.list_all()

        if output_format == 'json':
            result = {
                "ok": True,
                "count": len(personas),
                "personas": [p.to_dict() for p in personas]
            }
            print(json.dumps(result, indent=2))
        else:
            if not personas:
                print("No emerged personas found.")
                print("\nPersonas are extracted from successful investigation branches.")
                print("They will appear here after completing epistemic loops with convergence.")
            else:
                print(f"Found {len(personas)} emerged persona(s):\n")
                for p in personas:
                    domains = ", ".join(p.task_domains[:3]) or "general"
                    print(f"  {p.persona_id[:12]}... | {p.name}")
                    print(f"    Domains: {domains}")
                    print(f"    Loops: {p.loops_to_converge} | Findings: {p.findings_count}")
                    print(f"    Reputation: {p.reputation_score:.2f} ({p.uses_count} uses, {p.success_count} successes)")
                    print()

        return None

    except Exception as e:
        logger.error(f"Persona list failed: {e}")
        print(json.dumps({"ok": False, "error": str(e)}, indent=2))
        return 1


def handle_persona_show_command(args):
    """Handle persona-show command - show details of a specific persona."""
    try:
        from empirica.core.emerged_personas import EmergedPersonaStore

        persona_id = args.persona_id
        output_format = getattr(args, 'output', 'human')

        store = EmergedPersonaStore()
        persona = store.load(persona_id)

        if not persona:
            print(json.dumps({"ok": False, "error": f"Persona not found: {persona_id}"}, indent=2))
            return 1

        if output_format == 'json':
            result = {"ok": True, "persona": persona.to_dict()}
            print(json.dumps(result, indent=2))
        else:
            print(f"Persona: {persona.name}")
            print(f"ID: {persona.persona_id}")
            print(f"Source: session {persona.source_session_id[:8]}...")
            if persona.source_branch_id:
                print(f"Branch: {persona.source_branch_id[:8]}...")
            print()

            print("Vector Profile:")
            print("  Initial → Final (Delta)")
            for key in sorted(persona.delta_pattern.keys()):
                initial = persona.initial_vectors.get(key, 0.5)
                final = persona.final_vectors.get(key, 0.5)
                delta = persona.delta_pattern[key]
                arrow = "↑" if delta > 0 else "↓" if delta < 0 else "→"
                print(f"    {key:15s}: {initial:.2f} → {final:.2f} ({arrow}{abs(delta):.2f})")
            print()

            print("Convergence:")
            print(f"  Loops: {persona.loops_to_converge}")
            print(f"  Threshold: {persona.convergence_threshold}")
            print(f"  Scope: breadth={persona.scope_breadth}, duration={persona.scope_duration}")
            print()

            print("Task Characteristics:")
            print(f"  Domains: {', '.join(persona.task_domains)}")
            print(f"  Keywords: {', '.join(persona.task_keywords[:5])}")
            print()

            print("Performance:")
            print(f"  Findings: {persona.findings_count}")
            print(f"  Unknowns resolved: {persona.unknowns_resolved}")
            print(f"  Reputation: {persona.reputation_score:.2f}")
            print(f"  Uses: {persona.uses_count}, Successes: {persona.success_count}")

        return None

    except Exception as e:
        logger.error(f"Persona show failed: {e}")
        print(json.dumps({"ok": False, "error": str(e)}, indent=2))
        return 1


def handle_persona_promote_command(args):
    """Handle persona-promote command - promote emerged persona to MCO."""
    try:
        from empirica.core.emerged_personas import EmergedPersonaStore
        from pathlib import Path
        import yaml

        persona_id = args.persona_id
        output_format = getattr(args, 'output', 'human')

        store = EmergedPersonaStore()
        persona = store.load(persona_id)

        if not persona:
            print(json.dumps({"ok": False, "error": f"Persona not found: {persona_id}"}, indent=2))
            return 1

        # Find MCO personas.yaml
        mco_path = Path.cwd() / ".empirica" / "mco" / "personas.yaml"
        if not mco_path.parent.exists():
            mco_path.parent.mkdir(parents=True, exist_ok=True)

        # Load existing personas or create new
        if mco_path.exists():
            with open(mco_path) as f:
                mco_data = yaml.safe_load(f) or {"personas": []}
        else:
            mco_data = {"personas": []}

        # Convert emerged persona to MCO format
        mco_persona = {
            "id": persona.persona_id,
            "name": persona.name,
            "focus_domains": persona.task_domains,
            "priors": {
                "know": persona.final_vectors.get("know", 0.5),
                "uncertainty": persona.final_vectors.get("uncertainty", 0.3),
                "curiosity": persona.final_vectors.get("curiosity", 0.7),
            },
            "reputation_score": persona.reputation_score,
            "provenance": {
                "type": "emerged",
                "source_session": persona.source_session_id,
                "extracted_at": persona.extracted_at,
                "loops_to_converge": persona.loops_to_converge
            }
        }

        # Check if already exists
        existing_ids = [p.get("id") for p in mco_data.get("personas", [])]
        if persona.persona_id in existing_ids:
            print(json.dumps({"ok": False, "error": f"Persona already in MCO: {persona_id}"}, indent=2))
            return 1

        # Add to MCO
        mco_data["personas"].append(mco_persona)

        # Save
        with open(mco_path, 'w') as f:
            yaml.dump(mco_data, f, default_flow_style=False, sort_keys=False)

        result = {
            "ok": True,
            "message": f"Promoted persona to MCO",
            "persona_id": persona.persona_id,
            "mco_path": str(mco_path)
        }

        if output_format == 'json':
            print(json.dumps(result, indent=2))
        else:
            print(f"Promoted persona {persona.persona_id} to MCO")
            print(f"  Name: {persona.name}")
            print(f"  MCO: {mco_path}")

        return None

    except Exception as e:
        logger.error(f"Persona promote failed: {e}")
        print(json.dumps({"ok": False, "error": str(e)}, indent=2))
        return 1


def handle_persona_find_command(args):
    """Handle persona-find command - find personas similar to a task."""
    try:
        from empirica.core.emerged_personas import EmergedPersonaStore

        task = args.task
        limit = getattr(args, 'limit', 5)
        output_format = getattr(args, 'output', 'human')

        store = EmergedPersonaStore()
        personas = store.find_similar(task, limit=limit)

        if output_format == 'json':
            result = {
                "ok": True,
                "query": task,
                "count": len(personas),
                "personas": [p.to_dict() for p in personas]
            }
            print(json.dumps(result, indent=2))
        else:
            if not personas:
                print(f"No personas found matching: {task}")
            else:
                print(f"Found {len(personas)} persona(s) matching: {task}\n")
                for p in personas:
                    domains = ", ".join(p.task_domains[:3])
                    print(f"  {p.persona_id[:12]}... | {p.name}")
                    print(f"    Domains: {domains} | Rep: {p.reputation_score:.2f}")
                    print()

        return None

    except Exception as e:
        logger.error(f"Persona find failed: {e}")
        print(json.dumps({"ok": False, "error": str(e)}, indent=2))
        return 1
