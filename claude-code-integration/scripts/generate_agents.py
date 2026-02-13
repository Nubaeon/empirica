#!/usr/bin/env python3
"""
Agent Generator: Generate Claude Code custom agents from Empirica persona profiles.

Maps persona JSON files (.empirica/personas/*.json) to Claude Code agent .md files
with YAML frontmatter and epistemic system prompts.

Mapping:
  capabilities.can_read_files    -> Read, Grep, Glob tools
  capabilities.can_modify_code   -> Edit, Write tools
  capabilities.can_call_external -> Bash tool
  focus_domains                  -> System prompt expertise areas
  priors                         -> Epistemic baseline in prompt
  thresholds                     -> Sentinel gate parameters

Usage:
  python generate_agents.py                          # Generate from .empirica/personas/
  python generate_agents.py --personas-dir /path     # Custom persona directory
  python generate_agents.py --output-dir /path       # Custom output directory
  python generate_agents.py --dry-run                # Preview without writing
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Optional


# Tool mapping: persona capabilities -> Claude Code tool names
TOOL_MAPPING = {
    "read_tools": ["Read", "Grep", "Glob"],
    "modify_tools": ["Edit", "Write"],
    "execute_tools": ["Bash"],
    "agent_tools": ["Task"],
    "web_tools": ["WebFetch", "WebSearch"],
    "notebook_tools": ["NotebookEdit"],
}

# Tools available to all agents (noetic baseline)
NOETIC_TOOLS = ["Read", "Grep", "Glob"]

# Color mapping: persona domain -> agent color
DOMAIN_COLORS = {
    "security": "red",
    "performance": "yellow",
    "ux": "cyan",
    "architecture": "blue",
    "testing": "green",
    "outreach": "magenta",
}

# Thinking phase mapping
PHASE_DESCRIPTIONS = {
    "noetic": "investigation, analysis, and exploration",
    "praxic": "implementation, modification, and execution",
}


def load_persona(path: Path) -> Optional[Dict]:
    """Load a persona JSON file."""
    try:
        with open(path) as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        print(f"  Warning: Could not load {path.name}: {e}", file=sys.stderr)
        return None


def resolve_tools(capabilities: Dict) -> List[str]:
    """Map persona capabilities to Claude Code tool names."""
    tools = list(NOETIC_TOOLS)  # All agents get read access

    if capabilities.get("can_modify_code", False):
        tools.extend(TOOL_MAPPING["modify_tools"])

    if capabilities.get("can_call_external_tools", False):
        tools.extend(TOOL_MAPPING["execute_tools"])

    if capabilities.get("can_spawn_subpersonas", False):
        tools.extend(TOOL_MAPPING["agent_tools"])

    # Deduplicate while preserving order
    seen = set()
    return [t for t in tools if not (t in seen or seen.add(t))]


def resolve_color(persona: Dict) -> str:
    """Determine agent color from persona domains."""
    domains = persona.get("epistemic_config", {}).get("focus_domains", [])
    for domain_key, color in DOMAIN_COLORS.items():
        if any(domain_key in d.lower() for d in domains):
            return color
    return "blue"  # Default


def resolve_phase(capabilities: Dict) -> str:
    """Determine if agent is primarily noetic or praxic."""
    if capabilities.get("can_modify_code", False):
        return "praxic"
    return "noetic"


def agent_name_from_file(filepath: Path) -> str:
    """Generate agent name from filename (more reliable than persona_id)."""
    name = filepath.stem.replace("_", "-")
    # Remove common suffixes that aren't meaningful for agent names
    for suffix in ["-comp", "-demo"]:
        if name.endswith(suffix):
            name = name[:-len(suffix)]
    return name


def build_description(persona: Dict, phase: str, agent_name: str) -> str:
    """Build the agent description with example blocks."""
    name = persona.get("name", "Unknown")
    domains = persona.get("epistemic_config", {}).get("focus_domains", [])
    domain_str = ", ".join(domains[:5]) if domains else "general"

    phase_desc = PHASE_DESCRIPTIONS.get(phase, "analysis")

    examples = []

    # Example 1: Direct invocation
    examples.append(f"""<example>
