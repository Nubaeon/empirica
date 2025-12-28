#!/usr/bin/env python3
"""
CLI Markdown Generator - Generate documentation from extracted CLI commands

Reads cli_commands_extracted.json and generates comprehensive markdown documentation.
"""

import json
import sys
from pathlib import Path
from typing import Dict, List
from datetime import datetime


def format_argument(arg: Dict) -> str:
    """Format a single argument for display"""
    name = arg['name']
    arg_type = arg['type']
    required = arg['required']
    default = arg['default']
    help_text = arg['help']
    choices = arg['choices']
    
    # Format name
    if name.startswith('--'):
        formatted_name = f"`{name}`"
    else:
        formatted_name = f"`{name}` (positional)"
    
    # Build description
    parts = []
    
    if required:
        parts.append("**Required**")
    else:
        parts.append("**Optional**")
    
    if arg_type == 'flag':
        parts.append(f"Flag (default: `{default}`)")
    else:
        parts.append(f"Type: {arg_type}")
        if default is not None:
            parts.append(f"Default: `{default}`")
    
    if choices:
        parts.append(f"Choices: {', '.join(f'`{c}`' for c in choices)}")
    
    if help_text:
        parts.append(f"  \n  {help_text}")
    
    return f"- {formatted_name}: {' | '.join(parts)}"


def generate_command_section(cmd: Dict) -> str:
    """Generate markdown section for a single command"""
    
    lines = []
    
    # Command header
    lines.append(f"### `{cmd['name']}`")
    lines.append("")
    
    # Description
    if cmd['help']:
        lines.append(cmd['help'])
        lines.append("")
    
    # Usage example
    required_args = [a for a in cmd['arguments'] if a['required']]
    optional_flags = [a for a in cmd['arguments'] if a['type'] == 'flag' and not a['required']]
    
    usage_parts = [f"empirica {cmd['name']}"]
    
    for arg in required_args:
        if arg['name'].startswith('--'):
            usage_parts.append(f"{arg['name']} <VALUE>")
        else:
            usage_parts.append(f"<{arg['name'].upper()}>")
    
    if optional_flags:
        usage_parts.append("[OPTIONS]")
    
    lines.append("**Usage:**")
    lines.append("```bash")
    lines.append(" ".join(usage_parts))
    lines.append("```")
    lines.append("")
    
    # Arguments
    if cmd['arguments']:
        lines.append("**Arguments:**")
        lines.append("")
        for arg in cmd['arguments']:
            lines.append(format_argument(arg))
        lines.append("")
    
    # Handler info (for developers)
    if cmd['handler'] and cmd['handler'] != 'unknown':
        lines.append(f"**Handler:** `{cmd['handler']}`")
        lines.append("")
    
    lines.append("---")
    lines.append("")
    
    return "\n".join(lines)


def generate_markdown(data: Dict) -> str:
    """Generate complete markdown documentation"""
    
    lines = []
    
    # Header
    lines.append("# Empirica CLI Commands Reference (v4.0)")
    lines.append("")
    lines.append(f"**Generated from code:** {datetime.now().strftime('%Y-%m-%d')}")
    lines.append(f"**Total commands:** {data['total_commands']}")
    lines.append(f"**Source:** `{Path(data['source_file']).name}`")
    lines.append("")
    lines.append("---")
    lines.append("")
    
    # Table of contents
    lines.append("## Table of Contents")
    lines.append("")
    for category in data['categorized'].keys():
        anchor = category.lower().replace(' ', '-').replace('&', 'and')
        lines.append(f"- [{category}](#{anchor})")
    lines.append("")
    lines.append("---")
    lines.append("")
    
    # Commands by category
    for category, commands in data['categorized'].items():
        lines.append(f"## {category}")
        lines.append("")
        lines.append(f"**{len(commands)} commands**")
        lines.append("")
        
        for cmd in commands:
            lines.append(generate_command_section(cmd))
    
    # Footer
    lines.append("---")
    lines.append("")
    lines.append("## Notes")
    lines.append("")
    lines.append("- **Generated documentation:** This file is auto-generated from the codebase.")
    lines.append("- **100% accuracy:** Every command listed here exists in the current codebase.")
    lines.append("- **No phantom commands:** Commands not listed here do not exist.")
    lines.append("")
    lines.append("**To regenerate this documentation:**")
    lines.append("```bash")
    lines.append("cd dev_scripts/doc_regeneration")
    lines.append("python3 extract_cli_commands.py")
    lines.append("python3 generate_cli_markdown.py")
    lines.append("```")
    lines.append("")
    lines.append("**Last updated:** " + datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC'))
    lines.append("")
    
    return "\n".join(lines)


def main():
    """Main entry point"""
    
    # Load extracted data
    input_path = Path(__file__).parent / 'cli_commands_extracted.json'
    
    if not input_path.exists():
        print(f"❌ Error: {input_path} not found")
        print("   Run extract_cli_commands.py first!")
        sys.exit(1)
    
    print(f"📖 Loading {input_path}...")
    
    with open(input_path) as f:
        data = json.load(f)
    
    print(f"✅ Loaded {data['total_commands']} commands")
    
    # Generate markdown
    print("📝 Generating markdown...")
    markdown = generate_markdown(data)
    
    # Save output
    output_path = Path(__file__).parent.parent.parent / 'docs' / 'reference' / 'CLI_COMMANDS_GENERATED.md'
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        f.write(markdown)
    
    print(f"✅ Saved to: {output_path}")
    print(f"📊 Generated {len(markdown.splitlines())} lines of documentation")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
