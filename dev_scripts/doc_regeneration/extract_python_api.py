#!/usr/bin/env python3
"""
Python API Extractor - Extract public API from empirica modules

Extracts:
- Public classes
- Public methods
- Docstrings
- Type hints
- Method signatures

Output: JSON structure of all public APIs
"""

import ast
import inspect
import json
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
import importlib.util


def get_type_hint_string(annotation) -> str:
    """Convert type annotation to string"""
    if annotation is inspect.Parameter.empty:
        return "Any"
    
    # Handle string annotations
    if isinstance(annotation, str):
        return annotation
    
    # Handle type objects
    try:
        if hasattr(annotation, '__name__'):
            return annotation.__name__
        else:
            return str(annotation).replace('typing.', '')
    except:
        return "Any"


def extract_method_info(method, method_name: str) -> Dict:
    """Extract information about a method"""
    try:
        sig = inspect.signature(method)
        
        # Get parameters
        params = []
        for param_name, param in sig.parameters.items():
            if param_name == 'self':
                continue
            
            param_info = {
                'name': param_name,
                'type': get_type_hint_string(param.annotation),
                'default': None if param.default is inspect.Parameter.empty else repr(param.default),
                'required': param.default is inspect.Parameter.empty
            }
            params.append(param_info)
        
        # Get return type
        return_type = get_type_hint_string(sig.return_annotation)
        
        # Get docstring
        docstring = inspect.getdoc(method) or ""
        
        return {
            'name': method_name,
            'docstring': docstring,
            'parameters': params,
            'return_type': return_type,
            'signature': str(sig)
        }
    except Exception as e:
        return {
            'name': method_name,
            'docstring': inspect.getdoc(method) or "",
            'parameters': [],
            'return_type': "Any",
            'signature': f"(error extracting: {e})",
            'extraction_error': str(e)
        }


def extract_class_info(cls, class_name: str) -> Dict:
    """Extract information about a class"""
    
    # Get class docstring
    docstring = inspect.getdoc(cls) or ""
    
    # Get public methods
    methods = []
    for method_name, method in inspect.getmembers(cls, predicate=inspect.isfunction):
        # Skip private methods
        if method_name.startswith('_') and method_name != '__init__':
            continue
        
        methods.append(extract_method_info(method, method_name))
    
    # Get class properties
    properties = []
    for prop_name, prop in inspect.getmembers(cls, predicate=lambda x: isinstance(x, property)):
        if not prop_name.startswith('_'):
            properties.append({
                'name': prop_name,
                'docstring': inspect.getdoc(prop.fget) if prop.fget else ""
            })
    
    return {
        'name': class_name,
        'docstring': docstring,
        'methods': methods,
        'properties': properties,
        'is_public': not class_name.startswith('_')
    }


def extract_function_info(func, func_name: str) -> Dict:
    """Extract information about a standalone function"""
    return extract_method_info(func, func_name)


def extract_module_api(module_path: Path) -> Dict:
    """Extract API from a Python module"""
    
    # Import the module
    spec = importlib.util.spec_from_file_location("temp_module", module_path)
    if not spec or not spec.loader:
        return {'error': 'Could not load module'}
    
    module = importlib.util.module_from_spec(spec)
    
    try:
        spec.loader.exec_module(module)
    except Exception as e:
        return {'error': f'Could not execute module: {e}'}
    
    api = {
        'module': str(module_path),
        'classes': [],
        'functions': []
    }
    
    # Extract classes
    for name, obj in inspect.getmembers(module, predicate=inspect.isclass):
        # Only include classes defined in this module
        if obj.__module__ == module.__name__:
            if not name.startswith('_'):
                api['classes'].append(extract_class_info(obj, name))
    
    # Extract functions
    for name, obj in inspect.getmembers(module, predicate=inspect.isfunction):
        # Only include functions defined in this module
        if obj.__module__ == module.__name__:
            if not name.startswith('_'):
                api['functions'].append(extract_function_info(obj, name))
    
    return api


def scan_empirica_modules(empirica_path: Path) -> List[Dict]:
    """Scan all Python modules in empirica/ directory"""
    
    modules = []
    
    # Key modules to document
    important_modules = [
        'data/session_database.py',
        'core/goals/repository.py',
        'core/tasks/repository.py',
        'integrations/beads.py',
        'integrations/branch_mapping.py',
        'core/canonical/git_enhanced_reflex_logger.py',
        'core/handoff.py',
        'utils/doc_code_integrity.py'
    ]
    
    for module_rel_path in important_modules:
        module_path = empirica_path / module_rel_path
        
        if not module_path.exists():
            print(f"⚠️  Module not found: {module_rel_path}")
            continue
        
        print(f"📖 Extracting: {module_rel_path}")
        
        try:
            api = extract_module_api(module_path)
            
            if 'error' not in api:
                modules.append({
                    'module_path': module_rel_path,
                    'api': api
                })
                print(f"   ✅ {len(api['classes'])} classes, {len(api['functions'])} functions")
            else:
                print(f"   ❌ Error: {api['error']}")
        except Exception as e:
            print(f"   ❌ Exception: {e}")
    
    return modules


def main():
    """Main entry point"""
    
    # Find empirica module
    empirica_path = Path(__file__).parent.parent.parent / 'empirica'
    
    if not empirica_path.exists():
        print(f"❌ Error: {empirica_path} not found")
        sys.exit(1)
    
    print(f"🔍 Scanning Empirica modules in {empirica_path}...\n")
    
    # Extract API from modules
    modules = scan_empirica_modules(empirica_path)
    
    # Count totals
    total_classes = sum(len(m['api']['classes']) for m in modules)
    total_functions = sum(len(m['api']['functions']) for m in modules)
    
    # Output JSON
    output = {
        'extraction_date': '2025-12-16',
        'total_modules': len(modules),
        'total_classes': total_classes,
        'total_functions': total_functions,
        'modules': modules
    }
    
    output_path = Path(__file__).parent / 'python_api_extracted.json'
    with open(output_path, 'w') as f:
        json.dump(output, f, indent=2)
    
    print(f"\n✅ Saved to: {output_path}")
    print(f"\n📊 Summary:")
    print(f"   Total modules: {len(modules)}")
    print(f"   Total classes: {total_classes}")
    print(f"   Total functions: {total_functions}")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
