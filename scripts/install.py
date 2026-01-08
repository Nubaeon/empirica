#!/usr/bin/env python3
"""
Empirica Cross-Platform Installer

Installs Empirica with:
- Claude Code plugin (hooks for epistemic continuity)
- empirica-framework skill
- Environment variable configuration
- Optional Qdrant + Ollama embeddings setup

Works on: Linux, macOS, Windows
"""

import json
import os
import platform
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional


# =============================================================================
# Configuration
# =============================================================================

EMPIRICA_VERSION = "1.3.0"

# Recommended embeddings model (small, fast, good quality)
RECOMMENDED_EMBEDDINGS_MODEL = "nomic-embed-text"
ALTERNATIVE_EMBEDDINGS_MODEL = "mxbai-embed-large"

# Default Qdrant URL
DEFAULT_QDRANT_URL = "http://localhost:6333"

# Colors for terminal output
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

    @classmethod
    def disable(cls):
        """Disable colors for Windows CMD without ANSI support."""
        cls.HEADER = cls.BLUE = cls.CYAN = cls.GREEN = ''
        cls.YELLOW = cls.RED = cls.ENDC = cls.BOLD = ''


# Disable colors on Windows if not in a modern terminal
if platform.system() == "Windows" and not os.environ.get("WT_SESSION"):
    Colors.disable()


# =============================================================================
# Utility Functions
# =============================================================================

def print_header(text: str):
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{text.center(60)}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}\n")


def print_step(step: int, text: str):
    print(f"{Colors.CYAN}[{step}]{Colors.ENDC} {text}")


def print_success(text: str):
    print(f"{Colors.GREEN}✓{Colors.ENDC} {text}")


def print_warning(text: str):
    print(f"{Colors.YELLOW}⚠{Colors.ENDC} {text}")


def print_error(text: str):
    print(f"{Colors.RED}✗{Colors.ENDC} {text}")


def print_info(text: str):
    print(f"{Colors.BLUE}ℹ{Colors.ENDC} {text}")


def ask_yes_no(question: str, default: bool = True) -> bool:
    """Ask a yes/no question and return boolean."""
    default_str = "Y/n" if default else "y/N"
    while True:
        response = input(f"{question} [{default_str}]: ").strip().lower()
        if not response:
            return default
        if response in ('y', 'yes'):
            return True
        if response in ('n', 'no'):
            return False
        print("Please answer 'yes' or 'no'")


def ask_choice(question: str, choices: list[str], default: int = 0) -> str:
    """Ask user to choose from a list of options."""
    print(f"\n{question}")
    for i, choice in enumerate(choices):
        marker = f"{Colors.GREEN}→{Colors.ENDC}" if i == default else " "
        print(f"  {marker} [{i+1}] {choice}")

    while True:
        response = input(f"Choice [1-{len(choices)}, default={default+1}]: ").strip()
        if not response:
            return choices[default]
        try:
            idx = int(response) - 1
            if 0 <= idx < len(choices):
                return choices[idx]
        except ValueError:
            pass
        print(f"Please enter a number between 1 and {len(choices)}")


def get_home_dir() -> Path:
    """Get user home directory cross-platform."""
    return Path.home()


def get_claude_dir() -> Path:
    """Get Claude Code configuration directory."""
    return get_home_dir() / ".claude"


def get_empirica_dir() -> Path:
    """Get Empirica data directory."""
    return get_home_dir() / ".empirica"


def get_shell_profile() -> Optional[Path]:
    """Get the user's shell profile file."""
    home = get_home_dir()

    if platform.system() == "Windows":
        # PowerShell profile
        ps_profile = home / "Documents" / "PowerShell" / "Microsoft.PowerShell_profile.ps1"
        if ps_profile.parent.exists():
            return ps_profile
        return None

    # Unix-like systems
    shell = os.environ.get("SHELL", "")
    if "zsh" in shell:
        return home / ".zshrc"
    elif "bash" in shell:
        bashrc = home / ".bashrc"
        if bashrc.exists():
            return bashrc
        return home / ".bash_profile"
    elif "fish" in shell:
        return home / ".config" / "fish" / "config.fish"

    # Default to bashrc
    return home / ".bashrc"


def run_command(cmd: list[str], check: bool = True) -> subprocess.CompletedProcess:
    """Run a command and return the result."""
    try:
        return subprocess.run(cmd, capture_output=True, text=True, check=check)
    except subprocess.CalledProcessError as e:
        print_error(f"Command failed: {' '.join(cmd)}")
        print_error(f"Error: {e.stderr}")
        raise


