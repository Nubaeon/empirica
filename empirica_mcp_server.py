#!/usr/bin/env python3
"""
🧠 Empirica MCP Server (Meta Context Protocol)

Purpose:
- Expose Empirica/SDK and related dev capabilities to LLMs via a unified MCP tool interface
- Prefer direct function/class wrapping; fallback to CLI where necessary
- Provide structured JSON I/O for robust, low-latency integrations

Transports:
- STDIO (default) for local, secure use: `python3 empirica_mcp_server.py --stdio`

Implements minimal MCP methods:
- initialize
- tools/list
- tools/call

Initial implemented tools (fully working):
- empirica.workspace.scan
- empirica.context.validate_file
- empirica.web.templates.generate
- empirica.web.server.status
- empirica.uncertainty.assess
- sentry.fetch_full_event_context (via sentry_mcp_wrapper)
- devtools.get_console_error_summary (via chrome_devtools_correlator)
- correlator.correlate_sentry_with_browser

Additional tools (declared, not yet implemented):
- 24 semantic kit components placeholders with clear responses
"""

import sys
import os
import json
import time
import argparse
import subprocess
from pathlib import Path
from typing import Any, Dict, List

# Optional imports (graceful)
AUGIE_OK = False
try:
    from ai_ecosystem_architecture.augie_sdk.core import AugieSDK  # type: ignore
    AUGIE_OK = True
except Exception:
    AUGIE_OK = False

SENTRY_OK = False
DEVTOOLS_OK = True  # correlator simulates if not available

# Local wrappers
from sentry_mcp_wrapper import sentry_get_issue_full_event  # type: ignore
from chrome_devtools_correlator import (
    ChromeDevToolsCorrelator,
    correlate_sentry_error_with_browser,
)

# Utility
ROOT = Path(__file__).resolve().parent
WEB_DIR = ROOT / "semantic_self_aware_kit" / "web"

# ------------------ MCP Core ------------------

def mcp_response(id_: Any, result: Any = None, error: Any = None) -> Dict[str, Any]:
    if error is not None:
        return {"jsonrpc": "2.0", "id": id_, "error": error}
    return {"jsonrpc": "2.0", "id": id_, "result": result}

TOOLS: Dict[str, Dict[str, Any]] = {}


def register_tool(name: str, description: str, parameters: Dict[str, Any], returns: Dict[str, Any]):
    TOOLS[name] = {
        "name": name,
        "description": description,
        "inputSchema": parameters,
        "outputSchema": returns,
    }


# ------------------ Tool Implementations ------------------

def tool_empirica_workspace_scan(params: Dict[str, Any]) -> Dict[str, Any]:
    base = Path(params.get("path") or ROOT)
    max_entries = int(params.get("max_entries", 200))
    entries: List[Dict[str, Any]] = []
    for p in base.rglob("*"):
        try:
            if len(entries) >= max_entries:
                break
            entries.append({
                "path": str(p.relative_to(base)),
                "type": "dir" if p.is_dir() else "file",
                "size": (p.stat().st_size if p.is_file() else None),
            })
        except Exception:
            continue
    return {"root": str(base), "entries": entries}


def tool_empirica_context_validate_file(params: Dict[str, Any]) -> Dict[str, Any]:
    path = Path(params.get("path", ""))
    exists = path.exists()
    is_file = path.is_file()
    size = path.stat().st_size if is_file else None
    return {
        "path": str(path),
        "exists": exists,
        "is_file": is_file,
        "size": size,
        "validation": "ok" if exists else "missing",
    }


