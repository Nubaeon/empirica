#!/usr/bin/env python3
"""
Fix Phantom Commands in Documentation

Removes or updates references to removed/renamed commands:
- profile-* commands (removed feature)
- assess, cascade, decision (old names)
- goals → goals-list
- bootstrap-system → project-bootstrap
- etc.
"""

import sys
sys.path.insert(0, '/home/yogapad/empirical-ai/empirica')

from empirica.utils.cli_doc_validator import validate_cli_documentation
import json

def main():
    print("Running CLI documentation validator...")
    results = validate_cli_documentation(output_format='json')
    
    # Parse results
    data = json.loads(results) if isinstance(results, str) else results
    
    phantoms = data.get('phantom_commands', [])
    
    print(f"\nFound {len(phantoms)} phantom commands")
    print("\nRECOMMENDED ACTIONS:")
    print("\n1. PROFILE COMMANDS (removed feature - archive these docs):")
    for phantom in phantoms:
        if 'profile' in phantom['command']:
            print(f"   • {phantom['command']}: Found in {len(phantom['locations'])} files")
            for file, line in phantom['locations'][:3]:
                print(f"     - {file}:{line}")
    
    print("\n2. RENAMED COMMANDS (update to new names):")
    renames = {
        'goals': 'goals-list',
        'bootstrap-system': 'project-bootstrap',
        'assess': 'CHECK phase (part of CASCADE)',
        'cascade': 'CASCADE workflow (PREFLIGHT/CHECK/POSTFLIGHT)',
        'decision': 'CHECK phase decision',
    }
    for phantom in phantoms:
        cmd = phantom['command']
        if cmd in renames:
            print(f"   • {cmd} → {renames[cmd]}")
            for file, line in phantom['locations'][:2]:
                print(f"     - {file}:{line}")
    
    print("\n3. TYPOS/MISTAKES (remove or clarify):")
    typos = ['command-name', 'migrate', 'install-prompt', 'monitor-export']
    for phantom in phantoms:
        if phantom['command'] in typos:
            print(f"   • {phantom['command']}")
            for file, line in phantom['locations']:
                print(f"     - {file}:{line}")
    
    print("\n✅ CURRENT ACCURACY: {:.1f}%".format(data.get('accuracy_score', 0)))
    print("🎯 TARGET: >95% (fix these 16 phantoms)")
    
if __name__ == '__main__':
    main()