Context: User needs {domain_str} expertise for {phase_desc}
user: "Investigate the {domains[0] if domains else 'system'} aspects of this component"
assistant: "I'll use the empirica-integration:{agent_name} agent for specialized {domain_str} analysis."
<commentary>
Task matches {name}'s focus domains ({domain_str}), triggering specialized agent.
</commentary>
</example>""")

    # Example 2: Proactive trigger
    if phase == "praxic":
        examples.append(f"""<example>
Context: Implementation task requiring {domain_str} expertise
user: "Fix the {domains[0] if domains else 'code'} issues in this module"
assistant: "I'll use the empirica-integration:{agent_name} agent to analyze and fix these issues."
<commentary>
Praxic task matching {name}'s capabilities - agent can read, analyze, and modify code.
</commentary>
</example>""")
    else:
        examples.append(f"""<example>
Context: Investigation requiring {domain_str} analysis
user: "What are the {domains[0] if domains else 'potential'} concerns here?"
assistant: "I'll use the empirica-integration:{agent_name} agent for focused investigation."
<commentary>
Noetic investigation matching {name}'s focus domains - read-only deep analysis.
</commentary>
</example>""")

    return f"""Use this agent for {phase_desc} tasks requiring {domain_str} expertise. This agent has {name}'s epistemic profile with calibrated confidence thresholds.

{chr(10).join(examples)}"""


def build_system_prompt(persona: Dict, phase: str) -> str:
    """Build the markdown system prompt from persona config."""
    name = persona.get("name", "Unknown Expert")
    domains = persona.get("epistemic_config", {}).get("focus_domains", [])
    priors = persona.get("epistemic_config", {}).get("priors", {})
    thresholds = persona.get("epistemic_config", {}).get("thresholds", {})
    capabilities = persona.get("capabilities", {})

    domain_str = ", ".join(domains) if domains else "general analysis"
    phase_desc = PHASE_DESCRIPTIONS.get(phase, "analysis")

    # Format priors as readable baseline
    prior_lines = []
    for key in ["know", "uncertainty", "context", "clarity", "signal"]:
        if key in priors:
            prior_lines.append(f"  - **{key}**: {priors[key]}")

    priors_block = "\n".join(prior_lines) if prior_lines else "  - Default baseline"

    # Threshold block
    threshold_lines = []
    for key, val in thresholds.items():
        threshold_lines.append(f"  - **{key}**: {val}")
    threshold_block = "\n".join(threshold_lines) if threshold_lines else "  - Default thresholds"

    # Capability description
    cap_desc = []
    if capabilities.get("can_read_files"):
        cap_desc.append("read and analyze files")
    if capabilities.get("can_modify_code"):
        cap_desc.append("modify code")
    if capabilities.get("can_call_external_tools"):
        cap_desc.append("execute commands")
    if capabilities.get("can_spawn_subpersonas"):
        cap_desc.append("spawn sub-agents")
    cap_str = ", ".join(cap_desc) if cap_desc else "analyze information"

    max_depth = capabilities.get("max_investigation_depth", 5)

    prompt = f"""You are {name}, a specialized Empirica epistemic agent for {phase_desc}.

## Domain Expertise

Your focus domains: **{domain_str}**

You can: {cap_str}.

## Epistemic Baseline (Priors)

Your calibrated starting confidence:
{priors_block}

These priors reflect your domain expertise. Adjust based on actual investigation findings.

## Operating Thresholds

{threshold_block}

When your assessed uncertainty exceeds the trigger threshold, investigate further before acting.
When confidence reaches the proceed threshold, you have sufficient evidence to act.

## Investigation Protocol