def tool_empirica_web_templates_generate(params: Dict[str, Any]) -> Dict[str, Any]:
    """Run template generator for Empirica web"""
    gen = WEB_DIR / "templates" / "template_generator.py"
    if not gen.exists():
        return {"success": False, "error": f"Missing generator: {gen}"}
    try:
        res = subprocess.run(["python3", str(gen)], capture_output=True, text=True, timeout=120)
        return {
            "success": res.returncode == 0,
            "stdout": res.stdout[-4000:],
            "stderr": res.stderr[-4000:],
            "code": res.returncode,
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def tool_empirica_web_server_status(params: Dict[str, Any]) -> Dict[str, Any]:
    import urllib.request  # local import to avoid global dependency
    url = params.get("url", "http://localhost:5005/health")
    try:
        with urllib.request.urlopen(url, timeout=3) as r:
            body = r.read().decode("utf-8")
            return {"ok": True, "status": r.status, "body": body[:2000]}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def tool_empirica_uncertainty_assess(params: Dict[str, Any]) -> Dict[str, Any]:
    """Assess uncertainty using AugieSDK if available"""
    if not AUGIE_OK:
        return {"ok": False, "error": "AugieSDK unavailable"}
    try:
        augie = AugieSDK(params.get("ai_id", "empirica_mcp"))
        result = augie.assess_situation_enhanced(params.get("context", {}))
        return {"ok": True, "assessment": result}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def tool_sentry_fetch_full_event_context(params: Dict[str, Any]) -> Dict[str, Any]:
    issue_id = params.get("issue_id")
    project_slug = params.get("project_slug")
    if not issue_id or not project_slug:
        return {"success": False, "error": "issue_id and project_slug required"}
    return sentry_get_issue_full_event(issue_id, project_slug)


def tool_devtools_get_console_error_summary(params: Dict[str, Any]) -> Dict[str, Any]:
    url = params.get("url")
    correlator = ChromeDevToolsCorrelator()
    return correlator.get_console_error_summary(url)

def tool_devtools_get_network_requests(params: Dict[str, Any]) -> Dict[str, Any]:
    url = params.get("url")
    correlator = ChromeDevToolsCorrelator()
    return correlator.get_network_requests(url)

def tool_devtools_get_performance_metrics(params: Dict[str, Any]) -> Dict[str, Any]:
    url = params.get("url")
    correlator = ChromeDevToolsCorrelator()
    return correlator.get_performance_metrics(url)


def tool_correlator_correlate_sentry_with_browser(params: Dict[str, Any]) -> Dict[str, Any]:
    sentry_context = params.get("sentry_context") or {}
    return correlate_sentry_error_with_browser(sentry_context)


# --------- Implemented wrappers for key Semantic Kit components ---------

def tool_semantic_workspace_awareness(params: Dict[str, Any]) -> Dict[str, Any]:
    """Direct wrapper over WorkspaceNavigator to expose workspace intelligence"""
    from semantic_self_aware_kit.semantic_self_aware_kit.workspace_awareness.workspace_awareness import WorkspaceNavigator
    map_path = params.get("map_file_path") or "digital_workspace_map.json"
    assigned_to = params.get("assigned_to") or "AI"
    nav = WorkspaceNavigator(map_file_path=map_path)
    return {
        "status": nav.get_current_status(),
        "intelligence": nav.get_workspace_intelligence(),
        "next_task": nav.find_next_task(assigned_to=assigned_to),
    }


def tool_semantic_uncertainty_analysis(params: Dict[str, Any]) -> Dict[str, Any]:
    """Prefer AugieSDK for uncertainty assessment; fall back gracefully"""
    if AUGIE_OK:
        try:
            ai_id = params.get("ai_id", "empirica_mcp")
            context = params.get("context", {})
            augie = AugieSDK(ai_id)
            return {"ok": True, "assessment": augie.assess_situation_enhanced(context)}
        except Exception as e:
            return {"ok": False, "error": f"Augie assessment failed: {e}"}
    # Fallback simple vector
    ctx = params.get("context", {})
    score = 1.0 - float(ctx.get("confidence", 0.5))
    return {"ok": True, "assessment": {"uncertainty_score": score, "context": ctx}}


def tool_semantic_intelligent_navigation(params: Dict[str, Any]) -> Dict[str, Any]:
    """Attempt to call Intelligent Navigation if available; otherwise hint next steps"""
    try:
        from semantic_self_aware_kit.semantic_self_aware_kit.intelligent_navigation.intelligent_navigation import (
            suggest_navigation_plan,
        )
        target = params.get("target") or "."
        return suggest_navigation_plan(target)  # type: ignore
    except Exception:
        # Fallback heuristic using WorkspaceNavigator
        try:
            from semantic_self_aware_kit.semantic_self_aware_kit.workspace_awareness.workspace_awareness import WorkspaceNavigator
            nav = WorkspaceNavigator()
            return {
                "plan": [
                    "scan_workspace",
                    "identify_active_tasks",
                    "prioritize_in_progress",
                ],
                "next_task": nav.find_next_task() or {},
            }
        except Exception as e:
            return {"ok": False, "error": f"Navigation unavailable: {e}"}


def tool_semantic_context_validation(params: Dict[str, Any]) -> Dict[str, Any]:
    """Try Context Validation module; fallback to basic checks"""
    try:
        from semantic_self_aware_kit.semantic_self_aware_kit.context_validation.context_validation import (
            validate_context_safe,
        )
        target = params.get("target") or "."
        return validate_context_safe(target)  # type: ignore
    except Exception:
        # Basic fallback
        path = Path(params.get("target") or ".")
        return {
            "exists": path.exists(),
            "is_dir": path.is_dir(),
            "file_count": len(list(path.glob("**/*"))) if path.exists() else 0,
        }

# --------- Placeholders for 24 Semantic Kit components (declarative) ---------
SEMANTIC_COMPONENTS = [
    ("semantic.workspace_awareness", "Workspace inspection and navigation"),
    ("semantic.intelligent_navigation", "Navigate project intelligently"),
    ("semantic.context_validation", "Validate environment and inputs"),
    ("semantic.security_monitoring", "Security checks"),
    ("semantic.uncertainty_analysis", "8D uncertainty assessment"),
    ("semantic.advanced_uncertainty", "Advanced uncertainty vectors"),
    ("semantic.meta_cognitive_evaluator", "Metacognitive self-assessment"),
    ("semantic.empirical_performance_analyzer", "Performance metrics"),
    ("semantic.functionality_analyzer", "Functionality analysis"),
    ("semantic.collaboration_framework", "Collaboration tooling"),
    ("semantic.advanced_collaboration", "Advanced collaboration"),
    ("semantic.code_intelligence_analyzer", "Code intelligence"),
    ("semantic.environment_stabilization", "Environment stability"),
    ("semantic.procedural_analysis", "Procedural analysis"),
    ("semantic.runtime_validation", "Runtime validation"),
    ("semantic.universal_grounding", "Grounding utilities"),
    ("semantic.intelligent_suggestions", "Intelligent suggestions"),
    ("semantic.context_aware_integration", "Context-aware integration"),
    ("semantic.workspace_status", "Workspace status snapshot"),
    ("semantic.security_audit", "Security audit"),
    ("semantic.docs_generation", "Docs generation"),
    ("semantic.change_management", "Change management"),
    ("semantic.template_operations", "Template operations"),
    ("semantic.web_validation", "Web validation cascade"),
]


def tool_placeholder(params: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "ok": False,
        "implemented": False,
        "message": "Tool declared but not implemented yet. Prefer direct SDK wrapping where possible; fallback to CLI adapter.",
        "received_params": params,
    }
    return {
        "ok": False,
        "implemented": False,
        "message": "Tool declared but not implemented yet. Prefer direct SDK wrapping where possible; fallback to CLI adapter.",
        "received_params": params,
    }


# ------------------ Dynamic Component Invocation ------------------

def _dynamic_invoke(module_path: str, class_name: str = None, func_candidates: List[str] = None, kwargs: Dict[str, Any] = None) -> Dict[str, Any]:
    """Dynamically import a module/class and call the first available function/method from candidates.
    Returns structured JSON with result or graceful error and introspection info.
    """
    func_candidates = func_candidates or [
        "evaluate", "assess", "analyze", "analyze_code", "analyze_functionality",
        "suggest", "suggest_navigation_plan", "run", "run_cascade", "monitor",
        "get_status", "validate", "validate_context_safe", "plan", "integrate",
        "benchmark", "scan", "stabilize", "ground"
    ]
    kwargs = kwargs or {}
    try:
        import importlib
        mod = importlib.import_module(module_path)
        target = mod
        if class_name:
            cls = getattr(mod, class_name, None)
            if cls is None:
                return {"ok": False, "error": f"Class {class_name} not found in {module_path}", "available": dir(mod)}
            try:
                target = cls()  # type: ignore
            except Exception:
                try:
                    target = cls  # use class as namespace if no init
                except Exception as e:
                    return {"ok": False, "error": f"Failed to instantiate {class_name}: {e}"}
        # Find callable
        for fname in func_candidates:
            func = getattr(target, fname, None)
            if callable(func):
                try:
                    result = func(**kwargs) if "**" else func(kwargs) if len(kwargs) == 1 else func()
                except TypeError:
                    # Try flexible calling styles
                    try:
                        result = func(**kwargs)
                    except Exception:
                        try:
                            result = func()
                        except Exception as e:
                            return {"ok": False, "error": f"Callable {fname} failed: {e}"}
                return {"ok": True, "module": module_path, "callable": fname, "result": result}
        return {"ok": False, "error": "No known callable found", "available": dir(target)}
    except Exception as e:
        return {"ok": False, "error": f"Import error for {module_path}: {e}"}


# ------------------ Additional Semantic Wrappers ------------------

def tool_semantic_meta_cognitive_evaluator(params: Dict[str, Any]) -> Dict[str, Any]:
    return _dynamic_invoke(
        "semantic_self_aware_kit.semantic_self_aware_kit.meta_cognitive_evaluator.meta_cognitive_evaluator",
        func_candidates=["evaluate", "run", "analyze", "score", "assess"],
        kwargs=params,
    )

def tool_semantic_empirical_performance_analyzer(params: Dict[str, Any]) -> Dict[str, Any]:
    return _dynamic_invoke(
        "semantic_self_aware_kit.semantic_self_aware_kit.empirical_performance_analyzer.empirical_performance_analyzer",
        func_candidates=["analyze", "benchmark", "evaluate"],
        kwargs=params,
    )

def tool_semantic_functionality_analyzer(params: Dict[str, Any]) -> Dict[str, Any]:
    return _dynamic_invoke(
        "semantic_self_aware_kit.semantic_self_aware_kit.functionality_analyzer.functionality_analyzer",
        func_candidates=["analyze_functionality", "analyze", "evaluate"],
        kwargs=params,
    )

def tool_semantic_code_intelligence_analyzer(params: Dict[str, Any]) -> Dict[str, Any]:
    return _dynamic_invoke(
        "semantic_self_aware_kit.semantic_self_aware_kit.code_intelligence_analyzer.code_intelligence_analyzer",
        func_candidates=["analyze_code", "analyze", "scan"],
        kwargs=params,
    )

def tool_semantic_security_monitoring(params: Dict[str, Any]) -> Dict[str, Any]:
    return _dynamic_invoke(
        "semantic_self_aware_kit.semantic_self_aware_kit.security_monitoring.security_monitoring",
        func_candidates=["monitor", "evaluate", "scan"],
        kwargs=params,
    )

def tool_semantic_environment_stabilization(params: Dict[str, Any]) -> Dict[str, Any]:
    return _dynamic_invoke(
        "semantic_self_aware_kit.semantic_self_aware_kit.environment_stabilization.environment_stabilization",
        func_candidates=["stabilize", "run", "evaluate"],
        kwargs=params,
    )

def tool_semantic_runtime_validation(params: Dict[str, Any]) -> Dict[str, Any]:
    return _dynamic_invoke(
        "semantic_self_aware_kit.semantic_self_aware_kit.runtime_validation.runtime_validation",
        func_candidates=["run", "validate", "evaluate"],
        kwargs=params,
    )

def tool_semantic_proactive_monitor(params: Dict[str, Any]) -> Dict[str, Any]:
    return _dynamic_invoke(
        "semantic_self_aware_kit.semantic_self_aware_kit.proactive_monitor.proactive_monitor",
        func_candidates=["monitor", "run", "evaluate"],
        kwargs=params,
    )

def tool_semantic_advanced_investigation(params: Dict[str, Any]) -> Dict[str, Any]:
    return _dynamic_invoke(
        "semantic_self_aware_kit.semantic_self_aware_kit.advanced_investigation.advanced_investigation",
        func_candidates=["run", "investigate", "analyze"],
        kwargs=params,
    )

def tool_semantic_context_aware_integration(params: Dict[str, Any]) -> Dict[str, Any]:
    return _dynamic_invoke(
        "semantic_self_aware_kit.semantic_self_aware_kit.context_aware_integration.context_aware_integration",
        func_candidates=["integrate", "run", "evaluate"],
        kwargs=params,
    )

def tool_semantic_intelligent_suggestions(params: Dict[str, Any]) -> Dict[str, Any]:
    return _dynamic_invoke(
        "semantic_self_aware_kit.semantic_self_aware_kit.intelligent_suggestions.suggestion_engine",
        func_candidates=["suggest", "run", "evaluate"],
        kwargs=params,
    )

def tool_semantic_universal_grounding(params: Dict[str, Any]) -> Dict[str, Any]:
    return _dynamic_invoke(
        "semantic_self_aware_kit.semantic_self_aware_kit.universal_grounding.universal_grounding",
        func_candidates=["ground", "evaluate", "run"],
        kwargs=params,
    )

def tool_semantic_metacognitive_cascade(params: Dict[str, Any]) -> Dict[str, Any]:
    return _dynamic_invoke(
        "semantic_self_aware_kit.semantic_self_aware_kit.metacognitive_cascade.metacognitive_cascade",
        func_candidates=["run_cascade", "run", "evaluate"],
        kwargs=params,
    )

def tool_semantic_context_monitoring(params: Dict[str, Any]) -> Dict[str, Any]:
    return _dynamic_invoke(
        "semantic_self_aware_kit.semantic_self_aware_kit.context_monitoring.context_monitor",
        func_candidates=["get_status", "monitor", "evaluate"],
        kwargs=params,
    )

# ------------------ More Semantic Wrappers (remaining set) ------------------

def tool_semantic_collaboration_framework(params: Dict[str, Any]) -> Dict[str, Any]:
    return _dynamic_invoke(
        "semantic_self_aware_kit.semantic_self_aware_kit.collaboration_framework.collaboration_framework",
        func_candidates=["run", "evaluate", "integrate"],
        kwargs=params,
    )

def tool_semantic_advanced_collaboration(params: Dict[str, Any]) -> Dict[str, Any]:
    return _dynamic_invoke(
        "semantic_self_aware_kit.semantic_self_aware_kit.advanced_collaboration.advanced_collaboration",
        func_candidates=["run", "evaluate", "integrate"],
        kwargs=params,
    )

def tool_semantic_workspace_status(params: Dict[str, Any]) -> Dict[str, Any]:
    from semantic_self_aware_kit.semantic_self_aware_kit.workspace_awareness.workspace_awareness import WorkspaceNavigator
    nav = WorkspaceNavigator(map_file_path=params.get("map_file_path") or "digital_workspace_map.json")
    return {"status": nav.get_current_status(), "intelligence": nav.get_workspace_intelligence()}

def tool_semantic_security_audit(params: Dict[str, Any]) -> Dict[str, Any]:
    # Try security_monitoring first; otherwise simple audit over workspace
    try:
        return _dynamic_invoke(
            "semantic_self_aware_kit.semantic_self_aware_kit.security_monitoring.security_monitoring",
            func_candidates=["monitor", "evaluate", "scan"],
            kwargs=params,
        )
    except Exception as e:
        base = Path(params.get("path") or ".")
        py_files = list(base.glob("**/*.py"))
        return {"ok": True, "files_checked": len(py_files), "notes": "basic security audit placeholder"}

def tool_semantic_docs_generation(params: Dict[str, Any]) -> Dict[str, Any]:
    return {"ok": False, "implemented": False, "message": "Docs generation not implemented yet"}

def tool_semantic_change_management(params: Dict[str, Any]) -> Dict[str, Any]:
    """Wrap SimpleChangeManager for summary and adding changes"""
    import sys
    sys.path.insert(0, str(WEB_DIR))
    try:
        from simple_change_manager import SimpleChangeManager  # type: ignore
        mgr = SimpleChangeManager(params.get("project", "empirica"))
        action = params.get("action", "summary")
        if action == "add_link":
            cid = mgr.add_link_change(
                link_text=params.get("link_text", ""),
                old_url=params.get("old_url", ""),
                new_url=params.get("new_url", ""),
                reasoning=params.get("reasoning", ""),
                pages_affected=params.get("pages_affected", [])
            )
            return {"ok": True, "change_id": cid}
        if action == "add_cosmetic":
            cid = mgr.add_cosmetic_change(
                description=params.get("description", ""),
                semantic_reasoning=params.get("semantic_reasoning", ""),
                source_html=params.get("source_html", ""),
                target_element=params.get("target_element", ""),
                author=params.get("author", "mcp")
            )
            return {"ok": True, "change_id": cid}
        # default: summary
        summary = mgr.summarize()
        return {"ok": True, "summary": summary}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def tool_semantic_template_operations(params: Dict[str, Any]) -> Dict[str, Any]:
    # Alias to web.templates.generate
    return tool_empirica_web_templates_generate(params)

def tool_semantic_web_validation(params: Dict[str, Any]) -> Dict[str, Any]:
    script = WEB_DIR / "empirical_research_web" / "web_validation_cascade.py"
    if not script.exists():
        return {"ok": False, "error": f"Missing web validation cascade: {script}"}
    try:
        target = params.get("target")
        cmd = ["python3", str(script)] + ([target] if target else [])
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
        return {
            "ok": res.returncode == 0,
            "stdout": res.stdout[-4000:],
            "stderr": res.stderr[-2000:],
            "code": res.returncode,
        }
    except Exception as e:
        return {"ok": False, "error": str(e)}

# ------------------ Docs / Reference Tools ------------------

def tool_docs_master_reference(params: Dict[str, Any]) -> Dict[str, Any]:
    from pathlib import Path
    import json
    p = Path("Documentation/master_reference_manifest.json")
    if not p.exists():
        return {"ok": False, "error": "master_reference_manifest.json missing"}
    try:
        return {"ok": True, "manifest": json.loads(p.read_text())}
    except Exception as e:
        return {"ok": False, "error": str(e)}

# ------------------ Manager API (Cascade trigger) Wrapper ------------------

def tool_manager_start_cascade(params: Dict[str, Any]) -> Dict[str, Any]:
    """Start a reasoning cascade via Manager API.
    Expects: { event_type, thread_name?, initial_action?, initial_uncertainty?, ... }
    """
    import json, urllib.request
    url = params.get("url", "http://127.0.0.1:8080/api/start-reasoning-thread")
    data = json.dumps(params).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=5) as r:
            body = r.read().decode("utf-8")
            return {"ok": True, "status": r.status, "body": body[:4000]}
    except Exception as e:
        return {"ok": False, "error": str(e)}

