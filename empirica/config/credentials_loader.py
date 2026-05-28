#!/usr/bin/env python3
"""
Centralized Credentials Loader for Empirica AI Adapters

Features:
- Load credentials from YAML config
- Environment variable interpolation
- Fallback to legacy dotfiles
- Caching for performance
- Model validation
"""

import logging
import os
import re
import tempfile
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# Try to import YAML, fallback to JSON if not available
try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False
    logger.warning("PyYAML not installed, YAML support disabled. Install with: pip install pyyaml")

import json  # noqa: E402 — intentionally after conditional yaml import


class CredentialsLoader:
    """Load and manage AI adapter credentials"""

    # Singleton pattern for caching
    _instance = None
    _credentials_cache = None

    def __new__(cls):
        """Create singleton instance of credentials loader."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        """Initialize credentials loader and cache."""
        if self._credentials_cache is None:
            self._load_credentials()

    def _find_config_file(self) -> Path | None:
        """
        Find credentials config file in order of precedence:
        1. Environment variable EMPIRICA_CREDENTIALS_PATH
        2. .empirica/credentials.yaml (repo root)
        3. .empirica/credentials.json (repo root)
        4. ~/.empirica/credentials.yaml (home dir)
        """
        # Check environment variable first
        env_path = os.getenv('EMPIRICA_CREDENTIALS_PATH')
        if env_path and Path(env_path).exists():
            return Path(env_path)

        # Repo root .empirica directory
        # Navigate from empirica/config/ to repo root
        repo_root = Path(__file__).parent.parent.parent
        local_config = repo_root / '.empirica'

        if YAML_AVAILABLE and (local_config / 'credentials.yaml').exists():
            return local_config / 'credentials.yaml'
        if (local_config / 'credentials.json').exists():
            return local_config / 'credentials.json'

        # Home directory
        home_config = Path.home() / '.empirica'

        if YAML_AVAILABLE and (home_config / 'credentials.yaml').exists():
            return home_config / 'credentials.yaml'
        if (home_config / 'credentials.json').exists():
            return home_config / 'credentials.json'

        return None

    def _load_credentials(self):
        """Load credentials from config file or fallback to dotfiles"""
        config_file = self._find_config_file()

        if config_file:
            logger.info(f"✅ Loading credentials from: {config_file}")

            try:
                if config_file.suffix in ['.yaml', '.yml']:
                    if not YAML_AVAILABLE:
                        logger.error("YAML config found but PyYAML not installed")
                        self._credentials_cache = self._load_from_dotfiles()
                        return

                    with open(config_file) as f:
                        config = yaml.safe_load(f)
                else:
                    with open(config_file) as f:
                        config = json.load(f)

                # Interpolate environment variables
                self._credentials_cache = self._interpolate_env_vars(config)
                logger.info(f"   Loaded {len(config.get('providers', {}))} provider configurations")

            except Exception as e:
                logger.error(f"Failed to load credentials config: {e}")
                logger.warning("Falling back to legacy dotfiles")
                self._credentials_cache = self._load_from_dotfiles()

        else:
            logger.warning("⚠️ No credentials config found, falling back to legacy dotfiles")
            self._credentials_cache = self._load_from_dotfiles()

    def _interpolate_env_vars(self, config: dict) -> dict:
        """Replace ${VAR_NAME} with environment variable values"""
        def replace_vars(obj: Any) -> Any:
            """Recursively replace env vars in nested structure."""
            if isinstance(obj, dict):
                return {k: replace_vars(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [replace_vars(item) for item in obj]
            elif isinstance(obj, str):
                # Replace ${VAR_NAME} with env var value
                pattern = r'\$\{([A-Z_0-9]+)\}'

                def replacer(match: re.Match) -> str:
                    """Replace single env var match with its value."""
                    var_name = match.group(1)
                    value = os.getenv(var_name)
                    if value is None:
                        logger.debug(f"Environment variable {var_name} not set, using placeholder")
                        return match.group(0)  # Return original if not found
                    return value

                return re.sub(pattern, replacer, obj)
            else:
                return obj

        return replace_vars(config)

    def _load_from_dotfiles(self) -> dict:
        """Fallback: Load from legacy dotfiles"""
        repo_root = Path(__file__).parent.parent.parent

        credentials = {
            'version': '1.0',
            'providers': {},
            'source': 'dotfiles'
        }

        # Map dotfiles to providers
        dotfile_map = {
            'qwen': '.qwen_api',
            'minimax': '.minimax_key',  # Note: user has .minimax_key
            'rovodev': '.rovodev_api',
            'gemini': '.gemini_api',
            'qodo': '.qodo_api',
            'openrouter': '.open_router_api'
        }

        loaded_count = 0
        for provider, dotfile in dotfile_map.items():
            dotfile_path = repo_root / dotfile
            if dotfile_path.exists():
                try:
                    with open(dotfile_path) as f:
                        api_key = f.read().strip()

                    if api_key:
                        credentials['providers'][provider] = {
                            'api_key': api_key,
                            'source': 'dotfile',
                            'dotfile': str(dotfile_path)
                        }
                        loaded_count += 1
                        logger.debug(f"   Loaded {provider} from {dotfile}")
                except Exception as e:
                    logger.warning(f"Failed to load {dotfile}: {e}")

        logger.info(f"   Loaded {loaded_count} API keys from dotfiles")
        return credentials

    def save_cortex_config(
        self,
        *,
        url: str | None = None,
        api_key: str | None = None,
        config_path: Path | None = None,
    ) -> Path:
        """Persist Cortex {url, api_key} to credentials.yaml.

        Merges into the existing `cortex:` block — never touches
        `providers:`, `version:`, or any other top-level keys. At least
        one of url/api_key must be provided.

        Resolution order for target path (same as _find_config_file):
          1. config_path argument (explicit override)
          2. EMPIRICA_CREDENTIALS_PATH env var
          3. existing credentials.yaml in repo or home dir (whichever
             _find_config_file returns)
          4. ~/.empirica/credentials.yaml (creates if missing)

        Atomic write: tempfile + rename to avoid partial writes
        corrupting the file. Resets the cache so subsequent reads see
        the new values.

        Returns the path written to.
        """
        if url is None and api_key is None:
            raise ValueError(
                "save_cortex_config: at least one of url/api_key required"
            )

        # Resolve target:
        # 1. Explicit config_path argument
        # 2. EMPIRICA_CREDENTIALS_PATH env var (even if file doesn't exist —
        #    we're creating it, so existence check from _find_config_file
        #    would falsely fall through)
        # 3. _find_config_file (returns existing files only)
        # 4. ~/.empirica/credentials.yaml (default home location)
        target = config_path
        if target is None:
            env_path = os.getenv("EMPIRICA_CREDENTIALS_PATH")
            if env_path:
                target = Path(env_path)
        if target is None:
            target = self._find_config_file()
        if target is None:
            target = Path.home() / ".empirica" / "credentials.yaml"
        target.parent.mkdir(parents=True, exist_ok=True)

        # Load existing (preserve providers, etc.)
        existing: dict = {}
        if target.exists() and YAML_AVAILABLE:
            try:
                existing = yaml.safe_load(target.read_text(encoding="utf-8")) or {}
            except Exception as e:
                logger.warning(f"save_cortex_config: existing file unreadable, overwriting: {e}")
                existing = {}

        cortex_block = existing.get("cortex") or {}
        if not isinstance(cortex_block, dict):
            cortex_block = {}
        if url is not None:
            cortex_block["url"] = url.rstrip("/") or None
        if api_key is not None:
            cortex_block["api_key"] = api_key

        existing["cortex"] = cortex_block
        if "version" not in existing:
            existing["version"] = "1.0"

        if not YAML_AVAILABLE:
            raise RuntimeError(
                "save_cortex_config: PyYAML not installed (`pip install pyyaml`)",
            )

        # Atomic write (tempfile in same dir → rename)
        tmp_fd, tmp_path = tempfile.mkstemp(
            prefix=".credentials-", suffix=".yaml.tmp", dir=str(target.parent),
        )
        try:
            with os.fdopen(tmp_fd, "w", encoding="utf-8") as f:
                yaml.dump(
                    existing, f, default_flow_style=False,
                    sort_keys=False, allow_unicode=True,
                )
            os.replace(tmp_path, target)
        except Exception:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass
            raise

        # Invalidate cache so next read sees the new values
        self._credentials_cache = None
        return target

    def save_ntfy_config(
        self,
        *,
        url: str | None = None,
        topic: str | None = None,
        token: str | None = None,
        user: str | None = None,
        password: str | None = None,
        config_path: Path | None = None,
    ) -> Path:
        """Persist ntfy {url, topic, token | user+password} to credentials.yaml.

        Merges into the existing `ntfy:` block — never touches `cortex:`,
        `providers:`, `version:`, or any other top-level keys. At least
        one of token / user+password must be set for the listener to
        authenticate (token preferred — revocable + no password exposure).

        Resolution order for target path (same as save_cortex_config):
          1. config_path argument (explicit override)
          2. EMPIRICA_CREDENTIALS_PATH env var
          3. existing credentials.yaml (if any) returned by _find_config_file
          4. ~/.empirica/credentials.yaml (creates if missing)

        Atomic write: tempfile + rename. Resets cache.
        Returns the path written to.

        Driver: setup-claude-code's first-run credentials wizard
        (David, 2026-05-17) — fresh installs hit the listener-exit-code-2
        wall without ntfy creds. Mirrors save_cortex_config.
        """
        if all(v is None for v in (url, topic, token, user, password)):
            raise ValueError(
                "save_ntfy_config: at least one field required"
            )

        target = config_path
        if target is None:
            env_path = os.getenv("EMPIRICA_CREDENTIALS_PATH")
            if env_path:
                target = Path(env_path)
        if target is None:
            target = self._find_config_file()
        if target is None:
            target = Path.home() / ".empirica" / "credentials.yaml"
        target.parent.mkdir(parents=True, exist_ok=True)

        existing: dict = {}
        if target.exists() and YAML_AVAILABLE:
            try:
                existing = yaml.safe_load(target.read_text(encoding="utf-8")) or {}
            except Exception as e:
                logger.warning(f"save_ntfy_config: existing file unreadable, overwriting: {e}")
                existing = {}

        ntfy_block = existing.get("ntfy") or {}
        if not isinstance(ntfy_block, dict):
            ntfy_block = {}
        # Merge non-None fields; url gets trailing-slash strip per server convention.
        fields = {"url": url, "topic": topic, "token": token, "user": user, "password": password}
        for key, val in fields.items():
            if val is None:
                continue
            ntfy_block[key] = (val.rstrip("/") if key == "url" else val) or None
        existing["ntfy"] = ntfy_block
        if "version" not in existing:
            existing["version"] = "1.0"

        if not YAML_AVAILABLE:
            raise RuntimeError(
                "save_ntfy_config: PyYAML not installed (`pip install pyyaml`)",
            )

        tmp_fd, tmp_path = tempfile.mkstemp(
            prefix=".credentials-", suffix=".yaml.tmp", dir=str(target.parent),
        )
        try:
            with os.fdopen(tmp_fd, "w", encoding="utf-8") as f:
                yaml.dump(
                    existing, f, default_flow_style=False,
                    sort_keys=False, allow_unicode=True,
                )
            os.replace(tmp_path, target)
        except Exception:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass
            raise

        self._credentials_cache = None
        return target

    def get_cortex_config(self) -> dict[str, str | None]:
        """Return Cortex {url, api_key} resolved file-first:

        1. `cortex:` block in credentials file (~/.empirica/credentials.yaml)
           — canonical, wins per-field
        2. Env vars (CORTEX_REMOTE_URL / CORTEX_URL, CORTEX_API_KEY) fill
           only fields the file does not provide
        3. None if neither

        File-first precedence (2026-05-28): a stale CORTEX_API_KEY exported
        into a systemd-user env silently shadowed the valid file key for 10
        days (listener-deaf incident). credentials.yaml is the single
        canonical credential store across the ecosystem, so the file now
        wins; env only fills gaps. When env is set AND disagrees with the
        file, the env value is ignored and a warning is logged so the
        divergence is visible instead of silent.

        The browser extension stores its own copy in chrome.storage
        (`cortexUrl` + `cortexApiKey`); this is the CLI-side equivalent
        so users don't have to export env vars in every shell.

        Returns: {"url": str | None, "api_key": str | None}
        """
        env_url = os.getenv("CORTEX_REMOTE_URL") or os.getenv("CORTEX_URL")
        env_key = os.getenv("CORTEX_API_KEY")

        if not self._credentials_cache:
            self._load_credentials()

        file_cfg = self._credentials_cache.get("cortex") if self._credentials_cache else None
        file_url = file_cfg.get("url") if isinstance(file_cfg, dict) else None
        file_key = file_cfg.get("api_key") if isinstance(file_cfg, dict) else None

        # File is canonical. Warn (don't silently shadow) when a set env
        # value disagrees with the file — this is the guard the listener-deaf
        # incident needed.
        if env_key and file_key and env_key != file_key:
            logger.warning(
                "CORTEX_API_KEY env var differs from credentials.yaml key; "
                "ignoring env, file is canonical. Unset the env var to "
                "silence this (a stale env key caused the 2026-05-28 "
                "listener-deaf incident).",
            )
        if env_url and file_url and env_url.rstrip("/") != file_url.rstrip("/"):
            logger.warning(
                "CORTEX_REMOTE_URL env var differs from credentials.yaml url; "
                "ignoring env, file is canonical.",
            )

        # File wins per-field; env only fills what the file lacks.
        url = file_url or env_url
        key = file_key or env_key
        return {
            "url": url.rstrip("/") if url else None,
            "api_key": key or None,
        }

    def get_ntfy_config(self) -> dict[str, str | None]:
        """Return ntfy {url, topic, user, password, token} resolved by precedence:

        1. Env vars (ORCHESTRATION_NTFY_URL/_TOPIC/_USER/_PASS/_TOKEN)
        2. `ntfy:` block in credentials file (~/.empirica/credentials.yaml)
        3. `backends.ntfy` block in ~/.empirica/notify.yaml (the outbound
           notify dispatcher's config — single source of truth for ntfy
           when the extension has registered with cortex). Server URL +
           the env var named by `auth_env` are read here.
        4. Defaults: cortex's prod ntfy server + AI-wake topic.

        Used by the ntfy listener (`empirica loop listen`) to subscribe to
        the orchestration proposals topic and bridge push events into
        running Claude sessions via Monitor. Also reusable by any other
        ntfy-touching code that needs the canonical creds.

        Returns: {"url", "topic", "user", "password", "token"} — only one
        of (user+password) or (token) needs to be set. Token is preferred
        because ntfy access tokens (`tk_` prefix) are revocable + don't
        expose the account password.
        """
        defaults = {
            "url": "https://ntfy.getempirica.com",
            # T12 (2026-05-15): cortex split topics so AI-wake events don't
            # ping ECO's phone. `orchestration-events` is the AI-wake topic
            # (both auto-accepted and ECO-accepted proposals emit here);
            # `orchestration-proposals` is phone-only for ECO decisions.
            # The listener subscribes to the AI-wake topic.
            "topic": "orchestration-events",
        }
        env_map = {
            "url": os.getenv("ORCHESTRATION_NTFY_URL"),
            "topic": os.getenv("ORCHESTRATION_NTFY_TOPIC"),
            "user": os.getenv("ORCHESTRATION_NTFY_USER"),
            "password": os.getenv("ORCHESTRATION_NTFY_PASS"),
            "token": os.getenv("ORCHESTRATION_NTFY_TOKEN"),
        }

        if not self._credentials_cache:
            self._load_credentials()
        file_cfg = self._credentials_cache.get("ntfy") if self._credentials_cache else None
        file_map = file_cfg if isinstance(file_cfg, dict) else {}

        # notify.yaml fallback — the outbound notify dispatcher already has
        # ntfy server + auth configured (extension registers with cortex
        # using the same creds). Resolve auth via the `auth_env` indirection
        # the dispatcher uses (env var name → token value).
        notify_map = self._load_notify_ntfy_block()

        return {
            "url": (
                env_map["url"]
                or file_map.get("url")
                or notify_map.get("url")
                or defaults["url"]
            ).rstrip("/"),
            "topic": (
                env_map["topic"]
                or file_map.get("topic")
                or notify_map.get("topic")
                or defaults["topic"]
            ),
            "user": env_map["user"] or file_map.get("user") or notify_map.get("user") or None,
            "password": (
                env_map["password"] or file_map.get("password")
                or notify_map.get("password") or None
            ),
            "token": (
                env_map["token"] or file_map.get("token")
                or notify_map.get("token") or None
            ),
        }

    def _load_notify_ntfy_block(self) -> dict[str, str | None]:
        """Best-effort read of ~/.empirica/notify.yaml backends.ntfy.

        Returns {url, topic, user, password, token} with the values that
        the outbound notify dispatcher would use. `auth_env` is followed
        — when present, the named env var's value becomes either the
        token (if it starts with `tk_`) or the password (with empty user).

        Returns empty dict on any failure — caller falls back to the
        defaults.
        """
        from pathlib import Path
        try:
            import yaml
            notify_path = Path.home() / ".empirica" / "notify.yaml"
            if not notify_path.exists():
                return {}
            data = yaml.safe_load(notify_path.read_text()) or {}
            backends = data.get("backends") or {}
            ntfy_backend = backends.get("ntfy") or {}
            if not isinstance(ntfy_backend, dict):
                return {}
        except Exception:
            return {}

        out: dict[str, str | None] = {
            "url": ntfy_backend.get("server") or ntfy_backend.get("url"),
            "topic": ntfy_backend.get("default_topic") or ntfy_backend.get("topic"),
            "user": ntfy_backend.get("user"),
            "password": ntfy_backend.get("password"),
            "token": ntfy_backend.get("token"),
        }
        auth_env = ntfy_backend.get("auth_env")
        if auth_env and not (out["token"] or out["password"]):
            auth_value = os.getenv(auth_env)
            if auth_value:
                if auth_value.startswith("tk_"):
                    out["token"] = auth_value
                else:
                    out["password"] = auth_value
        return out

    def get_provider_config(self, provider: str) -> dict[str, Any] | None:
        """
        Get configuration for a specific provider

        Args:
            provider: Provider name (qwen, minimax, etc.)

        Returns:
            Dict with provider config or None if not found
        """
        if not self._credentials_cache:
            self._load_credentials()

        providers = self._credentials_cache.get('providers', {})
        return providers.get(provider)

    def get_api_key(self, provider: str) -> str | None:
        """Get API key for provider"""
        config = self.get_provider_config(provider)
        return config.get('api_key') if config else None

    def get_base_url(self, provider: str) -> str | None:
        """Get base URL for provider"""
        config = self.get_provider_config(provider)
        return config.get('base_url') if config else None

    def get_headers(self, provider: str) -> dict[str, str]:
        """
        Get HTTP headers for provider

        Automatically interpolates ${api_key} in headers
        """
        config = self.get_provider_config(provider)
        if not config:
            return {}

        headers = config.get('headers', {})
        api_key = config.get('api_key', '')

        # Replace ${api_key} in header values
        interpolated_headers = {}
        for key, value in headers.items():
            if isinstance(value, str):
                interpolated_headers[key] = value.replace('${api_key}', api_key)
            else:
                interpolated_headers[key] = value

        return interpolated_headers

    def get_default_model(self, provider: str) -> str | None:
        """Get default model for provider"""
        config = self.get_provider_config(provider)
        return config.get('default_model') if config else None

    def get_available_models(self, provider: str) -> list:
        """Get list of available models for provider"""
        config = self.get_provider_config(provider)
        return config.get('available_models', []) if config else []

    def validate_model(self, provider: str, model: str) -> bool:
        """Check if model is available for provider"""
        available = self.get_available_models(provider)
        if not available:
            return True  # No restrictions if not specified
        return model in available

    def get_auth_method(self, provider: str) -> str:
        """Get authentication method (header, query_param, cli)"""
        config = self.get_provider_config(provider)
        return config.get('auth_method', 'header') if config else 'header'

    def list_providers(self) -> list:
        """List all configured providers"""
        if not self._credentials_cache:
            self._load_credentials()
        return list(self._credentials_cache.get('providers', {}).keys())

    def reload(self):
        """Reload credentials from file"""
        self._credentials_cache = None
        self._load_credentials()


# Global instance
_loader = None


def get_credentials_loader() -> CredentialsLoader:
    """Get global credentials loader instance"""
    global _loader
    if _loader is None:
        _loader = CredentialsLoader()
    return _loader


if __name__ == "__main__":
    # Test credentials loader
    print("=" * 70)
    print("  CREDENTIALS LOADER TEST")
    print("=" * 70)

    loader = get_credentials_loader()

    print(f"\n✅ Credentials source: {loader._credentials_cache.get('source', 'config')}")
    print(f"✅ Providers configured: {len(loader.list_providers())}")

    # Test all providers
    providers = loader.list_providers()

    if not providers:
        print("\n⚠️ No providers configured!")
        print("\nExpected one of:")
        print("  - .empirica/credentials.yaml")
        print("  - Legacy dotfiles (.qwen_api, .minimax_key, etc.)")
    else:
        for provider in providers:
            print(f"\n{provider.upper()}:")
            config = loader.get_provider_config(provider)
            if config:
                has_key = bool(loader.get_api_key(provider))
                print(f"  API Key: {'✅ Configured' if has_key else '❌ Missing'}")

                base_url = loader.get_base_url(provider)
                if base_url:
                    print(f"  Base URL: {base_url}")

                default_model = loader.get_default_model(provider)
                if default_model:
                    print(f"  Default Model: {default_model}")

                models = loader.get_available_models(provider)
                if models:
                    print(f"  Available Models ({len(models)}): {', '.join(models[:3])}{'...' if len(models) > 3 else ''}")

                headers = loader.get_headers(provider)
                if headers:
                    print(f"  Headers: {', '.join(headers.keys())}")

                source = config.get('source')
                if source:
                    print(f"  Source: {source}")

    print("\n" + "=" * 70)
    print("  ✅ TEST COMPLETE")
    print("=" * 70)
