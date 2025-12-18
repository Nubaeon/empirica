#!/usr/bin/env python3
"""
Pydantic Tools Server for Empirica
Enhanced data validation, transformation, and analysis capabilities
"""

import asyncio
import json
import sys
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Union
from datetime import datetime

# Setup logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# Add empirica to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from pydantic import BaseModel, Field, ValidationError, validator
    from pydantic.json_schema import GenerateJsonSchema
    from typing_extensions import Annotated
    import yaml
    import toml
    import csv
    import xml.etree.ElementTree as ET
    from dataclasses import dataclass
    from enum import Enum
    
    # Import empirica models for integration (optional)
    try:
        from empirica.core.schemas.epistemic_assessment import EpistemicAssessment
        from empirica.core.goals.types import Goal
        HAS_EMPIRICA_MODELS = True
    except ImportError:
        HAS_EMPIRICA_MODELS = False
    
except ImportError as e:
    logger.error(f"Missing dependencies: {e}")
    sys.exit(1)

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import types

# Create server instance
app = Server("pydantic-tools")

# ============================================================================
# Core Pydantic Models for Tool Integration
# ============================================================================

class DataValidationRequest(BaseModel):
    """Request model for data validation"""
    data: Dict[str, Any]
    schema: Dict[str, Any]
    strict: bool = False
    
class DataTransformationRequest(BaseModel):
    """Request model for data transformation"""
    data: Dict[str, Any]
    target_schema: Dict[str, Any]
    transformation_rules: Optional[Dict[str, Any]] = None
    
class CodeAnalysisRequest(BaseModel):
    """Request model for code analysis"""
    code: str
    analysis_type: str = "complexity"  # complexity, dependencies, patterns
    language: str = "python"

# ============================================================================
# Tool Definitions
# ============================================================================

@app.list_tools()
async def list_tools() -> List[types.Tool]:
    """List all available Pydantic tools"""
    
    tools = [
        # ========== Data Validation Tools ==========
        types.Tool(
            name="validate_data",
            description="Validate data against a Pydantic schema",
            inputSchema={
                "type": "object",
                "properties": {
                    "data": {"type": "object", "description": "Data to validate"},
                    "schema": {"type": "object", "description": "Pydantic-compatible schema"},
                    "strict": {"type": "boolean", "description": "Strict validation mode"}
                },
                "required": ["data", "schema"]
            }
        ),
        
        types.Tool(
            name="generate_pydantic_model",
            description="Generate Pydantic model from JSON schema or example data",
            inputSchema={
                "type": "object",
                "properties": {
                    "input": {"type": "object", "description": "JSON schema or example data"},
                    "model_name": {"type": "string", "description": "Name for generated model"},
                    "include_validators": {"type": "boolean", "description": "Include custom validators"}
                },
                "required": ["input"]
            }
        ),
        
        # ========== Data Transformation Tools ==========
        types.Tool(
            name="transform_data",
            description="Transform data between schemas with validation",
            inputSchema={
                "type": "object",
                "properties": {
                    "data": {"type": "object", "description": "Source data"},
                    "target_schema": {"type": "object", "description": "Target schema"},
                    "transformation_rules": {"type": "object", "description": "Field mapping rules"}
                },
                "required": ["data", "target_schema"]
            }
        ),
        
        types.Tool(
            name="convert_data_format",
            description="Convert data between formats (JSON, YAML, TOML, CSV, XML)",
            inputSchema={
                "type": "object",
                "properties": {
                    "data": {"type": "string", "description": "Input data"},
                    "input_format": {"type": "string", "enum": ["json", "yaml", "toml", "csv", "xml"]},
                    "output_format": {"type": "string", "enum": ["json", "yaml", "toml", "csv", "xml"]},
                    "schema": {"type": "object", "description": "Optional validation schema"}
                },
                "required": ["data", "input_format", "output_format"]
            }
        ),
        
        # ========== Code Analysis Tools ==========
        types.Tool(
            name="analyze_code_complexity",
            description="Analyze code complexity and maintainability metrics",
            inputSchema={
                "type": "object",
                "properties": {
                    "code": {"type": "string", "description": "Source code to analyze"},
                    "language": {"type": "string", "default": "python"},
                    "metrics": {"type": "array", "items": {"type": "string"}}
                },
                "required": ["code"]
            }
        ),
        
        types.Tool(
            name="generate_data_classes",
            description="Generate Python dataclasses from JSON schema",
            inputSchema={
                "type": "object",
                "properties": {
                    "schema": {"type": "object", "description": "JSON schema"},
                    "class_name": {"type": "string", "description": "Base class name"},
                    "include_methods": {"type": "boolean", "description": "Include common methods"}
                },
                "required": ["schema"]
            }
        ),
        
        # ========== Empirica Integration Tools ==========
        types.Tool(
            name="validate_epistemic_assessment",
            description="Validate Empirica epistemic assessment data",
            inputSchema={
                "type": "object",
                "properties": {
                    "assessment": {"type": "object", "description": "Epistemic assessment data"},
                    "phase": {"type": "string", "enum": ["preflight", "check", "postflight"]}
                },
                "required": ["assessment"]
            }
        ),
        
        types.Tool(
            name="generate_goal_schema",
            description="Generate goal schema for Empirica workflow",
            inputSchema={
                "type": "object",
                "properties": {
                    "goal_description": {"type": "string", "description": "Natural language goal"},
                    "scope": {"type": "string", "enum": ["narrow", "medium", "broad"]},
                    "duration": {"type": "string", "enum": ["short", "medium", "long"]}
                },
                "required": ["goal_description"]
            }
        )
    ]
    
    return tools