def check_command_exists(cmd: str) -> bool:
    """Check if a command exists on the system."""
    return shutil.which(cmd) is not None


def get_python_command() -> str:
    """Get the correct Python command for this system."""
    # Try python3 first (Unix convention)
    if check_command_exists("python3"):
        return "python3"
    # Fall back to python (Windows, or unified installs)
    if check_command_exists("python"):
        return "python"
    return "python"


# =============================================================================
# Installation Steps
# =============================================================================

def check_prerequisites() -> dict:
    """Check system prerequisites and return status."""
    print_header("Checking Prerequisites")

    status = {
        "python": False,
        "git": False,
        "empirica": False,
        "ollama": False,
        "qdrant": False,
    }

    # Python
    python_cmd = get_python_command()
    if check_command_exists(python_cmd):
        result = run_command([python_cmd, "--version"], check=False)
        version = result.stdout.strip() or result.stderr.strip()
        print_success(f"Python: {version}")
        status["python"] = True
    else:
        print_error("Python not found - required")

    # Git
    if check_command_exists("git"):
        result = run_command(["git", "--version"], check=False)
        print_success(f"Git: {result.stdout.strip()}")
        status["git"] = True
    else:
        print_warning("Git not found - recommended for version control features")

    # Empirica
    if check_command_exists("empirica"):
        result = run_command(["empirica", "--version"], check=False)
        print_success(f"Empirica CLI: installed")
        status["empirica"] = True
    else:
        print_warning("Empirica CLI not found - will attempt to install")

    # Ollama (optional)
    if check_command_exists("ollama"):
        print_success("Ollama: installed (for local embeddings)")
        status["ollama"] = True
    else:
        print_info("Ollama: not installed (optional, for local embeddings)")

    # Qdrant (check if running)
    try:
        import urllib.request
        urllib.request.urlopen(DEFAULT_QDRANT_URL, timeout=2)
        print_success(f"Qdrant: running at {DEFAULT_QDRANT_URL}")
        status["qdrant"] = True
    except Exception:
        print_info("Qdrant: not running (optional, for semantic search)")

    return status


def install_empirica_package():
    """Install Empirica Python package if not present."""
    print_header("Installing Empirica Package")

    if check_command_exists("empirica"):
        print_success("Empirica already installed")
        return

    print_step(1, "Installing empirica via pip...")
    python_cmd = get_python_command()

    try:
        run_command([python_cmd, "-m", "pip", "install", "empirica"])
        print_success("Empirica package installed")
    except Exception as e:
        print_warning(f"pip install failed, trying from current directory...")
        # Try installing from local source if we're in the empirica repo
        if (Path.cwd() / "pyproject.toml").exists():
            run_command([python_cmd, "-m", "pip", "install", "-e", "."])
            print_success("Empirica installed from source")
        else:
            print_error(f"Failed to install Empirica: {e}")
            print_info("Please install manually: pip install empirica")


def create_directory_structure():
    """Create necessary directories."""
    print_header("Creating Directory Structure")

    directories = [
        get_empirica_dir(),
        get_empirica_dir() / "sessions",
        get_empirica_dir() / "lessons",
        get_claude_dir(),
        get_claude_dir() / "plugins" / "local",
        get_claude_dir() / "skills",
    ]

    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
        print_success(f"Created: {directory}")


def install_claude_plugin(source_dir: Optional[Path] = None):
    """Install the Claude Code plugin."""
    print_header("Installing Claude Code Plugin")

    claude_plugins = get_claude_dir() / "plugins" / "local"
    plugin_dest = claude_plugins / "empirica-integration"

    # Find plugin source
    if source_dir and (source_dir / "plugins" / "claude-code-integration").exists():
        plugin_source = source_dir / "plugins" / "claude-code-integration"
    elif (Path.cwd() / "plugins" / "claude-code-integration").exists():
        plugin_source = Path.cwd() / "plugins" / "claude-code-integration"
    else:
        print_warning("Plugin source not found in current directory")
        print_info("Please ensure you're running from the Empirica repository root")
        print_info("Or specify the source directory with --source")
        return False

    # Copy plugin files
    print_step(1, f"Copying plugin from {plugin_source}")
    if plugin_dest.exists():
        shutil.rmtree(plugin_dest)
    shutil.copytree(plugin_source, plugin_dest)
    print_success(f"Plugin copied to {plugin_dest}")

    # Fix hooks.json for Windows compatibility
    hooks_json = plugin_dest / "hooks" / "hooks.json"
    if hooks_json.exists():
        print_step(2, "Updating hooks for cross-platform compatibility")
        with open(hooks_json) as f:
            hooks = json.load(f)

        # Use 'python' on Windows, 'python3' elsewhere
        python_cmd = "python" if platform.system() == "Windows" else "python3"
        hooks_str = json.dumps(hooks)
        hooks_str = hooks_str.replace("python3 ", f"{python_cmd} ")
        hooks = json.loads(hooks_str)

        with open(hooks_json, 'w') as f:
            json.dump(hooks, f, indent=2)
        print_success("Hooks updated for this platform")

    return True


