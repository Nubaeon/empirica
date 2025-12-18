#!/usr/bin/env python3
"""
Code Pattern Extractor - Parse Python code to extract patterns

Extracts:
- Classes (names, docstrings, methods)
- Functions (names, params, returns, docstrings)
- Imports (dependencies)
- Decorators (behaviors)
- Database schema (SQLAlchemy models)
- CLI commands (Click decorators)
- MCP tools (function signatures)

Output: code_patterns.json
"""

import ast
import json
from pathlib import Path
from typing import Dict, List, Set, Any
from dataclasses import dataclass, asdict
from collections import defaultdict


@dataclass
class FunctionPattern:
    name: str
    module: str
    params: List[str]
    returns: str
    docstring: str
    decorators: List[str]
    calls: List[str]  # Functions this calls
    line_number: int


@dataclass
class ClassPattern:
    name: str
    module: str
    docstring: str
    methods: List[str]
    bases: List[str]
    decorators: List[str]
    line_number: int


@dataclass
class ImportPattern:
    module: str
    names: List[str]
    source_file: str


@dataclass
class DatabasePattern:
    table_name: str
    columns: List[Dict[str, str]]  # [{"name": "id", "type": "String"}]
    module: str


@dataclass
class CLICommandPattern:
    name: str
    params: List[Dict[str, str]]  # [{"name": "session-id", "type": "str"}]
    help_text: str
    module: str


