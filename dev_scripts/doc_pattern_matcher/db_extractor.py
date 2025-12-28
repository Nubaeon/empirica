#!/usr/bin/env python3
"""
Database Pattern Extractor - Extract schema from actual SQLite database

Compares against code patterns to detect:
- Tables in DB but not in code (orphaned)
- Tables in code but not in DB (missing migrations)
- Column mismatches

Output: db_patterns.json
"""

import json
import sqlite3
from pathlib import Path
from typing import Dict, List, Any
from dataclasses import dataclass, asdict


@dataclass
class DBTablePattern:
    table_name: str
    columns: List[Dict[str, str]]  # [{"name": "id", "type": "TEXT", "nullable": False}]
    row_count: int


class DBPatternExtractor:
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.tables: Dict[str, DBTablePattern] = {}
        
    def extract_all(self) -> Dict[str, Any]:
        """Extract patterns from SQLite database"""
        print("🗄️  Extracting database patterns...")
        
        if not self.db_path.exists():
            print(f"⚠️  Database not found: {self.db_path}")
            return {"tables": {}}
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        table_names = [row[0] for row in cursor.fetchall()]
        
        for table_name in table_names:
            self._extract_table(cursor, table_name)
        
        conn.close()
        
        print(f"✅ Extracted {len(self.tables)} tables from database")
        
        return {
            "tables": {k: asdict(v) for k, v in self.tables.items()}
        }
    
    def _extract_table(self, cursor: sqlite3.Cursor, table_name: str):
        """Extract schema for single table"""
        # Get table info
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = []
        
        for row in cursor.fetchall():
            col_id, col_name, col_type, not_null, default_val, primary_key = row
            columns.append({
                "name": col_name,
                "type": col_type,
                "nullable": not not_null,
                "primary_key": bool(primary_key)
            })
        
        # Get row count
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        row_count = cursor.fetchone()[0]
        
        self.tables[table_name] = DBTablePattern(
            table_name=table_name,
            columns=columns,
            row_count=row_count
        )


def main():
    root_dir = Path("/home/yogapad/empirical-ai/empirica")
    db_path = root_dir / ".empirica/empirica_state.db"
    
    extractor = DBPatternExtractor(db_path)
    patterns = extractor.extract_all()
    
    output_file = root_dir / "dev_scripts/doc_pattern_matcher/db_patterns.json"
    output_file.write_text(json.dumps(patterns, indent=2))
    
    print(f"\n✅ DB patterns saved to: {output_file}")
    print(f"   Tables: {len(patterns['tables'])}")


if __name__ == "__main__":
    main()