def configure_plugin_registry():
    """Configure Claude Code plugin registry files."""
    print_header("Configuring Plugin Registry")

    claude_dir = get_claude_dir()
    plugins_dir = claude_dir / "plugins"
    local_dir = plugins_dir / "local"

    # Use forward slashes even on Windows for JSON (works in most tools)
    local_str = str(local_dir).replace("\\", "/")
    plugin_str = str(local_dir / "empirica-integration").replace("\\", "/")

    timestamp = datetime.now().strftime("%Y-%m-%dT%H:%M:%S.000Z")

    # 1. known_marketplaces.json
    print_step(1, "Creating known_marketplaces.json")
    marketplaces_file = plugins_dir / "known_marketplaces.json"
    marketplaces = {}
    if marketplaces_file.exists():
        try:
            with open(marketplaces_file) as f:
                marketplaces = json.load(f)
        except json.JSONDecodeError:
            pass

    marketplaces["local"] = {
        "source": {
            "source": "directory",
            "path": local_str
        },
        "installLocation": local_str,
        "lastUpdated": timestamp
    }

    with open(marketplaces_file, 'w') as f:
        json.dump(marketplaces, f, indent=2)
    print_success(f"Updated {marketplaces_file}")

    # 2. marketplace.json in local/.claude-plugin/
    print_step(2, "Creating local marketplace catalog")
    marketplace_dir = local_dir / ".claude-plugin"
    marketplace_dir.mkdir(parents=True, exist_ok=True)

    marketplace = {
        "$schema": "https://anthropic.com/claude-code/marketplace.schema.json",
        "name": "local",
        "description": "Local Empirica plugins",
        "owner": {
            "name": "Empirica",
            "email": "support@empirica.dev"
        },
        "plugins": [
            {
                "name": "empirica-integration",
                "description": "Epistemic continuity across memory compacting",
                "version": EMPIRICA_VERSION,
                "author": {
                    "name": "Empirica Team",
                    "email": "support@empirica.dev"
                },
                "source": "./empirica-integration",
                "category": "productivity"
            }
        ]
    }

    with open(marketplace_dir / "marketplace.json", 'w') as f:
        json.dump(marketplace, f, indent=2)
    print_success(f"Created {marketplace_dir / 'marketplace.json'}")

    # 3. installed_plugins.json
    print_step(3, "Registering plugin installation")
    installed_file = plugins_dir / "installed_plugins.json"
    installed = {"version": 2, "plugins": {}}
    if installed_file.exists():
        try:
            with open(installed_file) as f:
                installed = json.load(f)
        except json.JSONDecodeError:
            pass

    installed["plugins"]["empirica-integration@local"] = [
        {
            "scope": "user",
            "installPath": plugin_str,
            "version": EMPIRICA_VERSION,
            "installedAt": timestamp,
            "lastUpdated": timestamp,
            "isLocal": True
        }
    ]

    with open(installed_file, 'w') as f:
        json.dump(installed, f, indent=2)
    print_success(f"Updated {installed_file}")

    # 4. settings.json - enable plugin
    print_step(4, "Enabling plugin in settings")
    settings_file = claude_dir / "settings.json"
    settings = {}
    if settings_file.exists():
        try:
            with open(settings_file) as f:
                settings = json.load(f)
        except json.JSONDecodeError:
            pass

    if "enabledPlugins" not in settings:
        settings["enabledPlugins"] = {}
    settings["enabledPlugins"]["empirica-integration@local"] = True

    with open(settings_file, 'w') as f:
        json.dump(settings, f, indent=2)
    print_success(f"Enabled plugin in {settings_file}")