# ------------------ Dev Panel and CSP Wrappers ------------------

def _http_json(url: str, method: str = "GET", body: Dict[str, Any] = None, headers: Dict[str, str] = None, timeout: float = 8.0) -> Dict[str, Any]:
    import json, urllib.request
    headers = headers or {"Content-Type": "application/json"}
    data = None
    if body is not None:
        data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            raw = r.read().decode("utf-8")
            try:
                parsed = json.loads(raw)
            except Exception:
                parsed = {"raw": raw[:4000]}
            return {"ok": True, "status": r.status, "data": parsed}
    except Exception as e:
        return {"ok": False, "error": str(e), "url": url}

# Dev Panel tools

def tool_devpanel_status(params: Dict[str, Any]) -> Dict[str, Any]:
    base = params.get("base_url", "http://127.0.0.1:5011")
    token = params.get("token")
    url = f"{base}/api/status" + (f"?token={token}" if token else "")
    return _http_json(url)

def tool_devpanel_clean(params: Dict[str, Any]) -> Dict[str, Any]:
    base = params.get("base_url", "http://127.0.0.1:5011")
    token = params.get("token")
    url = f"{base}/api/clean" + (f"?token={token}" if token else "")
    return _http_json(url, method="POST", body={})

def tool_devpanel_rebuild_web(params: Dict[str, Any]) -> Dict[str, Any]:
    base = params.get("base_url", "http://127.0.0.1:5011")
    token = params.get("token")
    url = f"{base}/api/rebuild-web" + (f"?token={token}" if token else "")
    return _http_json(url, method="POST", body={})

