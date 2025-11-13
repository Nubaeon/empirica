#!/usr/bin/env python3
"""
AI Code Guidance MCP Server (Simple STDIO)
==========================================
Provides comprehensive AI development guidelines via MCP.
Uses simple stdio loop (no async) to avoid TaskGroup issues.
"""

import sys
import json
import logging
from pathlib import Path

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(name)s:%(message)s')
logger = logging.getLogger("code-guidance-mcp")

# Path to the AI code guide
CODE_GUIDE_PATH = Path("/home/yogapad/empirical-ai/Documentation/Dev_Guides/ai_code_guide.md")

def load_code_guide():
    """Load the AI code guide content"""
    try:
        with open(CODE_GUIDE_PATH, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        logger.error(f"Failed to load code guide: {e}")
        return None

def parse_code_guide_sections():
    """Parse the code guide into structured sections"""
    content = load_code_guide()
    if not content:
        return {}
    
    sections = {}
    current_section = None
    current_content = []
    
    for line in content.split('\n'):
        if line.startswith('## '):
            # Save previous section
            if current_section:
                sections[current_section] = '\n'.join(current_content)
            
            # Start new section
            current_section = line[3:].strip()
            current_content = [line]
        else:
            if current_section:
                current_content.append(line)
    
    # Save final section
    if current_section:
        sections[current_section] = '\n'.join(current_content)
    
    return sections

def mcp_response(id_val, result=None, error=None):
    """Create MCP response"""
    # In JSON-RPC 2.0, responses must include the same id as the request
    # If id_val is None, we still include it in the response as per spec
    resp = {"jsonrpc": "2.0", "id": id_val}
    if error:
        resp["error"] = error
    else:
        resp["result"] = result
    return resp

TOOLS = {
    "get_code_guide": {
        "name": "get_code_guide",
        "description": "Get the complete AI Production Code Creation Guide",
        "inputSchema": {
            "type": "object",
            "properties": {
                "format": {
                    "type": "string",
                    "description": "Format: markdown, structured, or summary",
                    "enum": ["markdown", "structured", "summary"],
                    "default": "markdown"
                }
            }
        }
    },
    "get_guide_section": {
        "name": "get_guide_section",
        "description": "Get a specific section of the code guide",
        "inputSchema": {
            "type": "object",
            "properties": {
                "section": {
                    "type": "string",
                    "description": "Section name to retrieve"
                }
            },
            "required": ["section"]
        }
    },
    "search_code_guidance": {
        "name": "search_code_guidance",
        "description": "Search for specific guidance on coding topics",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query for coding guidance"
                }
            },
            "required": ["query"]
        }
    },
    "get_checklist": {
        "name": "get_checklist",
        "description": "Get development checklists for specific phases",
        "inputSchema": {
            "type": "object",
            "properties": {
                "phase": {
                    "type": "string",
                    "description": "Development phase",
                    "enum": ["planning", "implementation", "testing", "review", "deployment", "maintenance"]
                }
            },
            "required": ["phase"]
        }
    }
}

def tool_get_code_guide(arguments):
    """Get the complete code guide"""
    format_type = arguments.get("format", "markdown")
    content = load_code_guide()
    
    if not content:
        return {"error": "Failed to load AI code guide", "status": "error"}
    
    if format_type == "structured":
        sections = parse_code_guide_sections()
        return {
            "status": "success",
            "format": "structured",
            "sections": sections,
            "section_count": len(sections)
        }
    
    elif format_type == "summary":
        sections = parse_code_guide_sections()
        return {
            "status": "success",
            "format": "summary",
            "sections": list(sections.keys()),
            "section_count": len(sections),
            "word_count": len(content.split()),
            "guideline_count": len(content.split('###'))
        }
    
    else:  # markdown
        return {
            "status": "success",
            "format": "markdown",
            "content": content
        }

def tool_get_guide_section(arguments):
    """Get a specific section"""
    section_name = arguments.get("section", "")
    sections = parse_code_guide_sections()
    
    if section_name in sections:
        return {
            "status": "success",
            "section": section_name,
            "content": sections[section_name]
        }
    else:
        return {
            "status": "error",
            "error": f"Section '{section_name}' not found",
            "available_sections": list(sections.keys())
        }

def tool_search_code_guidance(arguments):
    """Search for guidance"""
    query = arguments.get("query", "").lower()
    content = load_code_guide()
    
    if not content:
        return {"error": "Failed to load code guide", "status": "error"}
    
    # Simple search implementation
    relevant_sections = []
    lines = content.split('\n')
    
    for i, line in enumerate(lines):
        if query in line.lower():
            # Include context around the match
            start = max(0, i-2)
            end = min(len(lines), i+3)
            context = '\n'.join(lines[start:end])
            relevant_sections.append({
                "line": i+1,
                "context": context
            })
    
    return {
        "status": "success",
        "query": query,
        "matches": len(relevant_sections),
        "results": relevant_sections[:10]  # Limit to first 10
    }

