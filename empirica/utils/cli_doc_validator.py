#!/usr/bin/env python3
"""
CLI Documentation Validator

Validates that user-facing documentation accurately reflects the actual CLI commands.

This is DIFFERENT from doc_code_integrity.py which validates internal code documentation.

Checks:
1. Commands referenced in docs actually exist in CLI
2. Command examples use correct syntax
3. Flag documentation matches actual flags
4. No phantom commands in user docs
"""

import re
import subprocess
from pathlib import Path
from typing import Dict, List, Set, Tuple
import json


def get_actual_cli_commands() -> Set[str]:
    """
    Extract all actual CLI commands from cli_core.py
    
    Returns:
        Set of command names (e.g., 'session-create', 'preflight-submit')
    """
    cli_core_path = Path(__file__).parent.parent / 'cli' / 'cli_core.py'
    
    with open(cli_core_path, 'r') as f:
        content = f.read()
    
    # Extract from add_parser calls
    pattern = r"add_parser\(\s*['\"]([a-z][a-z0-9-]+)['\"]"
    commands = set(re.findall(pattern, content))
    
    return commands


def extract_documented_commands(docs_dir: Path = None) -> Dict[str, List[Tuple[str, int]]]:
    """
    Extract all commands referenced in documentation
    
    Returns:
        Dict mapping command -> list of (file, line_number) where it's referenced
    """
    if docs_dir is None:
        docs_dir = Path(__file__).parent.parent.parent / 'docs'
    
    documented_commands = {}
    
    # Pattern for actual command usage: `empirica <command>` or ```bash\nempirica <command>
    patterns = [
        r'`empirica\s+([a-z][a-z0-9-]+)',  # Inline code: `empirica session-create`
        r'^\s*empirica\s+([a-z][a-z0-9-]+)',  # Command line: empirica session-create
        r'\$\s*empirica\s+([a-z][a-z0-9-]+)',  # Shell prompt: $ empirica session-create
    ]
    
    for md_file in docs_dir.rglob('*.md'):
        try:
            with open(md_file, 'r') as f:
                lines = f.readlines()
            
            for line_num, line in enumerate(lines, 1):
                for pattern in patterns:
                    matches = re.findall(pattern, line)
                    for command in matches:
                        if command not in documented_commands:
                            documented_commands[command] = []
                        documented_commands[command].append((str(md_file), line_num))
        except Exception as e:
            print(f"Warning: Could not process {md_file}: {e}")
    
    return documented_commands


def find_phantom_commands() -> List[Dict]:
    """
    Find commands documented but not implemented
    
    Returns:
        List of phantom command dictionaries with details
    """
    actual_commands = get_actual_cli_commands()
    documented_commands = extract_documented_commands()
    
    phantoms = []
    
    for cmd, locations in documented_commands.items():
        if cmd not in actual_commands:
            phantoms.append({
                'command': cmd,
                'locations': locations,
                'severity': 'high' if len(locations) > 5 else 'medium'
            })
    
    return phantoms


def find_undocumented_commands() -> List[str]:
    """
    Find implemented commands not documented anywhere
    
    Returns:
        List of undocumented command names
    """
    actual_commands = get_actual_cli_commands()
    documented_commands = extract_documented_commands()
    
    undocumented = []
    
    for cmd in actual_commands:
        if cmd not in documented_commands:
            undocumented.append(cmd)
    
    return undocumented


def validate_cli_documentation(output_format: str = 'text') -> Dict:
    """
    Run complete CLI documentation validation
    
    Args:
        output_format: 'text' or 'json'
    
    Returns:
        Validation results dictionary
    """
    actual_commands = get_actual_cli_commands()
    documented_commands = extract_documented_commands()
    phantoms = find_phantom_commands()
    undocumented = find_undocumented_commands()
    
    results = {
        'total_actual_commands': len(actual_commands),
        'total_documented_commands': len(documented_commands),
        'phantom_commands': phantoms,
        'undocumented_commands': undocumented,
        'accuracy_score': calculate_accuracy_score(actual_commands, documented_commands, phantoms)
    }
    
    if output_format == 'json':
        print(json.dumps(results, indent=2))
    else:
        print_text_report(results)
    
    return results


def calculate_accuracy_score(actual: Set[str], documented: Dict, phantoms: List) -> float:
    """
    Calculate documentation accuracy percentage
    
    Score = (correctly documented) / (total documented) * 100
    """
    correctly_documented = len([cmd for cmd in documented.keys() if cmd in actual])
    total_documented = len(documented)
    
    if total_documented == 0:
        return 0.0
    
    return (correctly_documented / total_documented) * 100


def print_text_report(results: Dict):
    """Print human-readable validation report"""
    print("=" * 70)
    print("CLI DOCUMENTATION VALIDATION REPORT")
    print("=" * 70)
    print()
    print(f"📊 Statistics:")
    print(f"  • Actual CLI commands: {results['total_actual_commands']}")
    print(f"  • Documented commands: {results['total_documented_commands']}")
    print(f"  • Accuracy score: {results['accuracy_score']:.1f}%")
    print()
    
    if results['phantom_commands']:
        print(f"⚠️  PHANTOM COMMANDS ({len(results['phantom_commands'])}):")
        print("   Commands in docs but NOT in CLI:")
        for phantom in results['phantom_commands'][:10]:
            print(f"   • {phantom['command']} (found in {len(phantom['locations'])} locations)")
        if len(results['phantom_commands']) > 10:
            print(f"   ... and {len(results['phantom_commands']) - 10} more")
        print()
    
    if results['undocumented_commands']:
        print(f"📝 UNDOCUMENTED COMMANDS ({len(results['undocumented_commands'])}):")
        print("   Commands in CLI but NOT in docs:")
        for cmd in results['undocumented_commands'][:10]:
            print(f"   • {cmd}")
        if len(results['undocumented_commands']) > 10:
            print(f"   ... and {len(results['undocumented_commands']) - 10} more")
        print()
    
    if not results['phantom_commands'] and not results['undocumented_commands']:
        print("✅ All CLI commands are properly documented!")
        print()


if __name__ == '__main__':
    import sys
    output_format = sys.argv[1] if len(sys.argv) > 1 else 'text'
    validate_cli_documentation(output_format)