def tool_devpanel_change_request(params: Dict[str, Any]) -> Dict[str, Any]:
    base = params.get("base_url", "http://127.0.0.1:5011")
    token = params.get("token")
    payload = {
        "type": params.get("type", "cosmetic"),
        "author": params.get("author", "mcp"),
        "description": params.get("description", ""),
        "semantic_reasoning": params.get("semantic_reasoning", ""),
        "source_html": params.get("source_html", ""),
        "target_element": params.get("target_element", ""),
        "link_text": params.get("link_text", ""),
        "old_url": params.get("old_url", ""),
        "new_url": params.get("new_url", ""),
        "reasoning": params.get("reasoning", ""),
        "pages_affected": params.get("pages_affected", []),
    }
    url = f"{base}/api/change-request" + (f"?token={token}" if token else "")
    return _http_json(url, method="POST", body=payload)

# CSP tools

def tool_csp_status(params: Dict[str, Any]) -> Dict[str, Any]:
    base = params.get("base_url", "http://127.0.0.1:8085")
    token = params.get("token")
    headers = {"Content-Type":"application/json"}
    if token: headers["Authorization"] = f"Bearer {token}"
    return _http_json(f"{base}/consciousness/status", headers=headers)

def tool_csp_broadcast(params: Dict[str, Any]) -> Dict[str, Any]:
    base = params.get("base_url", "http://127.0.0.1:8085")
    token = params.get("token")
    event = params.get("event", {})
    headers = {"Content-Type":"application/json"}
    if token: headers["Authorization"] = f"Bearer {token}"
    return _http_json(f"{base}/consciousness/broadcast", method="POST", body=event, headers=headers)

