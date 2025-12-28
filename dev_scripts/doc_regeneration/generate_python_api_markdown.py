#!/usr/bin/env python3
"""
Python API Markdown Generator - Generate documentation from extracted Python API

Reads python_api_extracted.json and generates comprehensive markdown documentation.
"""

import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List


def format_parameter(param: Dict) -> str:
    """Format a parameter for display"""
    name = param['name']
    param_type = param['type']
    default = param['default']
    required = param['required']
    
    if required:
        return f"`{name}: {param_type}`"
    else:
        return f"`{name}: {param_type} = {default}`"


def format_method(method: Dict) -> str:
    """Format a method section"""
    lines = []
    
    # Method header
    lines.append(f"#### `{method['name']}{method['signature']}`")
    lines.append("")
    
    # Docstring
    if method['docstring']:
        # Format docstring with proper indentation
        docstring_lines = method['docstring'].split('\n')
        for line in docstring_lines:
            lines.append(line)
        lines.append("")
    
    # Parameters
    if method['parameters']:
        lines.append("**Parameters:**")
        lines.append("")
        for param in method['parameters']:
            lines.append(f"- {format_parameter(param)}")
        lines.append("")
    
    # Return type
    if method['return_type'] and method['return_type'] != 'Any':
        lines.append(f"**Returns:** `{method['return_type']}`")
        lines.append("")
    
    return "\n".join(lines)


def format_class(cls: Dict, module_path: str) -> str:
    """Format a class section"""
    lines = []
    
    # Class header
    lines.append(f"### `{cls['name']}`")
    lines.append("")
    lines.append(f"**Module:** `{module_path}`")
    lines.append("")
    
    # Class docstring
    if cls['docstring']:
        docstring_lines = cls['docstring'].split('\n')
        for line in docstring_lines:
            lines.append(line)
        lines.append("")
    
    # Properties
    if cls['properties']:
        lines.append("**Properties:**")
        lines.append("")
        for prop in cls['properties']:
            lines.append(f"- `{prop['name']}`")
            if prop['docstring']:
                lines.append(f"  - {prop['docstring']}")
        lines.append("")
    
    # Methods
    if cls['methods']:
        lines.append("**Methods:**")
        lines.append("")
        for method in cls['methods']:
            lines.append(format_method(method))
    
    lines.append("---")
    lines.append("")
    
    return "\n".join(lines)


def format_function(func: Dict) -> str:
    """Format a standalone function"""
    return format_method(func)


def generate_markdown(data: Dict) -> str:
    """Generate complete markdown documentation"""
    
    lines = []
    
    # Header
    lines.append("# Empirica Python API Reference (v4.0)")
    lines.append("")
    lines.append(f"**Generated from code:** {datetime.now().strftime('%Y-%m-%d')}")
    lines.append(f"**Total modules:** {data['total_modules']}")
    lines.append(f"**Total classes:** {data['total_classes']}")
    lines.append(f"**Total functions:** {data['total_functions']}")
    lines.append("")
    lines.append("---")
    lines.append("")
    
    # Table of contents
    lines.append("## Table of Contents")
    lines.append("")
    for module_info in data['modules']:
        module_path = module_info['module_path']
        module_name = Path(module_path).stem
        anchor = module_name.lower().replace('_', '-')
        lines.append(f"- [{module_name}](#{anchor})")
    lines.append("")
    lines.append("---")
    lines.append("")
    
    # Modules
    for module_info in data['modules']:
        module_path = module_info['module_path']
        module_name = Path(module_path).stem
        api = module_info['api']
        
        lines.append(f"## {module_name}")
        lines.append("")
        lines.append(f"**Module:** `{module_path}`")
        lines.append("")
        
        # Classes
        if api['classes']:
            lines.append(f"**{len(api['classes'])} classes**")
            lines.append("")
            for cls in api['classes']:
                lines.append(format_class(cls, module_path))
        
        # Functions
        if api['functions']:
            lines.append(f"**{len(api['functions'])} functions**")
            lines.append("")
            for func in api['functions']:
                lines.append(format_function(func))
                lines.append("---")
                lines.append("")
    
    # Footer
    lines.append("---")
    lines.append("")
    lines.append("## Notes")
    lines.append("")
    lines.append("- **Generated documentation:** This file is auto-generated from the codebase.")
    lines.append("- **100% accuracy:** Every API listed here exists in the current codebase.")
    lines.append("- **Public APIs only:** Private methods (starting with `_`) are excluded.")
    lines.append("")
    lines.append("**To regenerate this documentation:**")
    lines.append("```bash")
    lines.append("cd dev_scripts/doc_regeneration")
    lines.append("python3 extract_python_api.py")
    lines.append("python3 generate_python_api_markdown.py")
    lines.append("```")
    lines.append("")
    lines.append("**Last updated:** " + datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC'))
    lines.append("")
    
    return "\n".join(lines)


def main():
    """Main entry point"""
    
    # Load extracted data
    input_path = Path(__file__).parent / 'python_api_extracted.json'
    
    if not input_path.exists():
        print(f"❌ Error: {input_path} not found")
        print("   Run extract_python_api.py first!")
        sys.exit(1)
    
    print(f"📖 Loading {input_path}...")
    
    with open(input_path) as f:
        data = json.load(f)
    
    print(f"✅ Loaded {data['total_modules']} modules")
    
    # Generate markdown
    print("📝 Generating markdown...")
    markdown = generate_markdown(data)
    
    # Save output
    output_path = Path(__file__).parent.parent.parent / 'docs' / 'reference' / 'PYTHON_API_GENERATED.md'
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        f.write(markdown)
    
    print(f"✅ Saved to: {output_path}")
    print(f"📊 Generated {len(markdown.splitlines())} lines of documentation")
    print(f"   {data['total_classes']} classes, {data['total_functions']} functions")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