# ============================================================================
# Tool Implementations
# ============================================================================

async def validate_data(arguments: Dict[str, Any]) -> List[types.Content]:
    """Validate data against Pydantic schema"""
    try:
        request = DataValidationRequest(**arguments)
        
        # Create dynamic Pydantic model
        DynamicModel = type("DynamicModel", (BaseModel,), {
            "__annotations__": {}
        })
        
        for field_name, field_schema in request.schema.get("properties", {}).items():
            field_type = field_schema.get("type", "str")
            if field_type == "string":
                DynamicModel.__annotations__[field_name] = str
            elif field_type == "integer":
                DynamicModel.__annotations__[field_name] = int
            elif field_type == "number":
                DynamicModel.__annotations__[field_name] = float
            elif field_type == "boolean":
                DynamicModel.__annotations__[field_name] = bool
            elif field_type == "object":
                DynamicModel.__annotations__[field_name] = dict
            elif field_type == "array":
                DynamicModel.__annotations__[field_name] = list
        
        # Rebuild model
        DynamicModel = type("DynamicModel", (BaseModel,), DynamicModel.__annotations__)
        
        # Validate data
        validated = DynamicModel(**request.data)
        
        return [types.TextContent(type="text", text=json.dumps({
            "valid": True,
            "validated_data": validated.model_dump(),
            "schema": request.schema
        }))]
        
    except ValidationError as e:
        return [types.TextContent(type="text", text=json.dumps({
            "valid": False,
            "errors": str(e),
            "error_details": e.errors()
        }))]
    except Exception as e:
        return [types.TextContent(type="text", text=json.dumps({
            "valid": False,
            "error": str(e)
        }))]

async def convert_data_format(arguments: Dict[str, Any]) -> List[types.Content]:
    """Convert data between formats"""
    try:
        input_data = arguments["data"]
        input_format = arguments["input_format"]
        output_format = arguments["output_format"]
        
        # Parse input
        if input_format == "json":
            data = json.loads(input_data)
        elif input_format == "yaml":
            data = yaml.safe_load(input_data)
        elif input_format == "toml":
            data = toml.loads(input_data)
        elif input_format == "xml":
            root = ET.fromstring(input_data)
            data = {child.tag: child.text for child in root}
        elif input_format == "csv":
            lines = input_data.strip().split('\n')
            reader = csv.DictReader(lines)
            data = [row for row in reader]
        
        # Convert to output format
        if output_format == "json":
            result = json.dumps(data, indent=2)
        elif output_format == "yaml":
            result = yaml.dump(data, default_flow_style=False)
        elif output_format == "toml":
            result = toml.dumps(data)
        elif output_format == "xml":
            root = ET.Element("root")
            for key, value in data.items():
                child = ET.SubElement(root, key)
                child.text = str(value)
            result = ET.tostring(root, encoding="unicode")
        elif output_format == "csv":
            if isinstance(data, list):
                output = []
                if data:
                    fieldnames = data[0].keys()
                    writer = csv.DictWriter(output, fieldnames=fieldnames)
                    writer.writeheader()
                    writer.writerows(data)
                result = '\n'.join(output)
            else:
                result = "key,value\n" + "\n".join(f"{k},{v}" for k, v in data.items())
        
        return [types.TextContent(type="text", text=result)]
        
    except Exception as e:
        return [types.TextContent(type="text", text=json.dumps({
            "error": str(e),
            "input_format": input_format,
            "output_format": output_format
        }))]