def tool_csp_fetch_events(params: Dict[str, Any]) -> Dict[str, Any]:
    base = params.get("base_url", "http://127.0.0.1:8085")
    token = params.get("token")
    limit = int(params.get("limit", 25))
    headers = {"Content-Type":"application/json"}
    if token: headers["Authorization"] = f"Bearer {token}"
    return _http_json(f"{base}/consciousness/events?limit={limit}", headers=headers)

# ------------------ Qdrant Tools ------------------

def _qdrant_http(path: str, method: str = "GET", body: Dict[str, Any] = None, timeout: float = 5.0) -> Dict[str, Any]:
    import json, urllib.request
    url = f"http://127.0.0.1:6333{path}"
    data = None
    if body is not None:
        data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"Content-Type":"application/json"}, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            raw = r.read().decode("utf-8")
            try:
                parsed = json.loads(raw)
            except Exception:
                parsed = {"raw": raw[:4000]}
            return {"ok": True, "status": r.status, "data": parsed}
    except Exception as e:
        return {"ok": False, "error": str(e), "url": url}


def tool_qdrant_upsert_point(params: Dict[str, Any]) -> Dict[str, Any]:
    collection = params.get("collection", "empirica_notes")
    point_id = params.get("id")
    vector = params.get("vector", [])
    payload = params.get("payload", {})
    if point_id is None:
        return {"ok": False, "error": "id required"}
    body = {"points": [{"id": point_id, "vector": vector, "payload": payload}]}
    return _qdrant_http(f"/collections/{collection}/points?wait=true", method="PUT", body=body)


def tool_qdrant_search(params: Dict[str, Any]) -> Dict[str, Any]:
    collection = params.get("collection", "empirica_notes")
    vector = params.get("vector", [])
    limit = int(params.get("limit", 5))
    body = {"vector": vector, "limit": limit, "with_payload": True}
    return _qdrant_http(f"/collections/{collection}/points/search", method="POST", body=body)


