#!/usr/bin/env python3
"""
Database Schema Extractor - Extract schema from session_database.py

Extracts:
- Table definitions
- Column names and types
- Primary keys
- Foreign keys
- Indexes
- Constraints

Output: JSON structure of database schema
"""

import re
import json
import sys
from pathlib import Path
from typing import Dict, List, Any


def extract_create_table_statements(sql_code: str) -> List[str]:
    """Extract all CREATE TABLE statements from code"""
    
    # Pattern to match CREATE TABLE ... )
    pattern = r'CREATE TABLE(?:\s+IF NOT EXISTS)?\s+(\w+)\s*\((.*?)\)'
    
    matches = re.finditer(pattern, sql_code, re.DOTALL | re.IGNORECASE)
    
    tables = []
    for match in matches:
        table_name = match.group(1)
        table_definition = match.group(2)
        
        tables.append({
            'name': table_name,
            'definition': table_definition.strip()
        })
    
    return tables


def parse_column_definition(col_def: str) -> Dict:
    """Parse a single column definition"""
    
    # Clean up the definition
    col_def = col_def.strip()
    
    # Extract column name (first word)
    parts = col_def.split(None, 1)
    if not parts:
        return {}
    
    col_name = parts[0]
    rest = parts[1] if len(parts) > 1 else ""
    
    # Extract type
    type_match = re.match(r'(\w+(?:\([^)]+\))?)', rest)
    col_type = type_match.group(1) if type_match else "TEXT"
    
    # Check for constraints
    is_primary_key = 'PRIMARY KEY' in rest.upper()
    is_not_null = 'NOT NULL' in rest.upper()
    is_unique = 'UNIQUE' in rest.upper()
    
    # Extract default value
    default = None
    default_match = re.search(r'DEFAULT\s+([^\s,]+)', rest, re.IGNORECASE)
    if default_match:
        default = default_match.group(1)
    
    # Extract foreign key
    foreign_key = None
    fk_match = re.search(r'REFERENCES\s+(\w+)\s*\((\w+)\)', rest, re.IGNORECASE)
    if fk_match:
        foreign_key = {
            'table': fk_match.group(1),
            'column': fk_match.group(2)
        }
    
    return {
        'name': col_name,
        'type': col_type,
        'primary_key': is_primary_key,
        'not_null': is_not_null,
        'unique': is_unique,
        'default': default,
        'foreign_key': foreign_key
    }


def parse_table_definition(table_def: str) -> Dict:
    """Parse a table definition into columns and constraints"""
    
    columns = []
    foreign_keys = []
    unique_constraints = []
    
    # Split by commas (but not within parentheses)
    parts = []
    current = ""
    paren_depth = 0
    
    for char in table_def:
        if char == '(':
            paren_depth += 1
        elif char == ')':
            paren_depth -= 1
        elif char == ',' and paren_depth == 0:
            parts.append(current.strip())
            current = ""
            continue
        current += char
    
    if current.strip():
        parts.append(current.strip())
    
    # Parse each part
    for part in parts:
        part = part.strip()
        
        # Check if it's a FOREIGN KEY constraint
        if part.upper().startswith('FOREIGN KEY'):
            fk_match = re.search(
                r'FOREIGN KEY\s*\(([^)]+)\)\s*REFERENCES\s+(\w+)\s*\(([^)]+)\)',
                part,
                re.IGNORECASE
            )
            if fk_match:
                foreign_keys.append({
                    'columns': [c.strip() for c in fk_match.group(1).split(',')],
                    'references_table': fk_match.group(2),
                    'references_columns': [c.strip() for c in fk_match.group(3).split(',')]
                })
        
        # Check if it's a UNIQUE constraint
        elif part.upper().startswith('UNIQUE'):
            unique_match = re.search(r'UNIQUE\s*\(([^)]+)\)', part, re.IGNORECASE)
            if unique_match:
                unique_constraints.append([c.strip() for c in unique_match.group(1).split(',')])
        
        # Otherwise it's a column definition
        else:
            col = parse_column_definition(part)
            if col:
                columns.append(col)
    
    return {
        'columns': columns,
        'foreign_keys': foreign_keys,
        'unique_constraints': unique_constraints
    }


def extract_create_index_statements(sql_code: str) -> List[Dict]:
    """Extract CREATE INDEX statements"""
    
    pattern = r'CREATE\s+(?:UNIQUE\s+)?INDEX\s+(?:IF NOT EXISTS\s+)?(\w+)\s+ON\s+(\w+)\s*\(([^)]+)\)'
    
    matches = re.finditer(pattern, sql_code, re.IGNORECASE)
    
    indexes = []
    for match in matches:
        index_name = match.group(1)
        table_name = match.group(2)
        columns = [c.strip() for c in match.group(3).split(',')]
        
        is_unique = 'UNIQUE' in match.group(0).upper()
        
        indexes.append({
            'name': index_name,
            'table': table_name,
            'columns': columns,
            'unique': is_unique
        })
    
    return indexes


def extract_database_schema(db_file_path: Path) -> Dict:
    """Main extraction function"""
    
    print(f"📖 Parsing {db_file_path}...")
    
    with open(db_file_path) as f:
        code = f.read()
    
    # Extract tables
    table_statements = extract_create_table_statements(code)
    
    tables = []
    for table_stmt in table_statements:
        table_info = parse_table_definition(table_stmt['definition'])
        tables.append({
            'name': table_stmt['name'],
            **table_info
        })
    
    # Extract indexes
    indexes = extract_create_index_statements(code)
    
    print(f"✅ Extracted {len(tables)} tables, {len(indexes)} indexes")
    
    return {
        'tables': tables,
        'indexes': indexes
    }


def main():
    """Main entry point"""
    
    # Find session_database.py
    db_file = Path(__file__).parent.parent.parent / 'empirica' / 'data' / 'session_database.py'
    
    if not db_file.exists():
        print(f"❌ Error: {db_file} not found")
        sys.exit(1)
    
    # Extract schema
    schema = extract_database_schema(db_file)
    
    # Add metadata
    output = {
        'extraction_date': '2025-12-16',
        'source_file': str(db_file),
        'total_tables': len(schema['tables']),
        'total_indexes': len(schema['indexes']),
        **schema
    }
    
    # Save JSON
    output_path = Path(__file__).parent / 'database_schema_extracted.json'
    with open(output_path, 'w') as f:
        json.dump(output, f, indent=2)
    
    print(f"\n✅ Saved to: {output_path}")
    print(f"\n📊 Summary:")
    print(f"   Total tables: {len(schema['tables'])}")
    for table in schema['tables']:
        print(f"   - {table['name']}: {len(table['columns'])} columns")
    print(f"   Total indexes: {len(schema['indexes'])}")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
