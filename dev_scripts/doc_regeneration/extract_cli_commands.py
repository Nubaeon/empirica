#!/usr/bin/env python3
"""
CLI Command Extractor - Extract command structure from cli_core.py

Parses the argparse command definitions and extracts:
- Command names
- Help text
- Arguments (required/optional)
- Argument types and defaults
- Handler functions

Output: JSON structure of all commands
"""

import ast
import json
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional


class CLICommandExtractor(ast.NodeVisitor):
    """Extract command definitions from cli_core.py AST"""
    
    def __init__(self):
        self.commands = []
        self.current_command = None
        self.in_add_parser = False
        
    def visit_Call(self, node):
        """Visit function calls to find add_parser and add_argument calls"""
        
        # Detect: subparsers.add_parser('command-name', help='...')
        if (hasattr(node.func, 'attr') and 
            node.func.attr == 'add_parser' and
            node.args):
            
            command_name = self._get_string_value(node.args[0])
            if command_name:
                self.current_command = {
                    'name': command_name,
                    'help': '',
                    'arguments': [],
                    'handler': None
                }
                
                # Extract help text
                for keyword in node.keywords:
                    if keyword.arg == 'help':
                        self.current_command['help'] = self._get_string_value(keyword.value)
                
                self.commands.append(self.current_command)
        
        # Detect: parser.add_argument('--flag', ...)
        elif (hasattr(node.func, 'attr') and 
              node.func.attr == 'add_argument' and
              self.current_command and
              node.args):
            
            arg_name = self._get_string_value(node.args[0])
            if arg_name:
                arg_info = {
                    'name': arg_name,
                    'required': False,
                    'type': 'string',
                    'default': None,
                    'help': '',
                    'choices': None
                }
                
                # Extract argument properties
                for keyword in node.keywords:
                    if keyword.arg == 'required':
                        arg_info['required'] = self._get_bool_value(keyword.value)
                    elif keyword.arg == 'help':
                        arg_info['help'] = self._get_string_value(keyword.value)
                    elif keyword.arg == 'default':
                        arg_info['default'] = self._get_value(keyword.value)
                    elif keyword.arg == 'type':
                        arg_info['type'] = self._get_type_name(keyword.value)
                    elif keyword.arg == 'choices':
                        arg_info['choices'] = self._get_list_value(keyword.value)
                    elif keyword.arg == 'action':
                        action = self._get_string_value(keyword.value)
                        if action == 'store_true':
                            arg_info['type'] = 'flag'
                            arg_info['default'] = False
                        elif action == 'store_false':
                            arg_info['type'] = 'flag'
                            arg_info['default'] = True
                
                self.current_command['arguments'].append(arg_info)
        
        self.generic_visit(node)
    
    def _get_string_value(self, node) -> Optional[str]:
        """Extract string value from AST node"""
        if isinstance(node, ast.Constant):
            return str(node.value) if node.value else None
        elif isinstance(node, ast.Str):  # Python < 3.8
            return node.s
        return None
    
    def _get_bool_value(self, node) -> bool:
        """Extract boolean value from AST node"""
        if isinstance(node, ast.Constant):
            return bool(node.value)
        elif isinstance(node, ast.NameConstant):  # Python < 3.8
            return bool(node.value)
        return False
    
    def _get_value(self, node) -> Any:
        """Extract generic value from AST node"""
        if isinstance(node, ast.Constant):
            return node.value
        elif isinstance(node, ast.Num):  # Python < 3.8
            return node.n
        elif isinstance(node, ast.Str):  # Python < 3.8
            return node.s
        elif isinstance(node, ast.NameConstant):  # Python < 3.8
            return node.value
        return None
    
    def _get_type_name(self, node) -> str:
        """Extract type name from AST node"""
        if isinstance(node, ast.Name):
            type_map = {
                'int': 'integer',
                'float': 'float',
                'str': 'string',
                'bool': 'boolean'
            }
            return type_map.get(node.id, node.id)
        return 'string'
    
    def _get_list_value(self, node) -> Optional[List]:
        """Extract list value from AST node"""
        if isinstance(node, ast.List):
            return [self._get_string_value(elt) for elt in node.elts]
        return None