def tool_qdrant_query_by_tag(params: Dict[str, Any]) -> Dict[str, Any]:
    collection = params.get("collection", "empirica_notes")
    tag_key = params.get("tag_key", "tag")
    tag_value = params.get("tag_value")
    if tag_value is None: return {"ok": False, "error": "tag_value required"}
    body = {
        "filter": {"must": [{"key": tag_key, "match": {"value": tag_value}}]},
        "with_payload": True,
        "limit": int(params.get("limit", 10))
    }
    return _qdrant_http(f"/collections/{collection}/points/scroll", method="POST", body=body)


def tool_qdrant_delete_points(params: Dict[str, Any]) -> Dict[str, Any]:
    collection = params.get("collection", "empirica_notes")
    ids = params.get("ids", [])
    if not ids: return {"ok": False, "error": "ids required"}
    body = {"points": ids}
    return _qdrant_http(f"/collections/{collection}/points/delete?wait=true", method="POST", body=body)


    collection = params.get("collection", "empirica_notes")
    tag_key = params.get("tag_key", "tag")
    tag_value = params.get("tag_value")
    if tag_value is None: return {"ok": False, "error": "tag_value required"}
    body = {
        "filter": {"must": [{"key": tag_key, "match": {"value": tag_value}}]},
        "with_payload": True,
        "limit": int(params.get("limit", 10))
    }
    return _qdrant_http(f"/collections/{collection}/points/scroll", method="POST", body=body)

# ------------------ MCM (SQLite) Tools ------------------

def tool_mcm_threads_summary(params: Dict[str, Any]) -> Dict[str, Any]:
    import sqlite3, time
    db = params.get("db_path", "ai_ecosystem_architecture/temporal_consciousness/memory_systems/enhanced_multi_session_reasoning.db")
    try:
        conn = sqlite3.connect(db)
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA busy_timeout=2000;")
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM reasoning_threads")
        total = cur.fetchone()[0]
        cur.execute("SELECT thread_id, thread_title, sessions_count, total_steps, last_updated FROM reasoning_threads ORDER BY last_updated DESC LIMIT ?", (int(params.get("limit", 10)),))
        rows = cur.fetchall()
        conn.close()
        return {"ok": True, "total_threads": total, "threads": rows}
    except Exception as e:
        return {"ok": False, "error": str(e), "db": db}


def tool_mcm_recent_steps(params: Dict[str, Any]) -> Dict[str, Any]:
    import sqlite3, time
    db = params.get("db_path", "ai_ecosystem_architecture/temporal_consciousness/memory_systems/enhanced_multi_session_reasoning.db")
    try:
        conn = sqlite3.connect(db)
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA busy_timeout=2000;")
        cur = conn.cursor()
        cur.execute("SELECT session_id, thread_id, chain_step, reasoning_type, timestamp FROM multi_session_reasoning_chains ORDER BY timestamp DESC LIMIT ?", (int(params.get("limit", 25)),))
        rows = cur.fetchall()
        conn.close()
        return {"ok": True, "steps": rows}
    except Exception as e:
        return {"ok": False, "error": str(e), "db": db}

# ------------------ Sentinel Tools ------------------

def _sentinel_http(path: str, timeout: float = 5.0) -> Dict[str, Any]:
    import urllib.request, json
    url = f"http://127.0.0.1:8988{path}"
    try:
        with urllib.request.urlopen(url, timeout=timeout) as r:
            raw = r.read().decode("utf-8")
            try:
                parsed = json.loads(raw)
            except Exception:
                parsed = {"raw": raw[:4000]}
            return {"ok": True, "status": r.status, "data": parsed}
    except Exception as e:
        return {"ok": False, "error": str(e), "url": url}


def tool_sentinel_health(params: Dict[str, Any]) -> Dict[str, Any]:
    return _sentinel_http("/v1/health")


def tool_sentinel_capabilities(params: Dict[str, Any]) -> Dict[str, Any]:
    return _sentinel_http("/v1/capabilities/list")

# ------------------ Registration ------------------
register_tool(
    "empirica.workspace.scan",
    "Scan workspace paths and return a compact listing",
    {"type": "object", "properties": {"path": {"type": "string"}, "max_entries": {"type": "integer"}}},
    {"type": "object"},
)
register_tool(
    "empirica.context.validate_file",
    "Validate that a file exists and return metadata",
    {"type": "object", "properties": {"path": {"type": "string"},}},
    {"type": "object"},
)
register_tool(
    "empirica.web.templates.generate",
    "Generate Empirica web templates",
    {"type": "object", "properties": {}},
    {"type": "object"},
)
register_tool(
    "empirica.web.server.status",
    "Check Empirica web server health",
    {"type": "object", "properties": {"url": {"type": "string"}}},
    {"type": "object"},
)
register_tool(
    "empirica.uncertainty.assess",
    "Assess uncertainty using AugieSDK if available",
    {"type": "object", "properties": {"ai_id": {"type": "string"}, "context": {"type": "object"}}},
    {"type": "object"},
)
register_tool(
    "sentry.fetch_full_event_context",
    "Fetch full Sentry event context via MCP",
    {"type": "object", "properties": {"issue_id": {"type": "string"}, "project_slug": {"type": "string"}}, "required": ["issue_id", "project_slug"]},
    {"type": "object"},
)
register_tool(
    "devtools.get_console_error_summary",
    "Get Chrome DevTools console error summary",
    {"type": "object", "properties": {"url": {"type": "string"}}},
    {"type": "object"},
)
register_tool(
    "devtools.get_network_requests",
    "Get network requests via Chrome DevTools MCP",
    {"type": "object", "properties": {"url": {"type": "string"}}},
    {"type": "object"},
)
register_tool(
    "devtools.get_performance_metrics",
    "Get performance metrics via Chrome DevTools MCP",
    {"type": "object", "properties": {"url": {"type": "string"}}},
    {"type": "object"},
)
register_tool(
    "correlator.correlate_sentry_with_browser",
    "Correlate Sentry production error with local browser state",
    {"type": "object", "properties": {"sentry_context": {"type": "object"}}},
    {"type": "object"},
)

