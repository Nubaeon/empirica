#!/usr/bin/env python3
"""
Sync System Prompts - Generate AI-specific variants from canonical core

Usage:
    python scripts/sync_system_prompts.py [--dry-run]

Structure:
    CANONICAL_CORE.md           <- Source of truth (AI-agnostic)
    model_deltas/
        claude.md               <- Claude-specific additions
        qwen.md                 <- Qwen-specific additions
        gemini.md               <- Gemini-specific additions
        copilot.md              <- Copilot-specific additions

    Output:
        CLAUDE.md               <- Core + claude.md delta
        QWEN.md                 <- Core + qwen.md delta
        etc.
"""

import os
import sys
from pathlib import Path
from datetime import datetime

PROMPTS_DIR = Path(__file__).parent.parent / "docs" / "system-prompts"
DELTAS_DIR = PROMPTS_DIR / "model_deltas"
CORE_FILE = PROMPTS_DIR / "CANONICAL_CORE.md"

# Model configurations: (delta_file, output_file, identity_replacement)
MODELS = {
    "claude": {
        "output": "CLAUDE.md",
        "identity": "Claude Code - Implementation Lead",
        "ai_id": "claude-code",
    },
    "qwen": {
        "output": "QWEN.md",
        "identity": "Qwen - Multi-modal Assistant",
        "ai_id": "qwen-assistant",
    },
    "gemini": {
        "output": "GEMINI.md",
        "identity": "Gemini - Google AI Assistant",
        "ai_id": "gemini-assistant",
    },
    "copilot": {
        "output": "COPILOT_INSTRUCTIONS.md",
        "identity": "GitHub Copilot - Code Assistant",
        "ai_id": "copilot-code",
    },
    "rovo": {
        "output": "ROVODEV.md",
        "identity": "Rovo Dev - Atlassian AI Agent",
        "ai_id": "rovo-dev",
    },
}


def load_core() -> str:
    """Load canonical core prompt"""
    if not CORE_FILE.exists():
        raise FileNotFoundError(f"Core file not found: {CORE_FILE}")
    return CORE_FILE.read_text()


def load_delta(model: str) -> str:
    """Load model-specific delta (if exists)"""
    delta_file = DELTAS_DIR / f"{model}.md"
    if delta_file.exists():
        return delta_file.read_text()
    return ""


def generate_variant(core: str, model: str, config: dict, delta: str) -> str:
    """Generate model-specific variant from core + delta"""

    # Replace generic identity with model-specific
    variant = core.replace(
        "**You are:** An AI agent integrated with Empirica epistemic framework",
        f"**You are:** {config['identity']}"
    )

    # Update header
    variant = variant.replace(
        "# Empirica System Prompt - Canonical Core v1.2.1",
        f"# Empirica System Prompt - {model.upper()} v1.2.1"
    )
    variant = variant.replace(
        "**AI-Agnostic Core - All agents extend this**",
        f"**Model:** {model.upper()} | **Generated:** {datetime.now().strftime('%Y-%m-%d')}"
    )

    # Append model-specific delta before final line
    if delta.strip():
        # Insert delta before the final tagline
        final_line = "**Epistemic honesty is functional. Start naturally.**"
        delta_section = f"\n---\n\n## {model.upper()}-SPECIFIC\n\n{delta.strip()}\n\n---\n\n"
        variant = variant.replace(final_line, delta_section + final_line)

    return variant


def sync_prompts(dry_run: bool = False):
    """Sync all model variants from canonical core"""

    print(f"Loading canonical core: {CORE_FILE}")
    core = load_core()
    print(f"  Core size: {len(core)} chars, {len(core.splitlines())} lines")

    # Ensure deltas directory exists
    DELTAS_DIR.mkdir(exist_ok=True)

    results = []
    for model, config in MODELS.items():
        delta = load_delta(model)
        variant = generate_variant(core, model, config, delta)

        output_path = PROMPTS_DIR / config["output"]

        if dry_run:
            print(f"\n[DRY-RUN] Would write: {config['output']}")
            print(f"  Size: {len(variant)} chars, {len(variant.splitlines())} lines")
            print(f"  Delta: {len(delta)} chars" if delta else "  Delta: (none)")
        else:
            output_path.write_text(variant)
            print(f"\nWrote: {config['output']}")
            print(f"  Size: {len(variant)} chars, {len(variant.splitlines())} lines")

        results.append({
            "model": model,
            "output": config["output"],
            "lines": len(variant.splitlines()),
            "has_delta": bool(delta),
        })

    # Summary
    print("\n" + "=" * 50)
    print("SYNC COMPLETE" if not dry_run else "DRY-RUN COMPLETE")
    print("=" * 50)
    for r in results:
        delta_marker = " (+delta)" if r["has_delta"] else ""
        print(f"  {r['output']:30} {r['lines']:4} lines{delta_marker}")

    return results


def main():
    dry_run = "--dry-run" in sys.argv

    if dry_run:
        print("=== DRY RUN MODE ===\n")

    try:
        sync_prompts(dry_run=dry_run)
    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