def install_skill(source_dir: Optional[Path] = None):
    """Install the empirica-framework skill."""
    print_header("Installing Empirica Skill")

    skills_dir = get_claude_dir() / "skills"
    skill_dest = skills_dir / "empirica-framework"

    # Find skill source
    if source_dir:
        skill_source = source_dir / "plugins" / "claude-code-integration" / "skills" / "empirica-framework"
    else:
        skill_source = Path.cwd() / "plugins" / "claude-code-integration" / "skills" / "empirica-framework"

    if not skill_source.exists():
        # Try the installed plugin location
        skill_source = get_claude_dir() / "plugins" / "local" / "empirica-integration" / "skills" / "empirica-framework"

    if not skill_source.exists():
        print_warning("Skill source not found")
        return False

    print_step(1, f"Copying skill from {skill_source}")
    if skill_dest.exists():
        shutil.rmtree(skill_dest)
    shutil.copytree(skill_source, skill_dest)
    print_success(f"Skill installed to {skill_dest}")

    return True


def configure_environment(config: dict) -> list[tuple[str, str]]:
    """Generate environment variable configuration."""
    print_header("Configuring Environment")

    env_vars = []

    # Core Empirica settings
    if config.get("autopilot"):
        env_vars.append(("EMPIRICA_AUTOPILOT_MODE", "true"))
        print_success("Autopilot mode: ENABLED")

    if config.get("auto_postflight"):
        env_vars.append(("EMPIRICA_AUTO_POSTFLIGHT", "true"))
        print_success("Auto-postflight: ENABLED")

    if config.get("sentinel_looping", True):
        env_vars.append(("EMPIRICA_SENTINEL_LOOPING", "true"))
        print_success("Sentinel looping: ENABLED")
    else:
        env_vars.append(("EMPIRICA_SENTINEL_LOOPING", "false"))
        print_info("Sentinel looping: DISABLED")

    # Qdrant configuration
    if config.get("qdrant_url"):
        env_vars.append(("EMPIRICA_QDRANT_URL", config["qdrant_url"]))
        print_success(f"Qdrant URL: {config['qdrant_url']}")

    # Embeddings configuration
    if config.get("embeddings_provider"):
        env_vars.append(("EMPIRICA_EMBEDDINGS_PROVIDER", config["embeddings_provider"]))
        print_success(f"Embeddings provider: {config['embeddings_provider']}")

    if config.get("embeddings_model"):
        env_vars.append(("EMPIRICA_EMBEDDINGS_MODEL", config["embeddings_model"]))
        print_success(f"Embeddings model: {config['embeddings_model']}")

    if config.get("ollama_url"):
        env_vars.append(("EMPIRICA_OLLAMA_URL", config["ollama_url"]))

    # Status line
    env_vars.append(("EMPIRICA_STATUS_MODE", "metacog"))
    print_success("Status mode: metacog (shows epistemic vectors)")

    return env_vars


def write_shell_config(env_vars: list[tuple[str, str]]):
    """Write environment variables to shell profile."""
    print_header("Updating Shell Profile")

    profile = get_shell_profile()
    if not profile:
        print_warning("Could not determine shell profile")
        print_info("Please add these environment variables manually:")
        for name, value in env_vars:
            print(f"  export {name}=\"{value}\"")
        return

    print_step(1, f"Updating {profile}")

    # Read existing content
    existing = ""
    if profile.exists():
        existing = profile.read_text()

    # Check if Empirica section already exists
    marker_start = "# >>> Empirica configuration >>>"
    marker_end = "# <<< Empirica configuration <<<"

    if marker_start in existing:
        # Replace existing section
        start_idx = existing.index(marker_start)
        end_idx = existing.index(marker_end) + len(marker_end)
        before = existing[:start_idx]
        after = existing[end_idx:]
    else:
        before = existing
        after = ""
        if not existing.endswith("\n"):
            before += "\n"

    # Generate new section
    is_fish = "fish" in str(profile)
    is_powershell = profile.suffix == ".ps1"

    lines = ["\n" + marker_start]
    for name, value in env_vars:
        if is_fish:
            lines.append(f'set -gx {name} "{value}"')
        elif is_powershell:
            lines.append(f'$env:{name} = "{value}"')
        else:
            lines.append(f'export {name}="{value}"')
    lines.append(marker_end + "\n")

    new_section = "\n".join(lines)

    # Write updated profile
    profile.parent.mkdir(parents=True, exist_ok=True)
    profile.write_text(before + new_section + after)
    print_success(f"Updated {profile}")

    print_info("Run the following to apply changes:")
    if is_powershell:
        print(f"  . {profile}")
    else:
        print(f"  source {profile}")


