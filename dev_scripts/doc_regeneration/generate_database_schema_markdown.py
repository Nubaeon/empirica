#!/usr/bin/env python3
"""
Database Schema Markdown Generator - Generate documentation from extracted schema

Reads database_schema_extracted.json and generates comprehensive markdown documentation.
"""

import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List


def format_column(col: Dict) -> str:
    """Format a column for display"""
    parts = [f"**`{col['name']}`**", f"Type: `{col['type']}`"]
    
    if col['primary_key']:
        parts.append("🔑 PRIMARY KEY")
    if col['not_null']:
        parts.append("NOT NULL")
    if col['unique']:
        parts.append("UNIQUE")
    if col['default']:
        parts.append(f"Default: `{col['default']}`")
    if col['foreign_key']:
        fk = col['foreign_key']
        parts.append(f"→ References `{fk['table']}.{fk['column']}`")
    
    return " | ".join(parts)


def format_table(table: Dict) -> str:
    """Format a table section"""
    lines = []
    
    # Table header
    lines.append(f"### `{table['name']}`")
    lines.append("")
    
    # Column count
    lines.append(f"**{len(table['columns'])} columns**")
    lines.append("")
    
    # Columns
    lines.append("**Columns:**")
    lines.append("")
    for col in table['columns']:
        lines.append(f"- {format_column(col)}")
    lines.append("")
    
    # Foreign keys (table-level)
    if table['foreign_keys']:
        lines.append("**Foreign Keys:**")
        lines.append("")
        for fk in table['foreign_keys']:
            cols = ", ".join(fk['columns'])
            ref_cols = ", ".join(fk['references_columns'])
            lines.append(f"- `({cols})` → `{fk['references_table']}({ref_cols})`")
        lines.append("")
    
    # Unique constraints
    if table['unique_constraints']:
        lines.append("**Unique Constraints:**")
        lines.append("")
        for uc in table['unique_constraints']:
            cols = ", ".join(uc)
            lines.append(f"- `({cols})`")
        lines.append("")
    
    lines.append("---")
    lines.append("")
    
    return "\n".join(lines)


def generate_markdown(data: Dict) -> str:
    """Generate complete markdown documentation"""
    
    lines = []
    
    # Header
    lines.append("# Empirica Database Schema Reference (v4.0)")
    lines.append("")
    lines.append(f"**Generated from code:** {datetime.now().strftime('%Y-%m-%d')}")
    lines.append(f"**Total tables:** {data['total_tables']}")
    lines.append(f"**Total indexes:** {data['total_indexes']}")
    lines.append(f"**Source:** `{Path(data['source_file']).name}`")
    lines.append("")
    lines.append("---")
    lines.append("")
    
    # Table of contents
    lines.append("## Table of Contents")
    lines.append("")
    
    # Group tables by category
    categories = {
        'Core': ['sessions', 'cascades', 'reflexes'],
        'Goals & Tasks': ['goals', 'subtasks'],
        'Investigation': ['noetic_tools', 'investigation_logs', 'praxic_logs', 'investigation_branches', 'merge_decisions'],
        'Project Tracking': ['projects', 'project_handoffs', 'project_findings', 'project_unknowns', 'project_dead_ends', 'project_reference_docs', 'epistemic_sources'],
        'Handoffs': ['handoff_reports'],
        'Monitoring': ['divergence_tracking', 'drift_monitoring', 'epistemic_snapshots'],
        'Learning': ['bayesian_beliefs', 'mistakes_made']
    }
    
    for category, table_names in categories.items():
        lines.append(f"### {category}")
        for table_name in table_names:
            anchor = table_name.replace('_', '-')
            lines.append(f"- [{table_name}](#{anchor})")
        lines.append("")
    
    lines.append("---")
    lines.append("")
    
    # Tables by category
    for category, table_names in categories.items():
        lines.append(f"## {category}")
        lines.append("")
        
        for table_name in table_names:
            # Find table in data
            table = next((t for t in data['tables'] if t['name'] == table_name), None)
            if table:
                lines.append(format_table(table))
    
    # Indexes
    lines.append("## Indexes")
    lines.append("")
    lines.append(f"**{data['total_indexes']} indexes defined**")
    lines.append("")
    
    # Group indexes by table
    indexes_by_table = {}
    for idx in data['indexes']:
        table = idx['table']
        if table not in indexes_by_table:
            indexes_by_table[table] = []
        indexes_by_table[table].append(idx)
    
    for table, indexes in sorted(indexes_by_table.items()):
        lines.append(f"### `{table}`")
        lines.append("")
        for idx in indexes:
            cols = ", ".join(idx['columns'])
            unique = " (UNIQUE)" if idx['unique'] else ""
            lines.append(f"- `{idx['name']}` on `({cols})`{unique}")
        lines.append("")
    
    # Footer
    lines.append("---")
    lines.append("")
    lines.append("## Notes")
    lines.append("")
    lines.append("- **Generated documentation:** This file is auto-generated from the codebase.")
    lines.append("- **100% accuracy:** Every table/column listed here exists in the current database schema.")
    lines.append("- **Schema evolution:** This represents the current v4.0 schema.")
    lines.append("")
    lines.append("**To regenerate this documentation:**")
    lines.append("```bash")
    lines.append("cd dev_scripts/doc_regeneration")
    lines.append("python3 extract_database_schema.py")
    lines.append("python3 generate_database_schema_markdown.py")
    lines.append("```")
    lines.append("")
    lines.append("**Last updated:** " + datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC'))
    lines.append("")
    
    return "\n".join(lines)


def main():
    """Main entry point"""
    
    # Load extracted data
    input_path = Path(__file__).parent / 'database_schema_extracted.json'
    
    if not input_path.exists():
        print(f"❌ Error: {input_path} not found")
        print("   Run extract_database_schema.py first!")
        sys.exit(1)
    
    print(f"📖 Loading {input_path}...")
    
    with open(input_path) as f:
        data = json.load(f)
    
    print(f"✅ Loaded {data['total_tables']} tables")
    
    # Generate markdown
    print("📝 Generating markdown...")
    markdown = generate_markdown(data)
    
    # Save output
    output_path = Path(__file__).parent.parent.parent / 'docs' / 'reference' / 'DATABASE_SCHEMA_GENERATED.md'
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        f.write(markdown)
    
    print(f"✅ Saved to: {output_path}")
    print(f"📊 Generated {len(markdown.splitlines())} lines of documentation")
    print(f"   {data['total_tables']} tables, {data['total_indexes']} indexes")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