1. **Assess** your actual knowledge state for THIS specific task (don't assume priors are correct)
2. **Investigate** systematically within your focus domains ({domain_str})
3. **Log findings** as you discover them - use structured observations
4. **Report** with confidence-rated conclusions

Maximum investigation depth: {max_depth} rounds.

## Output Format

Structure your results as:
- **Assessment**: Current epistemic state for the task
- **Findings**: What you discovered, with confidence ratings
- **Unknowns**: What remains unclear and needs further investigation
- **Recommendations**: Concrete next steps, ranked by impact"""

    if phase == "praxic":
        prompt += """

## Action Protocol

As a praxic agent, you can implement changes directly:
- Make minimal, focused modifications
- Verify changes don't introduce regressions
- Log what you changed and why"""

    return prompt


def generate_agent_md(persona: Dict, agent_name: str) -> Optional[str]:
    """Generate a complete agent .md file from persona JSON."""
    capabilities = persona.get("capabilities", {})
    phase = resolve_phase(capabilities)
    tools = resolve_tools(capabilities)
    color = resolve_color(persona)
    name = agent_name
    description = build_description(persona, phase, agent_name)
    system_prompt = build_system_prompt(persona, phase)

    # Build YAML frontmatter
    tools_str = json.dumps(tools)
    frontmatter = f"""---
name: {name}
description: {description}
model: inherit
color: {color}
tools: {tools_str}
---"""

    return f"{frontmatter}\n\n{system_prompt}\n"


def should_generate(persona: Dict, filepath: Path) -> bool:
    """Filter personas that should become agents."""
    stem = filepath.stem

    # Skip composite/demo personas - they're for testing
    if stem.endswith("_comp") or stem.endswith("_demo"):
        return False

    # Skip personas without meaningful domains
    domains = persona.get("epistemic_config", {}).get("focus_domains", [])
    if not domains:
        return False

    # Skip test personas
    if "test" in stem.lower() or "comm_test" in stem:
        return False

    return True


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Generate Claude Code agents from Empirica personas")
    parser.add_argument("--personas-dir", type=str, help="Directory containing persona JSON files")
    parser.add_argument("--output-dir", type=str, help="Output directory for agent .md files")
    parser.add_argument("--dry-run", action="store_true", help="Preview without writing files")
    parser.add_argument("--force", action="store_true", help="Overwrite existing agent files")
    parser.add_argument("--verbose", action="store_true", help="Show detailed output")
    args = parser.parse_args()

    # Resolve persona directory
    if args.personas_dir:
        personas_dir = Path(args.personas_dir)
    else:
        # Auto-detect from git root or cwd
        cwd = Path.cwd()
        personas_dir = cwd / ".empirica" / "personas"
        if not personas_dir.exists():
            # Try git root
            try:
                import subprocess
                git_root = subprocess.check_output(
                    ["git", "rev-parse", "--show-toplevel"],
                    stderr=subprocess.DEVNULL, text=True
                ).strip()
                personas_dir = Path(git_root) / ".empirica" / "personas"
            except (subprocess.CalledProcessError, FileNotFoundError):
                pass

    if not personas_dir.exists():
        print(f"Error: Personas directory not found: {personas_dir}", file=sys.stderr)
        sys.exit(1)

    # Resolve output directory
    if args.output_dir:
        output_dir = Path(args.output_dir)
    else:
        # Default: plugin agents/ directory
        script_dir = Path(__file__).resolve().parent
        output_dir = script_dir.parent / "agents"

    output_dir.mkdir(parents=True, exist_ok=True)

    # Load and generate
    persona_files = sorted(personas_dir.glob("*.json"))
    if not persona_files:
        print(f"No persona files found in {personas_dir}", file=sys.stderr)
        sys.exit(1)

    generated = 0
    skipped = 0
    errors = 0

    print(f"Generating agents from {len(persona_files)} personas in {personas_dir}")
    print(f"Output directory: {output_dir}")
    print()

    for pf in persona_files:
        persona = load_persona(pf)
        if not persona:
            errors += 1
            continue

        if not should_generate(persona, pf):
            if args.verbose:
                print(f"  Skip: {pf.name} (filtered)")
            skipped += 1
            continue

        name = agent_name_from_file(pf)
        output_file = output_dir / f"{name}.md"

        if output_file.exists() and not args.force:
            if args.verbose:
                print(f"  Skip: {name}.md (exists, use --force to overwrite)")
            skipped += 1
            continue

        content = generate_agent_md(persona, name)
        if not content:
            errors += 1
            continue

        if args.dry_run:
            print(f"  Would write: {name}.md ({len(content)} bytes)")
            if args.verbose:
                print(f"    Domains: {persona.get('epistemic_config', {}).get('focus_domains', [])}")
                tools = resolve_tools(persona.get("capabilities", {}))
                print(f"    Tools: {tools}")
        else:
            output_file.write_text(content)
            print(f"  Generated: {name}.md")

        generated += 1

    print()
    print(f"Results: {generated} generated, {skipped} skipped, {errors} errors")
    return 0 if errors == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
