#!/usr/bin/env python3
"""
Setup Claude Code Command - Configure Claude Code integration for Empirica

This command configures:
- Plugin files in ~/.claude/plugins/local/empirica-integration/
- CLAUDE.md system prompt in ~/.claude/CLAUDE.md
- Hooks in ~/.claude/settings.json (sentinel, compact, session lifecycle)
- MCP server in ~/.claude/mcp.json
- Marketplace registration

Replaces the bash install.sh for Homebrew users who already have empirica installed.

Author: Rovo Dev
Date: 2026-02-10
"""

import json
import logging
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

PLUGIN_NAME = "empirica-integration"
PLUGIN_VERSION = "1.5.0"


def _find_python() -> str:
    """Find a suitable Python >= 3.10, mimicking install.sh logic"""
    min_major, min_minor = 3, 10

    candidates = []

    # Check versioned binaries (highest first)
    for ver in [13, 12, 11, 10]:
        cmd = f"python3.{ver}"
        if shutil.which(cmd):
            candidates.append(cmd)

    # Check plain python3
    if shutil.which("python3"):
        candidates.append("python3")

    # Check macOS framework paths
    for ver in [13, 12, 11, 10]:
        fw = f"/Library/Frameworks/Python.framework/Versions/3.{ver}/bin/python3.{ver}"
        if Path(fw).exists():
            candidates.append(fw)

    # Check Homebrew paths
    for ver in [13, 12, 11, 10]:
        for prefix in ["/opt/homebrew", "/usr/local"]:
            brew = f"{prefix}/bin/python3.{ver}"
            if Path(brew).exists():
                candidates.append(brew)

    # Test each candidate for minimum version
    for py in candidates:
        try:
            result = subprocess.run(
                [py, "-c", "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"],
                capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0:
                py_ver = result.stdout.strip()
                major, minor = map(int, py_ver.split('.'))
                if major >= min_major and minor >= min_minor:
                    return py
        except Exception:
            continue

    # Fallback to current interpreter
    return sys.executable


def _get_plugin_source_dir() -> Optional[Path]:
    """Find the bundled plugin source directory"""
    # Method 1: Relative to this module's location
    module_dir = Path(__file__).parent.parent.parent  # empirica/cli/command_handlers -> empirica/
    bundled_path = module_dir / "plugins" / "claude-code-integration"
    if bundled_path.exists() and (bundled_path / "plugin.json").exists():
        return bundled_path

    # Method 2: Check if running from dev environment (plugins at repo root)
    repo_root = module_dir.parent
    dev_path = repo_root / "plugins" / "claude-code-integration"
    if dev_path.exists() and (dev_path / "plugin.json").exists():
        return dev_path

    return None


def _ensure_json_file(path: Path, default: dict) -> dict:
    """Ensure JSON file exists and return its contents"""
    if path.exists():
        try:
            with open(path) as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
    return default.copy()


def _write_json_file(path: Path, data: dict):
    """Write JSON file atomically"""
    temp_path = path.with_suffix('.tmp')
    with open(temp_path, 'w') as f:
        json.dump(data, f, indent=2)
    temp_path.rename(path)


def _hook_exists(hooks_list: list, pattern: str) -> bool:
    """Check if a hook with the given pattern already exists"""
    for hook_entry in hooks_list:
        for hook in hook_entry.get('hooks', []):
            cmd = hook.get('command', '')
            if pattern in cmd:
                return True
    return False


def handle_setup_claude_code_command(args):
    """Handle setup-claude-code command"""
    try:
        output_format = getattr(args, 'output', 'human')
        force = getattr(args, 'force', False)
        skip_mcp = getattr(args, 'skip_mcp', False)
        skip_claude_md = getattr(args, 'skip_claude_md', False)

        # Find bundled plugins
        source_dir = _get_plugin_source_dir()
        if not source_dir:
            if output_format == 'json':
                print(json.dumps({
                    "ok": False,
                    "error": "Could not find bundled plugin files",
                    "hint": "Run from a valid Empirica installation or dev environment"
                }, indent=2))
            else:
                print("❌ Error: Could not find bundled plugin files")
                print("   Run from a valid Empirica installation or dev environment")
            return None

        if output_format != 'json':
            print(f"🧠 Setting up Claude Code integration...")
            print(f"   Source: {source_dir}\n")

        # Find Python for hooks
        python_cmd = _find_python()
        if output_format != 'json':
            print(f"   Using Python: {python_cmd}")

        # Directories
        home = Path.home()
        claude_dir = home / ".claude"
        plugins_dir = claude_dir / "plugins" / "local"
        plugin_dir = plugins_dir / PLUGIN_NAME
        marketplace_dir = plugins_dir / ".claude-plugin"
        empirica_dir = home / ".empirica"

        # Create directories
        claude_dir.mkdir(parents=True, exist_ok=True)
        plugins_dir.mkdir(parents=True, exist_ok=True)
        marketplace_dir.mkdir(parents=True, exist_ok=True)
        empirica_dir.mkdir(parents=True, exist_ok=True)
        (empirica_dir / "instance_projects").mkdir(exist_ok=True)
        (empirica_dir / "statusline_cache").mkdir(exist_ok=True)

        # Bootstrap active_work.json
        active_work_file = empirica_dir / "active_work.json"
        if not active_work_file.exists():
            active_work = {
                "project_path": None,
                "folder_name": None,
                "claude_session_id": None,
                "empirica_session_id": None,
                "source": "setup-claude-code",
                "timestamp": datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S+0000')
            }
            _write_json_file(active_work_file, active_work)
            if output_format != 'json':
                print("   ✓ Created ~/.empirica/active_work.json")

        # ==================== INSTALL PLUGIN FILES ====================
        if output_format != 'json':
            print("\n📦 Installing plugin files...")

        if plugin_dir.exists() and not force:
            if output_format != 'json':
                print(f"   Plugin already exists at {plugin_dir}")
                print("   Use --force to reinstall")
        else:
            # Copy plugin directory
            if plugin_dir.exists():
                shutil.rmtree(plugin_dir)

            # Copy excluding __pycache__ and .git
            def ignore_patterns(directory, files):
                return [f for f in files if f in ('__pycache__', '.git', '.pyc')]

            shutil.copytree(source_dir, plugin_dir, ignore=ignore_patterns)

            # Make hooks executable
            hooks_dir = plugin_dir / "hooks"
            if hooks_dir.exists():
                for hook_file in hooks_dir.glob("*.py"):
                    hook_file.chmod(0o755)
                for hook_file in hooks_dir.glob("*.sh"):
                    hook_file.chmod(0o755)

            scripts_dir = plugin_dir / "scripts"
            if scripts_dir.exists():
                for script_file in scripts_dir.glob("*.py"):
                    script_file.chmod(0o755)

            if output_format != 'json':
                print(f"   ✓ Plugin installed to {plugin_dir}")

        # ==================== INSTALL CLAUDE.md ====================
        if not skip_claude_md:
            if output_format != 'json':
                print("\n📝 Installing CLAUDE.md...")

            claude_md_src = plugin_dir / "templates" / "CLAUDE.md"
            claude_md_dst = claude_dir / "CLAUDE.md"

            if claude_md_src.exists():
                if claude_md_dst.exists():
                    backup = claude_dir / "CLAUDE.md.bak"
                    shutil.copy2(claude_md_dst, backup)
                    if output_format != 'json':
                        print("   Backed up existing CLAUDE.md to CLAUDE.md.bak")

                shutil.copy2(claude_md_src, claude_md_dst)
                if output_format != 'json':
                    print("   ✓ CLAUDE.md installed to ~/.claude/CLAUDE.md")
            else:
                if output_format != 'json':
                    print("   ⚠️  CLAUDE.md template not found in plugin")

        # ==================== CONFIGURE SETTINGS.JSON ====================
        if output_format != 'json':
            print("\n⚙️  Configuring settings.json...")

        settings_file = claude_dir / "settings.json"
        settings = _ensure_json_file(settings_file, {})

        # Ensure enabledPlugins exists
        if 'enabledPlugins' not in settings:
            settings['enabledPlugins'] = {}

        # Enable the plugin
        plugin_key = f"{PLUGIN_NAME}@local"
        settings['enabledPlugins'][plugin_key] = True
        if output_format != 'json':
            print("   ✓ Plugin enabled")

        # Configure StatusLine
        if 'statusLine' not in settings:
            statusline_script = plugin_dir / "scripts" / "statusline_empirica.py"
            settings['statusLine'] = {
                "type": "command",
                "command": f"{python_cmd} {statusline_script}"
            }
            if output_format != 'json':
                print("   ✓ StatusLine configured")
        else:
            if output_format != 'json':
                print("   StatusLine already configured")

        # Ensure hooks structure
        if 'hooks' not in settings:
            settings['hooks'] = {}

        # Configure PreToolUse (Sentinel) hooks
        if 'PreToolUse' not in settings['hooks']:
            settings['hooks']['PreToolUse'] = []

        sentinel_script = f"{python_cmd} {plugin_dir}/hooks/sentinel-gate.py"
        if not _hook_exists(settings['hooks']['PreToolUse'], 'sentinel-gate'):
            settings['hooks']['PreToolUse'].extend([
                {
                    "matcher": "Edit|Write",
                    "hooks": [{"type": "command", "command": sentinel_script, "timeout": 10}]
                },
                {
                    "matcher": "Bash",
                    "hooks": [{"type": "command", "command": sentinel_script, "timeout": 10}]
                }
            ])
            if output_format != 'json':
                print("   ✓ PreToolUse (Sentinel) hooks configured")
        else:
            if output_format != 'json':
                print("   PreToolUse hooks already configured")

        # Configure PreCompact hook
        if 'PreCompact' not in settings['hooks']:
            settings['hooks']['PreCompact'] = []

        precompact_script = f"{python_cmd} {plugin_dir}/hooks/pre-compact.py"
        if not _hook_exists(settings['hooks']['PreCompact'], 'pre-compact.py'):
            settings['hooks']['PreCompact'].append({
                "matcher": "auto|manual",
                "hooks": [{"type": "command", "command": precompact_script, "timeout": 30}]
            })
            if output_format != 'json':
                print("   ✓ PreCompact hook configured")
        else:
            if output_format != 'json':
                print("   PreCompact hook already configured")

        # Configure SessionStart hooks
        if 'SessionStart' not in settings['hooks']:
            settings['hooks']['SessionStart'] = []

        postcompact_script = f"{python_cmd} {plugin_dir}/hooks/post-compact.py"
        sessioninit_script = f"{python_cmd} {plugin_dir}/hooks/session-init.py"
        ewm_script = f"{python_cmd} {plugin_dir}/hooks/ewm-protocol-loader.py"

        if not _hook_exists(settings['hooks']['SessionStart'], 'post-compact.py'):
            settings['hooks']['SessionStart'].extend([
                {
                    "matcher": "compact",
                    "hooks": [
                        {"type": "command", "command": postcompact_script, "timeout": 30},
                        {"type": "command", "command": ewm_script, "timeout": 10, "allowFailure": True}
                    ]
                },
                {
                    "matcher": "new|fresh",
                    "hooks": [
                        {"type": "command", "command": sessioninit_script, "timeout": 30},
                        {"type": "command", "command": ewm_script, "timeout": 10, "allowFailure": True}
                    ]
                }
            ])
            if output_format != 'json':
                print("   ✓ SessionStart hooks configured")
        else:
            if output_format != 'json':
                print("   SessionStart hooks already configured")

        # Configure SessionEnd hooks
        if 'SessionEnd' not in settings['hooks']:
            settings['hooks']['SessionEnd'] = []

        postflight_script = f"{python_cmd} {plugin_dir}/hooks/session-end-postflight.py"
        curate_script = f"{python_cmd} {plugin_dir}/hooks/curate-snapshots.py --output json"

        if not _hook_exists(settings['hooks']['SessionEnd'], 'session-end-postflight.py'):
            settings['hooks']['SessionEnd'].append({
                "matcher": ".*",
                "hooks": [
                    {"type": "command", "command": postflight_script, "timeout": 20},
                    {"type": "command", "command": curate_script, "timeout": 15, "allowFailure": True}
                ]
            })
            if output_format != 'json':
                print("   ✓ SessionEnd hooks configured")
        else:
            if output_format != 'json':
                print("   SessionEnd hooks already configured")

        # Configure SubagentStart hook
        if 'SubagentStart' not in settings['hooks']:
            settings['hooks']['SubagentStart'] = []

        substart_script = f"{python_cmd} {plugin_dir}/hooks/subagent-start.py"
        if not _hook_exists(settings['hooks']['SubagentStart'], 'subagent-start.py'):
            settings['hooks']['SubagentStart'].append({
                "matcher": ".*",
                "hooks": [{"type": "command", "command": substart_script, "timeout": 10, "allowFailure": True}]
            })
            if output_format != 'json':
                print("   ✓ SubagentStart hook configured")
        else:
            if output_format != 'json':
                print("   SubagentStart hook already configured")

        # Configure SubagentStop hook
        if 'SubagentStop' not in settings['hooks']:
            settings['hooks']['SubagentStop'] = []

        substop_script = f"{python_cmd} {plugin_dir}/hooks/subagent-stop.py"
        if not _hook_exists(settings['hooks']['SubagentStop'], 'subagent-stop.py'):
            settings['hooks']['SubagentStop'].append({
                "matcher": ".*",
                "hooks": [{"type": "command", "command": substop_script, "timeout": 15, "allowFailure": True}]
            })
            if output_format != 'json':
                print("   ✓ SubagentStop hook configured")
        else:
            if output_format != 'json':
                print("   SubagentStop hook already configured")

        # Configure UserPromptSubmit hook
        if 'UserPromptSubmit' not in settings['hooks']:
            settings['hooks']['UserPromptSubmit'] = []

        router_script = f"{python_cmd} {plugin_dir}/hooks/tool-router.py"
        if not _hook_exists(settings['hooks']['UserPromptSubmit'], 'tool-router.py'):
            settings['hooks']['UserPromptSubmit'].append({
                "matcher": ".*",
                "hooks": [{"type": "command", "command": router_script, "timeout": 3, "allowFailure": True}]
            })
            if output_format != 'json':
                print("   ✓ UserPromptSubmit hook configured")
        else:
            if output_format != 'json':
                print("   UserPromptSubmit hook already configured")

        # Write settings.json
        _write_json_file(settings_file, settings)

        # ==================== MARKETPLACE REGISTRATION ====================
        if output_format != 'json':
            print("\n📋 Registering in marketplace...")

        marketplace_file = marketplace_dir / "marketplace.json"
        marketplace = _ensure_json_file(marketplace_file, {
            "$schema": "https://anthropic.com/claude-code/marketplace.schema.json",
            "name": "local",
            "description": "Local development plugins",
            "owner": {"name": "Local", "email": "dev@localhost"},
            "plugins": []
        })

        # Add plugin to marketplace if not present
        plugin_names = [p.get('name') for p in marketplace.get('plugins', [])]
        if PLUGIN_NAME not in plugin_names:
            marketplace.setdefault('plugins', []).append({
                "name": PLUGIN_NAME,
                "description": "Noetic firewall + CASCADE workflow automation for Claude Code",
                "version": PLUGIN_VERSION,
                "author": {"name": "Empirica Project", "url": "https://github.com/Nubaeon/empirica"},
                "source": f"./{PLUGIN_NAME}",
                "category": "productivity"
            })
            _write_json_file(marketplace_file, marketplace)
            if output_format != 'json':
                print("   ✓ Added to marketplace.json")

        # ==================== INSTALLED PLUGINS REGISTRATION ====================
        installed_plugins_file = claude_dir / "plugins" / "installed_plugins.json"
        installed_plugins = _ensure_json_file(installed_plugins_file, {"version": 2, "plugins": {}})

        install_date = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")
        installed_plugins['plugins'][plugin_key] = [{
            "scope": "user",
            "installPath": str(plugin_dir),
            "version": PLUGIN_VERSION,
            "installedAt": install_date,
            "lastUpdated": install_date,
            "isLocal": True
        }]
        _write_json_file(installed_plugins_file, installed_plugins)
        if output_format != 'json':
            print("   ✓ Added to installed_plugins.json")

        # ==================== KNOWN MARKETPLACES ====================
        known_marketplaces_file = claude_dir / "plugins" / "known_marketplaces.json"
        known_marketplaces = _ensure_json_file(known_marketplaces_file, {})

        if 'local' not in known_marketplaces:
            known_marketplaces['local'] = {
                "source": {"source": "directory", "path": str(plugins_dir)},
                "installLocation": str(plugins_dir),
                "lastUpdated": install_date
            }
            _write_json_file(known_marketplaces_file, known_marketplaces)
            if output_format != 'json':
                print("   ✓ Local marketplace registered")

        # ==================== MCP SERVER ====================
        mcp_installed = False
        mcp_cmd = None

        if not skip_mcp:
            if output_format != 'json':
                print("\n🔌 Configuring MCP server...")

            # Find empirica-mcp
            mcp_cmd = shutil.which("empirica-mcp")
            if not mcp_cmd:
                local_bin = home / ".local" / "bin" / "empirica-mcp"
                if local_bin.exists():
                    mcp_cmd = str(local_bin)

            if not mcp_cmd:
                # Try to install via pipx
                if shutil.which("pipx"):
                    if output_format != 'json':
                        print("   Installing empirica-mcp via pipx...")
                    try:
                        result = subprocess.run(
                            ["pipx", "install", "empirica-mcp"],
                            capture_output=True, text=True, timeout=120
                        )
                        if result.returncode == 0:
                            mcp_cmd = shutil.which("empirica-mcp")
                            if not mcp_cmd:
                                mcp_cmd = str(home / ".local" / "bin" / "empirica-mcp")
                            if output_format != 'json':
                                print("   ✓ empirica-mcp installed via pipx")
                        else:
                            if output_format != 'json':
                                print(f"   ⚠️  pipx install failed: {result.stderr[:100]}")
                    except Exception as e:
                        if output_format != 'json':
                            print(f"   ⚠️  pipx install failed: {e}")
                else:
                    if output_format != 'json':
                        print("   ⚠️  pipx not available - install empirica-mcp manually:")
                        print("      pipx install empirica-mcp")

            if mcp_cmd:
                mcp_file = claude_dir / "mcp.json"
                mcp_config = _ensure_json_file(mcp_file, {"mcpServers": {}})

                if 'empirica' not in mcp_config.get('mcpServers', {}):
                    mcp_config.setdefault('mcpServers', {})['empirica'] = {
                        "command": mcp_cmd,
                        "args": [],
                        "type": "stdio",
                        "env": {"EMPIRICA_EPISTEMIC_MODE": "true"},
                        "tools": ["*"],
                        "description": "Empirica epistemic framework - CASCADE workflow, goals, findings"
                    }
                    _write_json_file(mcp_file, mcp_config)
                    mcp_installed = True
                    if output_format != 'json':
                        print("   ✓ MCP server configured in ~/.claude/mcp.json")
                else:
                    mcp_installed = True
                    if output_format != 'json':
                        print("   MCP server already configured")

        # ==================== OUTPUT ====================
        if output_format == 'json':
            result = {
                "ok": True,
                "plugin_dir": str(plugin_dir),
                "claude_md": str(claude_dir / "CLAUDE.md") if not skip_claude_md else None,
                "settings_file": str(settings_file),
                "mcp_configured": mcp_installed,
                "mcp_command": mcp_cmd,
                "hooks_configured": [
                    "PreToolUse (Sentinel)",
                    "PreCompact",
                    "SessionStart",
                    "SessionEnd",
                    "SubagentStart",
                    "SubagentStop",
                    "UserPromptSubmit"
                ],
                "message": "Claude Code integration configured successfully"
            }
            print(json.dumps(result, indent=2))
        else:
            print("\n" + "━" * 60)
            print(f"✅ {PLUGIN_NAME} v{PLUGIN_VERSION} configured successfully!")
            print("━" * 60)
            print()
            print(f"📍 Plugin:     {plugin_dir}")
            print(f"📝 CLAUDE.md:  ~/.claude/CLAUDE.md")
            print(f"⚙️  Settings:   ~/.claude/settings.json")
            print()
            print("━" * 60)
            print("WHAT'S CONFIGURED:")
            print("━" * 60)
            print()
            print("🛡️  Sentinel Gate (Noetic Firewall)")
            print("    - Noetic tools (Read, Grep, etc.) always allowed")
            print("    - Praxic tools (Edit, Write, Bash) require CHECK")
            print()
            print("📋 CASCADE Workflow (Pre/Post Compact)")
            print("    - Auto-saves epistemic state before compact")
            print("    - Auto-loads context after compact")
            print()
            print("📊 StatusLine")
            print("    - Shows session ID, phase, know/uncertainty vectors")
            print()
            if mcp_installed:
                print("🔌 MCP Server")
                print("    - Full Empirica API available to Claude")
                print()
            print("🎯 Skills")
            print("    - /empirica - Full command reference")
            print()
            print("━" * 60)
            print("NEXT STEPS:")
            print("━" * 60)
            print()
            print("1. Restart Claude Code to load the plugin")
            print()
            print("2. Verify with: /plugin")
            print(f"   Should show: {PLUGIN_NAME}@local")
            print()
            print("3. Connect MCP server: /mcp")
            print("   Should show: empirica connected")
            print()
            print("To disable sentinel gating temporarily:")
            print("  export EMPIRICA_SENTINEL_LOOPING=false")
            print()
            print("🧠 Happy epistemic coding!")

        return {
            "ok": True,
            "plugin_dir": str(plugin_dir),
            "mcp_configured": mcp_installed
        }

    except Exception as e:
        if getattr(args, 'output', 'human') == 'json':
            print(json.dumps({
                "ok": False,
                "error": str(e)
            }, indent=2))
        else:
            from ..cli_utils import handle_cli_error
            handle_cli_error(e, "Setup Claude Code", getattr(args, 'verbose', False))
        return None