register_tool(
    "manager.start_cascade",
    "Start a reasoning cascade via Manager API",
    {"type": "object", "properties": {"url": {"type": "string"}}},
    {"type": "object"},
)
register_tool(
    "docs.master_reference",
    "Return master reference manifest for AI onboarding",
    {"type": "object", "properties": {}},
    {"type": "object"},
)

# Dev Panel tools
register_tool(
    "devpanel.status",
    "Get local Dev Panel service status",
    {"type": "object", "properties": {"base_url": {"type": "string"}, "token": {"type": "string"}}},
    {"type": "object"},
)
register_tool(
    "devpanel.clean",
    "Clean logs and caches via Dev Panel",
    {"type": "object", "properties": {"base_url": {"type": "string"}, "token": {"type": "string"}}},
    {"type": "object"},
)
register_tool(
    "devpanel.rebuild_web",
    "Regenerate templates and restart web via Dev Panel",
    {"type": "object", "properties": {"base_url": {"type": "string"}, "token": {"type": "string"}}},
    {"type": "object"},
)
register_tool(
    "devpanel.change_request",
    "Submit a change request to the SimpleChangeManager via Dev Panel",
    {"type": "object", "properties": {"base_url": {"type": "string"}, "token": {"type": "string"}, "type": {"type": "string"}, "description": {"type": "string"}, "semantic_reasoning": {"type": "string"}, "source_html": {"type": "string"}, "target_element": {"type": "string"}, "link_text": {"type": "string"}, "old_url": {"type": "string"}, "new_url": {"type": "string"}, "reasoning": {"type": "string"}, "pages_affected": {"type": "array"}}},
    {"type": "object"},
)

# CSP tools
register_tool(
    "csp.status",
    "Get Collaborative Stream (CSP) status",
    {"type": "object", "properties": {"base_url": {"type": "string"}}},
    {"type": "object"},
)
register_tool(
    "csp.broadcast",
    "Broadcast an event to CSP",
    {"type": "object", "properties": {"base_url": {"type": "string"}, "event": {"type": "object"}}},
    {"type": "object"},
)
register_tool(
    "csp.fetch_events",
    "Fetch recent CSP events",
    {"type": "object", "properties": {"base_url": {"type": "string"}, "limit": {"type": "integer"}, "token": {"type": "string"}}},
    {"type": "object"},
)

# Qdrant tools
register_tool(
    "qdrant.upsert_point",
    "Upsert a point (vector + payload) into a Qdrant collection",
    {"type": "object", "properties": {"collection": {"type": "string"}, "id": {"type": "integer"}, "vector": {"type": "array"}, "payload": {"type": "object"}}, "required": ["id"]},
    {"type": "object"},
)
register_tool(
    "qdrant.search",
    "Search similar vectors in a Qdrant collection",
    {"type": "object", "properties": {"collection": {"type": "string"}, "vector": {"type": "array"}, "limit": {"type": "integer"}}},
    {"type": "object"},
)
register_tool(
    "qdrant.query_by_tag",
    "Query points by payload tag (scroll)",
    {"type": "object", "properties": {"collection": {"type": "string"}, "tag_key": {"type": "string"}, "tag_value": {"type": "string"}, "limit": {"type": "integer"}}, "required": ["tag_value"]},
    {"type": "object"},
)
register_tool(
    "qdrant.delete_points",
    "Delete points by IDs from a Qdrant collection",
    {"type": "object", "properties": {"collection": {"type": "string"}, "ids": {"type": "array"}}, "required": ["ids"]},
    {"type": "object"},
)

# Sentinel
register_tool(
    "sentinel.health",
    "Get Sentinel health",
    {"type": "object", "properties": {}},
    {"type": "object"},
)
register_tool(
    "sentinel.capabilities",
    "List Sentinel capabilities",
    {"type": "object", "properties": {}},
    {"type": "object"},
)

# MCM (SQLite) tools
register_tool(
    "mcm.threads_summary",
    "List MCM reasoning threads (SQLite)",
    {"type": "object", "properties": {"db_path": {"type": "string"}, "limit": {"type": "integer"}}},
    {"type": "object"},
)
register_tool(
    "mcm.recent_steps",
    "Fetch recent MCM reasoning steps (SQLite)",
    {"type": "object", "properties": {"db_path": {"type": "string"}, "limit": {"type": "integer"}}},
    {"type": "object"},
)

# Semantic Kit wrappers (implemented)
register_tool(
    "semantic.workspace_awareness",
    "Workspace inspection and navigation (direct SDK wrapper)",
    {"type": "object", "properties": {"map_file_path": {"type": "string"}, "assigned_to": {"type": "string"}}},
    {"type": "object"},
)
register_tool(
    "semantic.uncertainty_analysis",
    "8D uncertainty assessment (AugieSDK preferred)",
    {"type": "object", "properties": {"ai_id": {"type": "string"}, "context": {"type": "object"}}},
    {"type": "object"},
)
register_tool(
    "semantic.intelligent_navigation",
    "Navigate project intelligently (direct SDK wrapper with fallback)",
    {"type": "object", "properties": {"target": {"type": "string"}}},
    {"type": "object"},
)
register_tool(
    "semantic.context_validation",
    "Validate environment and inputs (direct SDK wrapper with fallback)",
    {"type": "object", "properties": {"target": {"type": "string"}}},
    {"type": "object"},
)