def tool_get_checklist(arguments):
    """Get development checklist"""
    phase = arguments.get("phase", "")
    
    checklists = {
        "planning": [
            "Clear problem definition",
            "Success criteria defined",
            "Edge cases identified",
            "Performance requirements specified",
            "Architecture design documented",
            "Error handling strategy planned",
            "Testing approach outlined"
        ],
        "implementation": [
            "Functions have single responsibility",
            "Meaningful names used",
            "Type hints added",
            "Docstrings written",
            "Input validation implemented",
            "Specific exceptions used",
            "Error logging added"
        ],
        "testing": [
            "Unit tests for all functions",
            "Integration tests for workflows",
            "Edge case testing",
            "Error condition testing",
            "Tests are independent",
            "Clear test names"
        ],
        "review": [
            "Code structure reviewed",
            "Error handling verified",
            "Security implications checked",
            "Performance considerations reviewed",
            "Docstrings complete",
            "Documentation updated"
        ],
        "deployment": [
            "All tests passing",
            "Security scan completed",
            "Performance testing done",
            "Environment variables configured",
            "Monitoring set up",
            "Logging configured"
        ],
        "maintenance": [
            "Performance metrics tracked",
            "Error rates monitored",
            "Dependencies kept current",
            "Security patches applied",
            "Documentation maintained"
        ]
    }
    
    if phase in checklists:
        return {
            "status": "success",
            "phase": phase,
            "checklist": checklists[phase],
            "item_count": len(checklists[phase])
        }
    else:
        return {
            "status": "error",
            "error": f"Phase '{phase}' not found",
            "available_phases": list(checklists.keys())
        }

TOOL_FUNCS = {
    "get_code_guide": tool_get_code_guide,
    "get_guide_section": tool_get_guide_section,
    "search_code_guidance": tool_search_code_guidance,
    "get_checklist": tool_get_checklist
}

def run_stdio():
    """Run MCP server over stdio"""
    logger.info("Starting AI Code Guidance MCP Server")
    
    # Check if code guide exists
    if not CODE_GUIDE_PATH.exists():
        logger.warning(f"Code guide not found at {CODE_GUIDE_PATH}")
    else:
        logger.info(f"Code guide loaded from {CODE_GUIDE_PATH}")
    
    while True:
        line = sys.stdin.readline()
        if not line:
            break
        
        try:
            req = json.loads(line)
        except Exception as e:
            logger.error(f"JSON parse error: {e}")
            continue
        
        # Extract method and id, with proper handling of missing/invalid values
        method = req.get("method")
        id_ = req.get("id")
        
        # If there's no method, it's an invalid request - only respond if it has an id
        if method is None:
            if id_ is not None:
                logger.warning(f"Invalid request: no method provided: {req}")
                print(json.dumps(mcp_response(id_, error={"code": -32600, "message": "Invalid Request: method is required"})), flush=True)
            continue
        
        if method == "initialize":
            # Only respond if the request has an id (not a notification)
            if id_ is not None:
                resp = mcp_response(id_, {
                    "protocolVersion": "2024-11-05",
                    "serverInfo": {"name": "code-guidance", "version": "1.0.0"},
                    "capabilities": {"tools": {}},
                })
                print(json.dumps(resp), flush=True)
            continue
        
        if method == "tools/list":
            # Only respond if the request has an id (not a notification)
            if id_ is not None:
                tools_list = [{
                    "name": t["name"],
                    "description": t["description"],
                    "inputSchema": t["inputSchema"],
                } for t in TOOLS.values()]
                print(json.dumps(mcp_response(id_, {"tools": tools_list})), flush=True)
            continue
        
        if method == "tools/call":
            # Only respond if the request has an id (not a notification)
            if id_ is not None:
                params = req.get("params", {})
                name = params.get("name")
                arguments = params.get("arguments", {})
                func = TOOL_FUNCS.get(name)
                
                if not func:
                    print(json.dumps(mcp_response(id_, error={"code": -32601, "message": f"Unknown tool {name}"})), flush=True)
                    continue
                
                try:
                    result = func(arguments)
                    print(json.dumps(mcp_response(id_, {"content": [{"type": "json", "data": result}]})), flush=True)
                except Exception as e:
                    logger.error(f"Tool execution error: {e}")
                    print(json.dumps(mcp_response(id_, error={"code": -32000, "message": str(e)})), flush=True)
            continue
        
        # Unknown method - only respond if the request has an id (not a notification)
        if id_ is not None:
            print(json.dumps(mcp_response(id_, error={"code": -32601, "message": f"Unknown method {method}"})), flush=True)

if __name__ == "__main__":
    try:
        run_stdio()
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)
