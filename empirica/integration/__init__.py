"""
Empirica Integration Module

External system integrations for Empirica:
- IDE integrations (VS Code, JetBrains, etc.)
- CI/CD pipeline hooks
- External tool connectors
- Third-party service adapters

Components:
- IDEConnector: Base class for IDE integrations
- CIHooks: Hooks for continuous integration pipelines
- WebhookHandler: Handle incoming webhooks

Usage:
    from empirica.integration import get_integration

    # Get VS Code integration
    vscode = get_integration("vscode")
    vscode.sync_session(session_id)

    # Set up CI hook
    ci_hook = CIHooks(project_id)
    ci_hook.on_build_complete(callback)
"""