def show_ollama_instructions():
    """Show instructions for setting up Ollama embeddings."""
    print_header("Ollama Embeddings Setup (Optional)")

    print(f"""
{Colors.CYAN}Ollama provides local embeddings for semantic search.{Colors.ENDC}

{Colors.BOLD}1. Install Ollama:{Colors.ENDC}
   Linux/Mac: curl -fsSL https://ollama.com/install.sh | sh
   Windows:   Download from https://ollama.com/download

{Colors.BOLD}2. Pull the recommended embeddings model:{Colors.ENDC}
   ollama pull {RECOMMENDED_EMBEDDINGS_MODEL}

   {Colors.BLUE}Alternative (larger, higher quality):{Colors.ENDC}
   ollama pull {ALTERNATIVE_EMBEDDINGS_MODEL}

{Colors.BOLD}3. Ollama runs automatically in the background.{Colors.ENDC}
   Default URL: http://localhost:11434
""")


def show_qdrant_instructions():
    """Show instructions for setting up Qdrant."""
    print_header("Qdrant Setup (Optional)")

    print(f"""
{Colors.CYAN}Qdrant provides semantic search for Empirica memories.{Colors.ENDC}

{Colors.BOLD}Option 1: Docker (Recommended){Colors.ENDC}
   docker run -p 6333:6333 -v ~/.qdrant:/qdrant/storage qdrant/qdrant

{Colors.BOLD}Option 2: Local Binary{Colors.ENDC}
   Download from: https://github.com/qdrant/qdrant/releases
   Run: ./qdrant

{Colors.BOLD}Option 3: Qdrant Cloud (Free tier available){Colors.ENDC}
   Sign up at: https://cloud.qdrant.io
   Set EMPIRICA_QDRANT_URL to your cloud instance URL

{Colors.BLUE}Qdrant enables:{Colors.ENDC}
   - Semantic search across findings, unknowns, dead-ends
   - Pattern retrieval during PREFLIGHT
   - Cross-project knowledge sharing
""")


def interactive_setup() -> dict:
    """Run interactive setup to get user preferences."""
    print_header("Empirica Configuration")

    config = {}

    # Autopilot mode
    print(f"""
{Colors.CYAN}Autopilot Mode{Colors.ENDC}
Automatically runs CASCADE phases (PREFLIGHT → CHECK → POSTFLIGHT)
with minimal manual intervention. Good for experienced users.
""")
    config["autopilot"] = ask_yes_no("Enable Autopilot mode?", default=False)

    # Auto-postflight
    print(f"""
{Colors.CYAN}Auto-Postflight{Colors.ENDC}
Automatically captures learning delta when sessions end.
Recommended for building calibration history.
""")
    config["auto_postflight"] = ask_yes_no("Enable auto-postflight?", default=True)

    # Sentinel looping
    print(f"""
{Colors.CYAN}Sentinel Looping{Colors.ENDC}
When CHECK returns 'investigate', automatically loops back to
gather more information. Disable for manual control.
""")
    config["sentinel_looping"] = ask_yes_no("Enable Sentinel looping?", default=True)

    # Qdrant
    print(f"""
{Colors.CYAN}Qdrant (Semantic Search){Colors.ENDC}
Enables semantic search across your epistemic history.
Requires Qdrant server running (Docker or local).
""")
    use_qdrant = ask_yes_no("Configure Qdrant?", default=True)
    if use_qdrant:
        qdrant_url = input(f"Qdrant URL [{DEFAULT_QDRANT_URL}]: ").strip()
        config["qdrant_url"] = qdrant_url or DEFAULT_QDRANT_URL

    # Embeddings
    print(f"""
{Colors.CYAN}Embeddings Provider{Colors.ENDC}
Local embeddings via Ollama (recommended) or API-based.
""")
    provider = ask_choice(
        "Choose embeddings provider:",
        ["ollama (local, free, recommended)", "openai (API key required)", "none (disable embeddings)"],
        default=0
    )

    if "ollama" in provider:
        config["embeddings_provider"] = "ollama"
        config["ollama_url"] = "http://localhost:11434"

        model = ask_choice(
            "Choose embeddings model:",
            [f"{RECOMMENDED_EMBEDDINGS_MODEL} (fast, good quality)",
             f"{ALTERNATIVE_EMBEDDINGS_MODEL} (slower, higher quality)"],
            default=0
        )
        config["embeddings_model"] = model.split()[0]

    elif "openai" in provider:
        config["embeddings_provider"] = "openai"
        config["embeddings_model"] = "text-embedding-3-small"

    return config