# Declare semantic component tool signatures
for name, desc in SEMANTIC_COMPONENTS:
    register_tool(
        name,
        f"{desc} (declared; implement via direct SDK wrapping)",
        {"type": "object", "properties": {"params": {"type": "object"}}},
        {"type": "object"},
    )


# Tool dispatch map
TOOL_FUNCS = {
    "empirica.workspace.scan": tool_empirica_workspace_scan,
    "empirica.context.validate_file": tool_empirica_context_validate_file,
    "empirica.web.templates.generate": tool_empirica_web_templates_generate,
    "empirica.web.server.status": tool_empirica_web_server_status,
    "empirica.uncertainty.assess": tool_empirica_uncertainty_assess,
    "sentry.fetch_full_event_context": tool_sentry_fetch_full_event_context,
    "devtools.get_console_error_summary": tool_devtools_get_console_error_summary,
    "devtools.get_network_requests": tool_devtools_get_network_requests,
    "devtools.get_performance_metrics": tool_devtools_get_performance_metrics,
    "correlator.correlate_sentry_with_browser": tool_correlator_correlate_sentry_with_browser,
    "manager.start_cascade": tool_manager_start_cascade,
    "docs.master_reference": tool_docs_master_reference,
    # Dev Panel
    "devpanel.status": tool_devpanel_status,
    "devpanel.clean": tool_devpanel_clean,
    "devpanel.rebuild_web": tool_devpanel_rebuild_web,
    "devpanel.change_request": tool_devpanel_change_request,
    # CSP
    "csp.status": tool_csp_status,
    "csp.broadcast": tool_csp_broadcast,
    "csp.fetch_events": tool_csp_fetch_events,
    # Qdrant
    "qdrant.upsert_point": tool_qdrant_upsert_point,
    "qdrant.search": tool_qdrant_search,
    "qdrant.query_by_tag": tool_qdrant_query_by_tag,
    "qdrant.delete_points": tool_qdrant_delete_points,
    # Sentinel
    "sentinel.health": tool_sentinel_health,
    "sentinel.capabilities": tool_sentinel_capabilities,
    # MCM
    "mcm.threads_summary": tool_mcm_threads_summary,
    "mcm.recent_steps": tool_mcm_recent_steps,
    # Semantic wrappers
    "semantic.workspace_awareness": tool_semantic_workspace_awareness,
    "semantic.uncertainty_analysis": tool_semantic_uncertainty_analysis,
    "semantic.intelligent_navigation": tool_semantic_intelligent_navigation,
    "semantic.context_validation": tool_semantic_context_validation,
}
for name, _ in SEMANTIC_COMPONENTS:
    TOOL_FUNCS.setdefault(name, tool_placeholder)

# Register dynamic semantic wrappers
TOOL_FUNCS.update({
    # Remaining semantic wrappers
    "semantic.collaboration_framework": tool_semantic_collaboration_framework,
    "semantic.advanced_collaboration": tool_semantic_advanced_collaboration,
    "semantic.workspace_status": tool_semantic_workspace_status,
    "semantic.security_audit": tool_semantic_security_audit,
    "semantic.docs_generation": tool_semantic_docs_generation,
    "semantic.change_management": tool_semantic_change_management,
    "semantic.template_operations": tool_semantic_template_operations,
    "semantic.web_validation": tool_semantic_web_validation,

    "semantic.meta_cognitive_evaluator": tool_semantic_meta_cognitive_evaluator,
    "semantic.empirical_performance_analyzer": tool_semantic_empirical_performance_analyzer,
    "semantic.functionality_analyzer": tool_semantic_functionality_analyzer,
    "semantic.code_intelligence_analyzer": tool_semantic_code_intelligence_analyzer,
    "semantic.security_monitoring": tool_semantic_security_monitoring,
    "semantic.environment_stabilization": tool_semantic_environment_stabilization,
    "semantic.runtime_validation": tool_semantic_runtime_validation,
    "semantic.proactive_monitor": tool_semantic_proactive_monitor,
    "semantic.advanced_investigation": tool_semantic_advanced_investigation,
    "semantic.context_aware_integration": tool_semantic_context_aware_integration,
    "semantic.intelligent_suggestions": tool_semantic_intelligent_suggestions,
    "semantic.universal_grounding": tool_semantic_universal_grounding,
    "semantic.metacognitive_cascade": tool_semantic_metacognitive_cascade,
    "semantic.context_monitoring": tool_semantic_context_monitoring,
})


# ------------------ MCP Loop (STDIO) ------------------

def run_stdio():
    correlator = ChromeDevToolsCorrelator()  # Pre-create; may be used by tools
    while True:
        line = sys.stdin.readline()
        if not line:
            break
        try:
            req = json.loads(line)
        except Exception:
            continue
        method = req.get("method")
        id_ = req.get("id")

        if method == "initialize":
            resp = mcp_response(id_, {
                "protocolVersion": "2024-11-05",
                "serverInfo": {"name": "empirica-mcp", "version": "0.1.0"},
                "capabilities": {"tools": {}},
            })
            print(json.dumps(resp), flush=True)
            continue

        if method == "tools/list":
            tools_list = [{
                "name": t["name"],
                "description": t["description"],
                "inputSchema": t["inputSchema"],
            } for t in TOOLS.values()]
            print(json.dumps(mcp_response(id_, {"tools": tools_list})), flush=True)
            continue

        if method == "tools/call":
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
                print(json.dumps(mcp_response(id_, error={"code": -32000, "message": str(e)})), flush=True)
            continue

        # Unknown method
        print(json.dumps(mcp_response(id_, error={"code": -32601, "message": f"Unknown method {method}"})), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--stdio", action="store_true", help="Run MCP server over stdio")
    args = parser.parse_args()
    if args.stdio:
        run_stdio()
    else:
        # Default to stdio if nothing specified
        run_stdio()
