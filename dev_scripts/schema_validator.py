#!/usr/bin/env python3
"""
Empirica Schema Validator

Automated detection of schema mismatches between:
1. Actual database schema
2. Code-defined table structures  
3. Actual usage in INSERT/UPDATE/SELECT statements

Purpose: Identify all schema inconsistencies like the goals table issue found during testing.
"""

import sqlite3
import os
import re
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional
import json


class SchemaValidator:
    """Validate Empirica database schema consistency"""
    
    def __init__(self, db_path: str = ".empirica/sessions/sessions.db"):
        self.db_path = Path(db_path)
        if not self.db_path.exists():
            # Try alternative path
            alt_path = Path(".empirica/sessions.db")
            if alt_path.exists():
                self.db_path = alt_path
            else:
                raise FileNotFoundError(f"Database not found at {self.db_path} or .empirica/sessions.db")
        
        self.connection = sqlite3.connect(self.db_path)
        self.cursor = self.connection.cursor()

    def get_actual_schema(self) -> Dict[str, List[Tuple]]:
        """Get actual schema from database"""
        tables = {}
        
        # Get list of tables
        self.cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        table_names = [row[0] for row in self.cursor.fetchall()]
        
        for table_name in table_names:
            # Get column info for each table
            self.cursor.execute(f"PRAGMA table_info({table_name});")
            columns = self.cursor.fetchall()  # (cid, name, type, notnull, dflt_value, pk)
            tables[table_name] = [(col[1], col[2], bool(col[5])) for col in columns]  # (name, type, is_primary_key)
        
        return tables

    def get_expected_schema_from_code(self) -> Dict[str, List[Tuple]]:
        """Extract expected schema from CREATE TABLE statements in code"""
        expected_schema = {}
        
        # Look for all Python files in the codebase
        py_files = list(Path(".").rglob("*.py"))
        
        for py_file in py_files:
            try:
                content = py_file.read_text()
                
                # Find CREATE TABLE statements with robust regex
                # This looks for CREATE TABLE [IF NOT EXISTS] table_name (column definitions)
                create_table_pattern = r'CREATE\s+TABLE(?:\s+IF\s+NOT\s+EXISTS)?\s+(\w+)\s*\(\s*((?:[^()]|\([^)]*\))*)\s*\)'
                
                for match in re.finditer(create_table_pattern, content, re.IGNORECASE | re.DOTALL):
                    table_name = match.group(1)
                    table_body = match.group(2)
                    
                    # Extract column definitions by splitting on commas not inside other parentheses
                    columns_raw = self._split_sql_fields(table_body)
                    
                    table_columns = []
                    for col_define in columns_raw:
                        col_define = col_define.strip()
                        if not col_define or col_define.upper().startswith(('PRIMARY', 'FOREIGN', 'UNIQUE', 'CHECK', 'CONSTRAINT', 'INDEX')):
                            continue  # Skip constraints, not actual columns
                            
                        # Extract column name and type
                        # Handle patterns like: name TYPE, name TYPE NOT NULL, name TYPE DEFAULT value, etc.
                        parts = col_define.split(None, 2)  # Split on first 2 whitespace boundaries
                        if len(parts) >= 2:
                            col_name = parts[0].strip('`"\'')
                            col_type = parts[1].split()[0]  # Get just the basic type part
                            
                            # Check if this column has PRIMARY KEY constraint
                            is_pk = 'PRIMARY KEY' in col_define.upper()
                            
                            table_columns.append((col_name, col_type, is_pk))
                    
                    # Only add if not already defined (avoid duplicates)
                    if table_columns and table_name not in expected_schema:
                        expected_schema[table_name] = table_columns
            
            except Exception:
                continue  # Skip unreadable files
                
        return expected_schema
    
    def _split_sql_fields(self, text: str) -> List[str]:
        """Split SQL field definitions respecting parentheses in constraints"""
        fields = []
        current_field = ""
        paren_depth = 0
        i = 0
        
        while i < len(text):
            char = text[i]
            if char == '(':
                paren_depth += 1
                current_field += char
            elif char == ')':
                paren_depth -= 1
                current_field += char
            elif char == ',' and paren_depth == 0:
                fields.append(current_field.strip())
                current_field = ""
            else:
                current_field += char
            i += 1
        
        if current_field.strip():
            fields.append(current_field.strip())
        
        return fields
    
    def analyze_code_usage(self) -> Dict[str, Dict[str, Set[str]]]:
        """Analyze all INSERT, UPDATE, SELECT statements for table/column usage"""
        usage_stats = {}
        
        # Look for all Python files in the codebase  
        py_files = list(Path(".").rglob("*.py"))
        
        for py_file in py_files:
            try:
                content = py_file.read_text()
                
                # Pattern 1: INSERT statements - capture table and potential columns
                insert_pattern = r'INSERT\s+INTO\s+(\w+)'
                for match in re.finditer(insert_pattern, content, re.IGNORECASE):
                    table_name = match.group(1)
                    
                    if table_name not in usage_stats:
                        usage_stats[table_name] = {
                            'insert_columns': set(),
                            'select_columns': set(),
                            'update_columns': set(),
                            'files': set(),
                            'occurrences': []
                        }
                    
                    # Look ahead for the column list in parentheses in INSERT
                    start_pos = match.start()
                    insert_match = re.search(rf'INSERT\s+INTO\s+{table_name}\s*\(([^)]+)\)', 
                                           content[start_pos:start_pos+200], 
                                           re.IGNORECASE)
                    if insert_match:
                        cols_text = insert_match.group(1)
                        col_names = [col.strip().strip('`"\'') for col in cols_text.split(',')]
                        for col in col_names:
                            if col and col != '':
                                usage_stats[table_name]['insert_columns'].add(col)
                    
                    usage_stats[table_name]['files'].add(str(py_file))
                
                # Pattern 2: SELECT statements - capture table and columns
                select_pattern = r'SELECT\s+(.+?)\s+FROM\s+(\w+)'
                for match in re.finditer(select_pattern, content, re.IGNORECASE | re.DOTALL):
                    col_part = match.group(1)
                    table_name = match.group(2)
                    
                    if table_name not in usage_stats:
                        usage_stats[table_name] = {
                            'insert_columns': set(),
                            'select_columns': set(),
                            'update_columns': set(),
                            'files': set(),
                            'occurrences': []
                        }
                    
                    # Extract column names from SELECT clause
                    if '*' in col_part:
                        usage_stats[table_name]['select_columns'].add('*')
                    else:
                        # Handle column names, possibly with table prefixes or functions
                        col_candidates = re.split(r'[,\s]+', col_part)
                        for col in col_candidates:
                            # Clean up: remove function calls, aliases, etc.
                            col = col.strip().strip('`"\'')
                            if col and not any(func in col.upper() for func in ['COUNT(', 'SUM(', 'AVG(', 'MAX(', 'MIN(', 'DISTINCT']):
                                # Extract just the column name part (before AS or any aliases)
                                col_clean = col.split(' as ')[0].split('.')[1] if '.' in col.split(' as ')[0] else col.split(' as ')[0]
                                col_clean = col_clean.split(' ')[0]  # Also handle cases like 'col_name AS alias'
                                if col_clean and col_clean.isidentifier():  # Basic check for valid identifier
                                    usage_stats[table_name]['select_columns'].add(col_clean)
                    
                    usage_stats[table_name]['files'].add(str(py_file))
                
                # Pattern 3: UPDATE statements
                update_pattern = r'UPDATE\s+(\w+)'
                for match in re.finditer(update_pattern, content, re.IGNORECASE):
                    table_name = match.group(1)
                    
                    if table_name not in usage_stats:
                        usage_stats[table_name] = {
                            'insert_columns': set(),
                            'select_columns': set(),
                            'update_columns': set(),
                            'files': set(),
                            'occurrences': []
                        }
                    
                    # Look for SET clause to find update columns in UPDATE statement
                    start_pos = match.start()
                    update_match = re.search(rf'UPDATE\s+{table_name}\s+SET\s+([^WHERE]+)', 
                                           content[start_pos:start_pos+300], 
                                           re.IGNORECASE | re.DOTALL)
                    if update_match:
                        set_clause = update_match.group(1)
                        # Extract column names from SET clause (col = value format)
                        assignments = re.findall(r'([`\'"]?[\w_]+[`\'"]?)\s*=', set_clause)
                        for col_name in assignments:
                            col_name_clean = col_name.strip('`"\'')
                            if col_name_clean and col_name_clean.isidentifier():
                                usage_stats[table_name]['update_columns'].add(col_name_clean)
                    
                    usage_stats[table_name]['files'].add(str(py_file))
                
                # Pattern 4: JOIN statements (additional table references)
                join_patterns = [
                    r'JOIN\s+(\w+)',
                    r'LEFT\s+JOIN\s+(\w+)',
                    r'RIGHT\s+JOIN\s+(\w+)',
                    r'INNER\s+JOIN\s+(\w+)'
                ]
                
                for jp in join_patterns:
                    for join_match in re.finditer(jp, content, re.IGNORECASE):
                        table_name = join_match.group(1)
                        
                        if table_name not in usage_stats:
                            usage_stats[table_name] = {
                                'insert_columns': set(),
                                'select_columns': set(),
                                'update_columns': set(),
                                'files': set(),
                                'occurrences': []
                            }
                        
                        usage_stats[table_name]['files'].add(str(py_file))
            
            except Exception:
                continue  # Skip unreadable files
        
        return usage_stats

    def compare_schema_and_usage(self, actual_schema: Dict[str, List[Tuple]], expected_schema: Dict[str, List[Tuple]], usage_stats: Dict[str, Dict]) -> Tuple[List[Dict], List[Dict]]:
        """Compare actual schema vs expected and usage patterns to find issues"""
        issues = []
        comparisons = []
        
        # Compare each table's actual vs expected schema and usage
        all_table_names = set(actual_schema.keys()) | set(expected_schema.keys())
        
        for table_name in all_table_names:
            actual_cols = {col[0] for col in actual_schema.get(table_name, [])}
            expected_cols = {col[0] for col in expected_schema.get(table_name, [])}
            
            # Find discrepancies
            extra_in_db = actual_cols - expected_cols
            missing_in_db = expected_cols - actual_cols
            
            # Also check if columns are used in code but don't exist in schema
            usage_cols = set()
            if table_name in usage_stats:
                usage_cols = (usage_stats[table_name]['insert_columns'] | 
                             usage_stats[table_name]['select_columns'] | 
                             usage_stats[table_name]['update_columns'])
                # Remove wildcard marker
                usage_cols.discard('*')
            
            used_but_not_in_db = usage_cols - actual_cols
            unused_in_db = actual_cols - usage_cols if table_name in usage_stats else set()
            
            if extra_in_db or missing_in_db or used_but_not_in_db or unused_in_db:
                comparison = {
                    'table': table_name,
                    'actual_columns': [col[0] for col in actual_schema.get(table_name, [])],
                    'expected_columns': [col[0] for col in expected_schema.get(table_name, [])],
                    'extra_in_db': list(extra_in_db),
                    'missing_in_db': list(missing_in_db),
                    'used_but_not_in_db': list(used_but_not_in_db),
                    'unused_in_db': list(unused_in_db),
                    'actual_count': len(actual_cols),
                    'expected_count': len(expected_cols),
                    'used_columns_count': len(usage_cols)
                }
                
                comparisons.append(comparison)
                
                # Add specific issues
                for col in extra_in_db:
                    issues.append({
                        'type': 'extra_column_in_db',
                        'table': table_name,
                        'column': col,
                        'severity': 'info',
                        'message': f'Column "{col}" exists in database but not defined in CREATE TABLE statement'
                    })
                
                for col in missing_in_db:
                    issues.append({
                        'type': 'missing_column_in_db',
                        'table': table_name,
                        'column': col,
                        'severity': 'critical',
                        'message': f'Column "{col}" defined in CREATE TABLE but missing from database schema'
                    })
                
                for col in used_but_not_in_db:
                    issues.append({
                        'type': 'used_column_not_in_schema',
                        'table': table_name,
                        'column': col,
                        'severity': 'critical',
                        'message': f'Column "{col}" referenced in code but not present in database schema'
                    })
                
                for col in unused_in_db:
                    issues.append({
                        'type': 'unused_column_in_db',
                        'table': table_name,
                        'column': col,
                        'severity': 'warning',
                        'message': f'Column "{col}" exists in schema but not actively used in code'
                    })
        
        return issues, comparisons
    
    def generate_report(self, actual_schema: Dict[str, List[Tuple]], expected_schema: Dict[str, List[Tuple]], usage_stats: Dict[str, Dict], issues: List[Dict], comparisons: List[Dict]) -> str:
        """Generate formatted validation report"""
        report_lines = [
            "EMPIRICA SCHEMA VALIDATION REPORT",
            "=================================",
            ""
        ]
        
        # Summary
        total_tables = len(actual_schema)
        total_issues = len(issues)
        
        report_lines.append(f"📊 DATABASE OVERVIEW:")
        report_lines.append(f"   • Total tables in database: {total_tables}")
        report_lines.append(f"   • Schema definitions in code: {len(expected_schema)}")
        report_lines.append(f"   • Code usage patterns found: {len(usage_stats)} tables")
        report_lines.append(f"   • Issues found: {total_issues}")
        report_lines.append(f"   • Tables with schema mismatches: {len([c for c in comparisons if c['extra_in_db'] or c['missing_in_db'] or c['used_but_not_in_db']])}")
        report_lines.append("")
        
        # Issues summary by severity
        critical_issues = [i for i in issues if i['severity'] == 'critical']
        warning_issues = [i for i in issues if i['severity'] == 'warning']
        info_issues = [i for i in issues if i['severity'] == 'info']
        
        if critical_issues:
            report_lines.append(f"🚨 CRITICAL ISSUES ({len(critical_issues)}):")
            for issue in critical_issues:
                report_lines.append(f"   • [{issue['table']}::{issue['column']}] {issue['message']}")
            report_lines.append("")
        
        if warning_issues:
            report_lines.append(f"⚠️  WARNINGS ({len(warning_issues)}):")
            for issue in warning_issues:
                report_lines.append(f"   • [{issue['table']}::{issue['column']}] {issue['message']}")
            report_lines.append("")
        
        if info_issues:
            report_lines.append(f"ℹ️  INFORMATIONAL ({len(info_issues)}):")
            for issue in info_issues:
                report_lines.append(f"   • [{issue['table']}::{issue['column']}] {issue['message']}")
            report_lines.append("")
        
        # Issues detailed breakdown
        if issues:
            report_lines.append("❌ DETAILED ISSUES:")
            for issue in issues:
                if issue['severity'] == 'critical':
                    severity_icon = "🚨"
                elif issue['severity'] == 'warning':
                    severity_icon = "⚠️"
                else:
                    severity_icon = "ℹ️"
                
                report_lines.append(f"   {severity_icon} {issue['table']}.{issue['column']}")
                report_lines.append(f"      Type: {issue['type']}")
                report_lines.append(f"      Severity: {issue['severity']}")
                report_lines.append(f"      {issue['message']}")
                if issue['table'] in usage_stats:
                    files_using = usage_stats[issue['table']]['files']
                    report_lines.append(f"      Used in: {len(files_using)} files")
                report_lines.append("")
        else:
            report_lines.append("✅ No schema issues detected!")
            report_lines.append("")
        
        # Schema details
        report_lines.append("📋 SCHEMA DETAILS:")
        for table_name in sorted(actual_schema.keys()):
            columns = actual_schema[table_name]
            report_lines.append(f"   {table_name} ({len(columns)} columns):")
            
            # Show column usage
            table_usage = usage_stats.get(table_name, {})
            used_cols = set()
            if table_usage:
                used_cols = (table_usage.get('insert_columns', set()) | 
                            table_usage.get('select_columns', set()) | 
                            table_usage.get('update_columns', set()))
                used_cols.discard('*')  # Remove wildcard marker
            
            for col_name, col_type, is_pk in columns:
                pk_marker = " [PK]" if is_pk else ""
                usage_marker = " ✓" if col_name in used_cols else " ○"  # Check mark for used, circle for unused
                report_lines.append(f"     - {col_name} ({col_type}){pk_marker}{usage_marker}")
            
            # Show usage stats
            usage_count = 0
            if table_name in usage_stats:
                usage_count = len(table_usage.get('files', set()))
            
            report_lines.append(f"       Code references: {usage_count} files")
            report_lines.append("")
        
        # Comparison summary for tables with issues
        problematic_comparisons = [c for c in comparisons if c['extra_in_db'] or c['missing_in_db'] or c['used_but_not_in_db']]
        if problematic_comparisons:
            report_lines.append("🔍 COMPARISON SUMMARY (Tables with Issues):")
            for comp in problematic_comparisons:
                report_lines.append(f"   {comp['table']}:")
                if comp['missing_in_db']:
                    report_lines.append(f"     • Missing in DB (defined in code): {', '.join(comp['missing_in_db'])}")
                if comp['extra_in_db']: 
                    report_lines.append(f"     • Extra in DB (not in code): {', '.join(comp['extra_in_db'])}")
                if comp['used_but_not_in_db']:
                    report_lines.append(f"     • Used in code but not in schema: {', '.join(comp['used_but_not_in_db'])}")
                if comp['unused_in_db']:
                    report_lines.append(f"     • Unused in code: {', '.join(comp['unused_in_db'])}")
                
                report_lines.append(f"       Schema: {comp['actual_count']} actual vs {comp['expected_count']} expected")
                report_lines.append("")
        else:
            report_lines.append("✅ All table schemas align between code and database")
        
        return "\n".join(report_lines)

    def run_validation(self) -> Dict:
        """Run comprehensive schema validation"""
        print("🔍 Starting Empirica Schema Validation...")
        
        # Get actual database schema
        print("📋 Getting actual database schema...")
        actual_schema = self.get_actual_schema()
        print(f"   Found {len(actual_schema)} tables")
        
        # Get expected schema from code
        print("📝 Getting expected schema from code...")
        expected_schema = self.get_expected_schema_from_code()
        print(f"   Found {len(expected_schema)} tables defined in code")
        
        # Analyze code usage of tables/columns
        print("🔍 Analyzing code usage patterns...")
        usage_stats = self.analyze_code_usage()
        print(f"   Found usage patterns across {len(usage_stats)} tables")
        
        # Compare schemas and usage patterns
        print("🔍 Comparing schemas and code usage...")
        issues, comparisons = self.compare_schema_and_usage(actual_schema, expected_schema, usage_stats)
        
        # Generate comprehensive report
        print("📊 Generating validation report...")
        report = self.generate_report(actual_schema, expected_schema, usage_stats, issues, comparisons)
        
        return {
            'report': report,
            'issues': issues,
            'comparisons': comparisons,
            'actual_schema': actual_schema,
            'expected_schema': expected_schema,
            'code_usage': usage_stats
        }