class CodePatternExtractor:
    def __init__(self, root_dir: Path):
        self.root_dir = root_dir
        self.functions: Dict[str, FunctionPattern] = {}
        self.classes: Dict[str, ClassPattern] = {}
        self.imports: List[ImportPattern] = []
        self.db_tables: Dict[str, DatabasePattern] = {}
        self.cli_commands: Dict[str, CLICommandPattern] = {}
        self.call_graph: Dict[str, Set[str]] = defaultdict(set)
        
    def extract_all(self) -> Dict[str, Any]:
        """Extract patterns from all Python files"""
        print("🔍 Extracting code patterns...")
        
        py_files = list(self.root_dir.glob("empirica/**/*.py"))
        py_files = [f for f in py_files if "__pycache__" not in str(f)]
        
        for i, py_file in enumerate(py_files, 1):
            if i % 10 == 0:
                print(f"  Processed {i}/{len(py_files)} files...")
            self._extract_from_file(py_file)
        
        print(f"✅ Extracted {len(self.functions)} functions, {len(self.classes)} classes")
        
        return {
            "functions": {k: asdict(v) for k, v in self.functions.items()},
            "classes": {k: asdict(v) for k, v in self.classes.items()},
            "imports": [asdict(i) for i in self.imports],
            "db_tables": {k: asdict(v) for k, v in self.db_tables.items()},
            "cli_commands": {k: asdict(v) for k, v in self.cli_commands.items()},
            "call_graph": {k: list(v) for k, v in self.call_graph.items()},
        }
    
    def _extract_from_file(self, filepath: Path):
        """Extract patterns from single file"""
        try:
            content = filepath.read_text()
            tree = ast.parse(content)
            module_name = str(filepath.relative_to(self.root_dir)).replace("/", ".").replace(".py", "")
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    self._extract_function(node, module_name)
                elif isinstance(node, ast.ClassDef):
                    self._extract_class(node, module_name)
                elif isinstance(node, ast.Import) or isinstance(node, ast.ImportFrom):
                    self._extract_import(node, module_name)
        except Exception as e:
            print(f"⚠️  Error parsing {filepath}: {e}")
    
    def _extract_function(self, node: ast.FunctionDef, module: str):
        """Extract function pattern"""
        # Get parameters
        params = [arg.arg for arg in node.args.args]
        
        # Get return type
        returns = ""
        if node.returns:
            returns = ast.unparse(node.returns) if hasattr(ast, 'unparse') else ""
        
        # Get docstring
        docstring = ast.get_docstring(node) or ""
        
        # Get decorators
        decorators = []
        for dec in node.decorator_list:
            if isinstance(dec, ast.Name):
                decorators.append(dec.id)
            elif isinstance(dec, ast.Call) and isinstance(dec.func, ast.Name):
                decorators.append(dec.func.id)
        
        # Extract function calls
        calls = []
        for child in ast.walk(node):
            if isinstance(child, ast.Call):
                if isinstance(child.func, ast.Name):
                    calls.append(child.func.id)
                elif isinstance(child.func, ast.Attribute):
                    calls.append(child.func.attr)
        
        func_key = f"{module}.{node.name}"
        self.functions[func_key] = FunctionPattern(
            name=node.name,
            module=module,
            params=params,
            returns=returns,
            docstring=docstring[:200],  # Truncate long docstrings
            decorators=decorators,
            calls=list(set(calls)),
            line_number=node.lineno
        )
        
        # Build call graph
        self.call_graph[func_key].update(calls)
        
        # Check for CLI commands
        if "click.command" in decorators or "command" in decorators:
            self._extract_cli_command(node, module)
    
    def _extract_class(self, node: ast.ClassDef, module: str):
        """Extract class pattern"""
        docstring = ast.get_docstring(node) or ""
        
        # Get methods
        methods = [n.name for n in node.body if isinstance(n, ast.FunctionDef)]
        
        # Get base classes
        bases = []
        for base in node.bases:
            if isinstance(base, ast.Name):
                bases.append(base.id)
            elif isinstance(base, ast.Attribute):
                bases.append(base.attr)
        
        # Get decorators
        decorators = []
        for dec in node.decorator_list:
            if isinstance(dec, ast.Name):
                decorators.append(dec.id)
        
        class_key = f"{module}.{node.name}"
        self.classes[class_key] = ClassPattern(
            name=node.name,
            module=module,
            docstring=docstring[:200],
            methods=methods,
            bases=bases,
            decorators=decorators,
            line_number=node.lineno
        )
        
        # Check for SQLAlchemy models
        if "Base" in bases or any("declarative_base" in str(b).lower() for b in bases):
            self._extract_db_table(node, module)
    
    def _extract_import(self, node, module: str):
        """Extract import pattern"""
        if isinstance(node, ast.Import):
            for alias in node.names:
                self.imports.append(ImportPattern(
                    module=alias.name,
                    names=[alias.asname or alias.name],
                    source_file=module
                ))
        elif isinstance(node, ast.ImportFrom):
            module_name = node.module or ""
            names = [alias.name for alias in node.names]
            self.imports.append(ImportPattern(
                module=module_name,
                names=names,
                source_file=module
            ))
    
    def _extract_db_table(self, node: ast.ClassDef, module: str):
        """Extract database table pattern from SQLAlchemy model"""
        # Look for __tablename__
        table_name = None
        for item in node.body:
            if isinstance(item, ast.Assign):
                for target in item.targets:
                    if isinstance(target, ast.Name) and target.id == "__tablename__":
                        if isinstance(item.value, ast.Constant):
                            table_name = item.value.value
        
        if not table_name:
            return
        
        # Extract columns
        columns = []
        for item in node.body:
            if isinstance(item, ast.Assign):
                for target in item.targets:
                    if isinstance(target, ast.Name) and isinstance(item.value, ast.Call):
                        if hasattr(item.value.func, 'attr') and item.value.func.attr == "Column":
                            col_type = ""
                            if item.value.args:
                                arg = item.value.args[0]
                                if isinstance(arg, ast.Name):
                                    col_type = arg.id
                                elif isinstance(arg, ast.Call) and isinstance(arg.func, ast.Name):
                                    col_type = arg.func.id
                            
                            columns.append({
                                "name": target.id,
                                "type": col_type
                            })
        
        self.db_tables[table_name] = DatabasePattern(
            table_name=table_name,
            columns=columns,
            module=module
        )
    
    def _extract_cli_command(self, node: ast.FunctionDef, module: str):
        """Extract CLI command pattern"""
        # Look for @click.option decorators
        params = []
        for dec in node.decorator_list:
            if isinstance(dec, ast.Call):
                if (isinstance(dec.func, ast.Attribute) and 
                    dec.func.attr == "option"):
                    if dec.args and isinstance(dec.args[0], ast.Constant):
                        param_name = dec.args[0].value
                        param_type = "str"  # Default
                        
                        # Try to get type from keywords
                        for kw in dec.keywords:
                            if kw.arg == "type":
                                if isinstance(kw.value, ast.Name):
                                    param_type = kw.value.id
                        
                        params.append({
                            "name": param_name,
                            "type": param_type
                        })
        
        self.cli_commands[node.name] = CLICommandPattern(
            name=node.name,
            params=params,
            help_text=ast.get_docstring(node) or "",
            module=module
        )


def main():
    root_dir = Path("/home/yogapad/empirical-ai/empirica")
    extractor = CodePatternExtractor(root_dir)
    patterns = extractor.extract_all()
    
    output_file = root_dir / "dev_scripts/doc_pattern_matcher/code_patterns.json"
    output_file.write_text(json.dumps(patterns, indent=2))
    
    print(f"\n✅ Code patterns saved to: {output_file}")
    print(f"   Functions: {len(patterns['functions'])}")
    print(f"   Classes: {len(patterns['classes'])}")
    print(f"   DB Tables: {len(patterns['db_tables'])}")
    print(f"   CLI Commands: {len(patterns['cli_commands'])}")
    print(f"   Imports: {len(patterns['imports'])}")


if __name__ == "__main__":
    main()