def extract_command_handlers(cli_core_path: Path) -> Dict[str, str]:
    """Extract command to handler mapping from main() function"""
    with open(cli_core_path) as f:
        tree = ast.parse(f.read())
    
    handlers = {}
    
    # Find the command_handlers dictionary
    for node in ast.walk(tree):
        if isinstance(node, ast.Dict):
            # Look for dictionary with command names as keys
            for key, value in zip(node.keys, node.values):
                if isinstance(key, ast.Constant) and isinstance(key.value, str):
                    cmd_name = key.value
                    if isinstance(value, ast.Name):
                        handlers[cmd_name] = value.id
    
    return handlers


def extract_cli_commands(cli_core_path: Path) -> List[Dict]:
    """Main extraction function"""
    
    print(f"📖 Parsing {cli_core_path}...")
    
    with open(cli_core_path) as f:
        tree = ast.parse(f.read())
    
    # Extract command structure
    extractor = CLICommandExtractor()
    extractor.visit(tree)
    
    # Extract handler mappings
    handlers = extract_command_handlers(cli_core_path)
    
    # Link handlers to commands
    for cmd in extractor.commands:
        cmd['handler'] = handlers.get(cmd['name'], 'unknown')
    
    print(f"✅ Extracted {len(extractor.commands)} commands")
    
    return extractor.commands


def group_commands_by_category(commands: List[Dict]) -> Dict[str, List[Dict]]:
    """Group commands by logical category"""
    
    categories = {
        'Session Management': [],
        'CASCADE Workflow': [],
        'Goals & Tasks': [],
        'Investigation': [],
        'Project Tracking': [],
        'Checkpoints & Handoffs': [],
        'Identity & Security': [],
        'Configuration': [],
        'Monitoring': [],
        'Utilities': []
    }
    
    # Categorization rules
    for cmd in commands:
        name = cmd['name']
        if name.startswith('session'):
            categories['Session Management'].append(cmd)
        elif name in ['preflight', 'preflight-submit', 'check', 'check-submit', 
                      'postflight', 'postflight-submit', 'workflow']:
            categories['CASCADE Workflow'].append(cmd)
        elif name.startswith('goals-'):
            categories['Goals & Tasks'].append(cmd)
        elif name.startswith('investigate-') or name in ['investigate', 'act-log', 'investigate-log']:
            categories['Investigation'].append(cmd)
        elif name.startswith('project-') or name in ['finding-log', 'unknown-log', 'deadend-log', 'refdoc-add']:
            categories['Project Tracking'].append(cmd)
        elif name.startswith('checkpoint-') or name.startswith('handoff-'):
            categories['Checkpoints & Handoffs'].append(cmd)
        elif name.startswith('identity-'):
            categories['Identity & Security'].append(cmd)
        elif name.startswith('config') or name == 'monitor':
            categories['Configuration'].append(cmd)
        elif name.startswith('check-') or name.startswith('monitor'):
            categories['Monitoring'].append(cmd)
        else:
            categories['Utilities'].append(cmd)
    
    # Remove empty categories
    return {k: v for k, v in categories.items() if v}


def main():
    """Main entry point"""
    
    # Find cli_core.py
    cli_core_path = Path(__file__).parent.parent.parent / 'empirica' / 'cli' / 'cli_core.py'
    
    if not cli_core_path.exists():
        print(f"❌ Error: {cli_core_path} not found")
        sys.exit(1)
    
    # Extract commands
    commands = extract_cli_commands(cli_core_path)
    
    # Group by category
    categorized = group_commands_by_category(commands)
    
    # Output JSON
    output = {
        'total_commands': len(commands),
        'extraction_date': '2025-12-16',
        'source_file': str(cli_core_path),
        'commands': commands,
        'categorized': categorized
    }
    
    output_path = Path(__file__).parent / 'cli_commands_extracted.json'
    with open(output_path, 'w') as f:
        json.dump(output, f, indent=2)
    
    print(f"\n✅ Saved to: {output_path}")
    print(f"\n📊 Summary:")
    print(f"   Total commands: {len(commands)}")
    print(f"   Categories: {len(categorized)}")
    for category, cmds in categorized.items():
        print(f"   - {category}: {len(cmds)} commands")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