def main():
    """Main entry point"""
    print("🚀 Starting Empirica Schema Validation Tool")
    
    # Check for the database file in common locations
    db_paths = [
        Path(".empirica/sessions/sessions.db"),
        Path(".empirica/sessions.db"),
        Path("sessions.db")
    ]
    
    db_path = None
    for path in db_paths:
        if path.exists():
            db_path = path
            break
    
    if not db_path:
        print(f"❌ Database not found at common locations:")
        for p in db_paths:
            print(f"   - {p.absolute()}")
        print("   Is this an Empirica project directory?")
        return 1
    
    print(f"   Database: {db_path.absolute()}")
    
    try:
        validator = SchemaValidator(str(db_path))
        result = validator.run_validation()
    except Exception as e:
        print(f"❌ Error during validation: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    # Print report to console
    print("\n" + result['report'])
    
    # Save detailed report
    report_path = Path('schema_validation_report.txt')
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("EMPIRICA SCHEMA VALIDATION REPORT\n")
        f.write("=================================\n\n")
        f.write(result['report'])
        f.write("\n\nDETAILED ANALYSIS DATA:\n")
        f.write(f"Issues found: {len(result['issues'])}\n")
        f.write(f"Comparisons with differences: {len([c for c in result['comparisons'] if c['extra_in_db'] or c['missing_in_db'] or c['used_but_not_in_db']])}\n")
        
        f.write(f"\nActual schema structure:\n")
        for table, columns in result['actual_schema'].items():
            f.write(f"  {table}: {len(columns)} columns\n")
        
        f.write(f"\nExpected schema from code:\n")  
        for table, columns in result['expected_schema'].items():
            f.write(f"  {table}: {len(columns)} columns\n")
        
        f.write(f"\nCode usage patterns:\n")
        for table, usage in result['code_usage'].items():
            total_refs = len(usage.get('files', set()))
            f.write(f"  {table}: referenced in {total_refs} files\n")
    
    print(f"\n💾 Full report saved to: {report_path.absolute()}")
    
    # Return exit code based on findings
    all_issues = result['issues']
    critical_issues = [i for i in all_issues if i['severity'] == 'critical']
    
    if critical_issues:
        print(f"\n🚨 Found {len(critical_issues)} CRITICAL schema issues that need fixing!")
        return 1
    elif all_issues:
        print(f"\n⚠️  Found {len(all_issues)} potential schema issues to investigate")
        return 0  # Warn but don't fail
    else:
        print(f"\n✅ Schema validation complete - no issues detected!")
        return 0


if __name__ == "__main__":
    exit(main())