async def analyze_code_complexity(arguments: Dict[str, Any]) -> List[types.Content]:
    """Analyze code complexity"""
    try:
        code = arguments["code"]
        language = arguments.get("language", "python")
        
        # Basic analysis for Python
        if language == "python":
            lines = code.split('\n')
            total_lines = len(lines)
            non_empty_lines = len([l for l in lines if l.strip()])
            
            # Count functions/classes
            functions = sum(1 for line in lines if line.strip().startswith('def '))
            classes = sum(1 for line in lines if line.strip().startswith('class '))
            
            # Count imports
            imports = sum(1 for line in lines if line.strip().startswith('import ') or line.strip().startswith('from '))
            
            # Estimate complexity
            complexity_score = (functions * 2 + classes * 3 + imports) / max(1, non_empty_lines / 10)
            
            analysis = {
                "total_lines": total_lines,
                "non_empty_lines": non_empty_lines,
                "functions": functions,
                "classes": classes,
                "imports": imports,
                "complexity_score": round(complexity_score, 2),
                "maintainability": "high" if complexity_score < 5 else "medium" if complexity_score < 10 else "low"
            }
            
            return [types.TextContent(type="text", text=json.dumps(analysis, indent=2))]
        
    except Exception as e:
        return [types.TextContent(type="text", text=json.dumps({"error": str(e)}))]

# ============================================================================
# Tool Router
# ============================================================================

@app.call_tool()
async def call_tool(name: str, arguments: Dict[str, Any]) -> List[types.Content]:
    """Route tool calls to appropriate handlers"""
    
    logger.info(f"Tool call: {name} with args: {json.dumps(arguments, indent=2)[:200]}")
    
    try:
        if name == "validate_data":
            return await validate_data(arguments)
        elif name == "convert_data_format":
            return await convert_data_format(arguments)
        elif name == "analyze_code_complexity":
            return await analyze_code_complexity(arguments)
        elif name == "generate_pydantic_model":
            return [types.TextContent(type="text", text=json.dumps({"message": "Pydantic model generation not yet implemented"}))]
        elif name == "transform_data":
            return [types.TextContent(type="text", text=json.dumps({"message": "Data transformation not yet implemented"}))]
        elif name == "generate_data_classes":
            return [types.TextContent(type="text", text=json.dumps({"message": "Data class generation not yet implemented"}))]
        elif name == "validate_epistemic_assessment":
            return [types.TextContent(type="text", text=json.dumps({"message": "Epistemic assessment validation not yet implemented"}))]
        elif name == "generate_goal_schema":
            return [types.TextContent(type="text", text=json.dumps({"message": "Goal schema generation not yet implemented"}))]
        else:
            return [types.TextContent(type="text", text=json.dumps({"error": f"Unknown tool: {name}"}))]
    
    except Exception as e:
        logger.error(f"Tool {name} failed: {e}")
        return [types.TextContent(type="text", text=json.dumps({"error": str(e)}))]

# ============================================================================
# Server Main
# ============================================================================

async def main():
    """Run Pydantic Tools Server"""
    logger.info("🚀 Starting Pydantic Tools Server")
    logger.info("📦 Available tools: validate_data, convert_data_format, analyze_code_complexity, generate_pydantic_model, transform_data, generate_data_classes, validate_epistemic_assessment, generate_goal_schema")
    
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )

if __name__ == "__main__":
    asyncio.run(main())