def show_completion_summary(config: dict):
    """Show installation completion summary."""
    print_header("Installation Complete!")

    print(f"""
{Colors.GREEN}Empirica {EMPIRICA_VERSION} has been installed successfully!{Colors.ENDC}

{Colors.BOLD}What was installed:{Colors.ENDC}
  ✓ Empirica CLI (empirica command)
  ✓ Claude Code plugin (epistemic hooks)
  ✓ empirica-framework skill
  ✓ Environment configuration

{Colors.BOLD}Configuration:{Colors.ENDC}
  • Autopilot: {"ENABLED" if config.get("autopilot") else "disabled"}
  • Auto-postflight: {"ENABLED" if config.get("auto_postflight") else "disabled"}
  • Sentinel looping: {"ENABLED" if config.get("sentinel_looping", True) else "disabled"}
  • Qdrant: {config.get("qdrant_url", "not configured")}
  • Embeddings: {config.get("embeddings_provider", "none")} / {config.get("embeddings_model", "n/a")}

{Colors.BOLD}Next steps:{Colors.ENDC}
  1. Restart Claude Code to load the plugin
  2. Create your first session:
     {Colors.CYAN}empirica session-create --ai-id claude-code --output json{Colors.ENDC}
  3. Run PREFLIGHT to start tracking:
     {Colors.CYAN}empirica preflight-submit -{Colors.ENDC}
""")

    if not config.get("qdrant_url"):
        print(f"""
{Colors.YELLOW}Optional: Set up Qdrant for semantic search{Colors.ENDC}
  Run: docker run -p 6333:6333 qdrant/qdrant
  Then: export EMPIRICA_QDRANT_URL="http://localhost:6333"
""")

    if config.get("embeddings_provider") == "ollama":
        print(f"""
{Colors.YELLOW}Don't forget to pull the embeddings model:{Colors.ENDC}
  ollama pull {config.get("embeddings_model", RECOMMENDED_EMBEDDINGS_MODEL)}
""")


# =============================================================================
# Main
# =============================================================================

def main():
    """Main installation flow."""
    print_header(f"Empirica Installer v{EMPIRICA_VERSION}")
    print(f"Platform: {platform.system()} {platform.release()}")
    print(f"Python: {sys.version.split()[0]}")

    # Parse arguments
    import argparse
    parser = argparse.ArgumentParser(description="Install Empirica")
    parser.add_argument("--source", type=Path, help="Source directory for plugin files")
    parser.add_argument("--non-interactive", action="store_true", help="Use defaults, no prompts")
    parser.add_argument("--skip-plugin", action="store_true", help="Skip Claude Code plugin")
    parser.add_argument("--skip-skill", action="store_true", help="Skip skill installation")
    parser.add_argument("--skip-env", action="store_true", help="Skip environment setup")
    args = parser.parse_args()

    try:
        # Step 1: Check prerequisites
        status = check_prerequisites()
        if not status["python"]:
            print_error("Python is required. Please install Python 3.10+ first.")
            sys.exit(1)

        # Step 2: Install Empirica package
        if not status["empirica"]:
            install_empirica_package()

        # Step 3: Create directories
        create_directory_structure()

        # Step 4: Interactive configuration
        if args.non_interactive:
            config = {
                "autopilot": False,
                "auto_postflight": True,
                "sentinel_looping": True,
                "qdrant_url": DEFAULT_QDRANT_URL if status["qdrant"] else None,
                "embeddings_provider": "ollama" if status["ollama"] else None,
                "embeddings_model": RECOMMENDED_EMBEDDINGS_MODEL if status["ollama"] else None,
            }
        else:
            config = interactive_setup()

        # Step 5: Install plugin
        if not args.skip_plugin:
            if install_claude_plugin(args.source):
                configure_plugin_registry()

        # Step 6: Install skill
        if not args.skip_skill:
            install_skill(args.source)

        # Step 7: Configure environment
        if not args.skip_env:
            env_vars = configure_environment(config)
            if env_vars:
                write_shell_config(env_vars)

        # Step 8: Show setup instructions if needed
        if not status["ollama"] and config.get("embeddings_provider") == "ollama":
            show_ollama_instructions()

        if not status["qdrant"] and config.get("qdrant_url"):
            show_qdrant_instructions()

        # Step 9: Show completion summary
        show_completion_summary(config)

    except KeyboardInterrupt:
        print("\n\nInstallation cancelled.")
        sys.exit(1)
    except Exception as e:
        print_error(f"Installation failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
