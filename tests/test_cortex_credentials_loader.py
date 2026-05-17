"""Tests for `CredentialsLoader.get_cortex_config()` — Cortex creds resolution
via env-vars + ~/.empirica/credentials.yaml (1.9.7+).

Mirrors the extension's chrome.storage save (`cortexUrl` + `cortexApiKey`)
for CLI users so they don't have to export env vars in every shell.
"""

from __future__ import annotations

import pytest

from empirica.config.credentials_loader import CredentialsLoader


@pytest.fixture(autouse=True)
def isolate_home_and_env(monkeypatch, tmp_path):
    """Universal isolation — every test gets a fake HOME and clean env.

    Without this, tests that fall through to `~/.empirica/credentials.yaml`
    can read OR overwrite the developer's real credentials file.
    """
    fake_home = tmp_path / "fake_home"
    fake_home.mkdir()
    monkeypatch.setenv("HOME", str(fake_home))
    monkeypatch.delenv("CORTEX_REMOTE_URL", raising=False)
    monkeypatch.delenv("CORTEX_URL", raising=False)
    monkeypatch.delenv("CORTEX_API_KEY", raising=False)
    monkeypatch.delenv("EMPIRICA_CREDENTIALS_PATH", raising=False)


@pytest.fixture
def isolated_loader(monkeypatch, tmp_path):
    """Build a CredentialsLoader pointed at a tmp credentials.yaml."""

    # Reset singleton cache so the test gets a fresh load
    CredentialsLoader._instance = None
    CredentialsLoader._credentials_cache = None

    def _make(yaml_content: str | None):
        if yaml_content is not None:
            creds_file = tmp_path / "credentials.yaml"
            creds_file.write_text(yaml_content)
            monkeypatch.setenv("EMPIRICA_CREDENTIALS_PATH", str(creds_file))
        # Fresh instance per call
        CredentialsLoader._instance = None
        CredentialsLoader._credentials_cache = None
        return CredentialsLoader()
    return _make


# ─── env-var resolution ───────────────────────────────────────────────


def test_env_vars_resolve_cortex(monkeypatch, isolated_loader):
    monkeypatch.setenv("CORTEX_REMOTE_URL", "https://cortex.example.com/")
    monkeypatch.setenv("CORTEX_API_KEY", "ctx_env_key")

    loader = isolated_loader(None)
    cfg = loader.get_cortex_config()

    # Trailing slash stripped
    assert cfg["url"] == "https://cortex.example.com"
    assert cfg["api_key"] == "ctx_env_key"


def test_cortex_url_alias_works(monkeypatch, isolated_loader):
    """CORTEX_URL is accepted as alias for CORTEX_REMOTE_URL."""
    monkeypatch.setenv("CORTEX_URL", "https://cortex.example.com")
    monkeypatch.setenv("CORTEX_API_KEY", "ctx_env_key")

    loader = isolated_loader(None)
    cfg = loader.get_cortex_config()
    assert cfg["url"] == "https://cortex.example.com"


# ─── credentials.yaml resolution ──────────────────────────────────────


def test_credentials_yaml_resolves_cortex(isolated_loader):
    """With no env vars, reads `cortex:` block from credentials.yaml."""
    yaml_content = """
version: 1.0
cortex:
  url: https://cortex.file.com/
  api_key: ctx_file_key
"""
    loader = isolated_loader(yaml_content)
    cfg = loader.get_cortex_config()
    assert cfg["url"] == "https://cortex.file.com"
    assert cfg["api_key"] == "ctx_file_key"


def test_env_overrides_file_per_field(monkeypatch, isolated_loader):
    """Env per-field overrides file. Partial env still works."""
    yaml_content = """
version: 1.0
cortex:
  url: https://cortex.file.com
  api_key: ctx_file_key
"""
    monkeypatch.setenv("CORTEX_API_KEY", "ctx_env_key_overrides")
    # No URL env — file's URL should win
    loader = isolated_loader(yaml_content)
    cfg = loader.get_cortex_config()
    assert cfg["url"] == "https://cortex.file.com"  # from file
    assert cfg["api_key"] == "ctx_env_key_overrides"  # from env


def test_missing_cortex_block_returns_none(isolated_loader):
    """No cortex block + no env → (None, None)."""
    yaml_content = """
version: 1.0
providers:
  openai:
    api_key: sk-test
"""
    loader = isolated_loader(yaml_content)
    cfg = loader.get_cortex_config()
    assert cfg["url"] is None
    assert cfg["api_key"] is None


def test_partial_cortex_block(isolated_loader):
    """Only `url` configured → api_key is None, doesn't crash."""
    yaml_content = """
version: 1.0
cortex:
  url: https://cortex.example.com
"""
    loader = isolated_loader(yaml_content)
    cfg = loader.get_cortex_config()
    assert cfg["url"] == "https://cortex.example.com"
    assert cfg["api_key"] is None


def test_completely_missing_credentials_file(isolated_loader):
    """No env, no file → (None, None) without crashing."""
    loader = isolated_loader(None)
    cfg = loader.get_cortex_config()
    assert cfg["url"] is None
    assert cfg["api_key"] is None


# ─── save_cortex_config — write path ──────────────────────────────────


def test_save_cortex_creates_file_when_missing(tmp_path, monkeypatch):
    """No existing credentials.yaml → save creates it with cortex: block."""
    target = tmp_path / "credentials.yaml"
    monkeypatch.setenv("EMPIRICA_CREDENTIALS_PATH", str(target))

    CredentialsLoader._instance = None
    CredentialsLoader._credentials_cache = None
    loader = CredentialsLoader()
    path = loader.save_cortex_config(
        url="https://cortex.example.com",
        api_key="ctx_new_key",
        config_path=target,
    )

    assert path == target
    assert target.exists()
    import yaml
    parsed = yaml.safe_load(target.read_text())
    assert parsed["cortex"]["url"] == "https://cortex.example.com"
    assert parsed["cortex"]["api_key"] == "ctx_new_key"
    assert parsed["version"] == "1.0"


def test_save_cortex_preserves_providers_section(tmp_path, monkeypatch):
    """Existing providers.qwen.api_key must survive a cortex save."""
    target = tmp_path / "credentials.yaml"
    target.write_text("""
version: 1.0
providers:
  qwen:
    api_key: qwen_secret_unchanged
    base_url: https://qwen.example.com
cortex:
  url: https://old.example.com
  api_key: old_key
""")
    monkeypatch.setenv("EMPIRICA_CREDENTIALS_PATH", str(target))

    CredentialsLoader._instance = None
    CredentialsLoader._credentials_cache = None
    loader = CredentialsLoader()
    loader.save_cortex_config(api_key="ctx_updated", config_path=target)

    import yaml
    parsed = yaml.safe_load(target.read_text())
    assert parsed["providers"]["qwen"]["api_key"] == "qwen_secret_unchanged"
    assert parsed["providers"]["qwen"]["base_url"] == "https://qwen.example.com"
    assert parsed["cortex"]["api_key"] == "ctx_updated"
    assert parsed["cortex"]["url"] == "https://old.example.com"  # untouched


def test_save_cortex_partial_update_url_only(tmp_path, monkeypatch):
    """save(url=X) without api_key keeps existing api_key intact."""
    target = tmp_path / "credentials.yaml"
    target.write_text("""
version: 1.0
cortex:
  url: https://A.example.com
  api_key: B
""")
    monkeypatch.setenv("EMPIRICA_CREDENTIALS_PATH", str(target))

    CredentialsLoader._instance = None
    CredentialsLoader._credentials_cache = None
    loader = CredentialsLoader()
    loader.save_cortex_config(url="https://C.example.com", config_path=target)

    import yaml
    parsed = yaml.safe_load(target.read_text())
    assert parsed["cortex"]["url"] == "https://C.example.com"
    assert parsed["cortex"]["api_key"] == "B"  # preserved


def test_save_cortex_invalidates_cache(tmp_path, monkeypatch):
    """After save, next get_cortex_config() reads the new value (not cached)."""
    target = tmp_path / "credentials.yaml"
    target.write_text("""
version: 1.0
cortex:
  url: https://A.example.com
  api_key: cached_key
""")
    monkeypatch.setenv("EMPIRICA_CREDENTIALS_PATH", str(target))
    monkeypatch.delenv("CORTEX_REMOTE_URL", raising=False)
    monkeypatch.delenv("CORTEX_URL", raising=False)
    monkeypatch.delenv("CORTEX_API_KEY", raising=False)

    CredentialsLoader._instance = None
    CredentialsLoader._credentials_cache = None
    loader = CredentialsLoader()
    cached = loader.get_cortex_config()
    assert cached["api_key"] == "cached_key"

    loader.save_cortex_config(api_key="fresh_key", config_path=target)
    fresh = loader.get_cortex_config()
    assert fresh["api_key"] == "fresh_key"


def test_save_cortex_requires_at_least_one_field(tmp_path, monkeypatch):
    """save() with neither url nor api_key raises ValueError."""
    target = tmp_path / "credentials.yaml"
    monkeypatch.setenv("EMPIRICA_CREDENTIALS_PATH", str(target))

    CredentialsLoader._instance = None
    CredentialsLoader._credentials_cache = None
    loader = CredentialsLoader()
    with pytest.raises(ValueError, match="at least one of url/api_key"):
        loader.save_cortex_config(config_path=target)


def test_save_cortex_atomic_no_tempfile_leak(tmp_path, monkeypatch):
    """After save, no `.credentials-*.yaml.tmp` files left behind."""
    target = tmp_path / "credentials.yaml"
    monkeypatch.setenv("EMPIRICA_CREDENTIALS_PATH", str(target))

    CredentialsLoader._instance = None
    CredentialsLoader._credentials_cache = None
    loader = CredentialsLoader()
    loader.save_cortex_config(
        url="https://x.example.com", api_key="k", config_path=target,
    )

    tmp_files = list(tmp_path.glob(".credentials-*.tmp"))
    assert tmp_files == [], f"Tempfiles leaked: {tmp_files}"


# ─── Daemon endpoints ─────────────────────────────────────────────────


def test_endpoint_post_cortex_writes_and_returns_preview(tmp_path, monkeypatch):
    """POST /api/v1/credentials/cortex with url+api_key → 200 + preview only."""
    from fastapi.testclient import TestClient

    from empirica.api.serve_app import create_serve_app

    target = tmp_path / "credentials.yaml"
    monkeypatch.setenv("EMPIRICA_CREDENTIALS_PATH", str(target))
    monkeypatch.delenv("CORTEX_REMOTE_URL", raising=False)
    monkeypatch.delenv("CORTEX_URL", raising=False)
    monkeypatch.delenv("CORTEX_API_KEY", raising=False)

    CredentialsLoader._instance = None
    CredentialsLoader._credentials_cache = None

    app = create_serve_app()
    with TestClient(app) as client:
        resp = client.post(
            "/api/v1/credentials/cortex",
            json={"url": "https://cortex.example.com", "api_key": "ctx_abcdwxyz"},
        )
    assert resp.status_code == 200
    body = resp.json()
    assert body["ok"] is True
    assert body["url"] == "https://cortex.example.com"
    assert body["api_key_set"] is True
    assert body["api_key_preview"] == "...wxyz"  # last 4 only
    assert "credentials.yaml" in body["written_path"]
    # Verify file actually written
    assert target.exists()


def test_endpoint_get_cortex_never_returns_full_key(tmp_path, monkeypatch):
    """GET /api/v1/credentials/cortex returns preview, NEVER raw key."""
    from fastapi.testclient import TestClient

    from empirica.api.serve_app import create_serve_app

    target = tmp_path / "credentials.yaml"
    target.write_text("""
version: 1.0
cortex:
  url: https://x.example.com
  api_key: ctx_dontleakme_zzz9
""")
    monkeypatch.setenv("EMPIRICA_CREDENTIALS_PATH", str(target))
    monkeypatch.delenv("CORTEX_REMOTE_URL", raising=False)
    monkeypatch.delenv("CORTEX_URL", raising=False)
    monkeypatch.delenv("CORTEX_API_KEY", raising=False)

    CredentialsLoader._instance = None
    CredentialsLoader._credentials_cache = None

    app = create_serve_app()
    with TestClient(app) as client:
        resp = client.get("/api/v1/credentials/cortex")

    body = resp.json()
    assert body["ok"] is True
    assert body["api_key_set"] is True
    assert body["api_key_preview"] == "...zzz9"
    # The raw key MUST NOT appear anywhere in the response
    assert "ctx_dontleakme_zzz9" not in resp.text


def test_endpoint_post_rejects_empty_payload(monkeypatch):
    """POST with no url + no api_key → 200 ok=false with hint."""
    from fastapi.testclient import TestClient

    from empirica.api.serve_app import create_serve_app

    monkeypatch.delenv("CORTEX_REMOTE_URL", raising=False)
    monkeypatch.delenv("CORTEX_URL", raising=False)
    monkeypatch.delenv("CORTEX_API_KEY", raising=False)

    app = create_serve_app()
    with TestClient(app) as client:
        resp = client.post("/api/v1/credentials/cortex", json={})
    assert resp.status_code == 200  # not 422 — surfaces as ok=false
    body = resp.json()
    assert body["ok"] is False
    assert "required" in body["error"].lower()


# ── save_ntfy_config (David, 2026-05-17 — first-run wizard) ──────────────


# Test-fixture token/password strings — obviously synthetic, not real
# secrets. Suppresses ruff S105/S106 false positives on hardcoded creds
# in test files. Defined module-level so all save_ntfy tests share them.
_FIXTURE_NTFY_TOKEN = "tk_test_abc123"  # noqa: S105
_FIXTURE_NTFY_TOKEN_XYZ = "tk_xyz"  # noqa: S105
_FIXTURE_NTFY_TOKEN_X = "tk_x"  # noqa: S105
_FIXTURE_NTFY_PASSWORD = "s3cret"  # noqa: S105


def test_save_ntfy_creates_file_when_missing(tmp_path, monkeypatch):
    """Fresh install: setup-claude-code wizard writes a complete ntfy block
    to a not-yet-existing credentials.yaml."""
    target = tmp_path / "credentials.yaml"
    monkeypatch.setenv("EMPIRICA_CREDENTIALS_PATH", str(target))
    monkeypatch.delenv("ORCHESTRATION_NTFY_URL", raising=False)
    monkeypatch.delenv("ORCHESTRATION_NTFY_TOPIC", raising=False)
    monkeypatch.delenv("ORCHESTRATION_NTFY_TOKEN", raising=False)
    monkeypatch.delenv("ORCHESTRATION_NTFY_USER", raising=False)
    monkeypatch.delenv("ORCHESTRATION_NTFY_PASS", raising=False)

    from empirica.config.credentials_loader import CredentialsLoader
    loader = CredentialsLoader()
    written = loader.save_ntfy_config(
        url="https://ntfy.example.com",
        topic="orchestration-events",
        token=_FIXTURE_NTFY_TOKEN,
    )

    assert written == target
    assert target.exists()
    import yaml as _yaml
    data = _yaml.safe_load(target.read_text())
    assert data["ntfy"]["url"] == "https://ntfy.example.com"
    assert data["ntfy"]["topic"] == "orchestration-events"
    assert data["ntfy"]["token"] == _FIXTURE_NTFY_TOKEN
    # version key written by default
    assert data.get("version") == "1.0"


def test_save_ntfy_preserves_existing_cortex_block(tmp_path, monkeypatch):
    """The wizard runs after cortex is set (or vice versa). Writing the
    ntfy block must NEVER blow away the cortex block — atomic merge only."""
    target = tmp_path / "credentials.yaml"
    monkeypatch.setenv("EMPIRICA_CREDENTIALS_PATH", str(target))
    import yaml as _yaml
    target.write_text(_yaml.dump({
        "version": "1.0",
        "cortex": {"url": "https://cortex.example.com", "api_key": "ctx_keep_me"},
    }))

    from empirica.config.credentials_loader import CredentialsLoader
    loader = CredentialsLoader()
    loader.save_ntfy_config(
        url="https://ntfy.example.com",
        topic="t",
        token=_FIXTURE_NTFY_TOKEN_XYZ,
    )

    data = _yaml.safe_load(target.read_text())
    # cortex block untouched
    assert data["cortex"] == {"url": "https://cortex.example.com", "api_key": "ctx_keep_me"}
    # ntfy block added
    assert data["ntfy"]["token"] == _FIXTURE_NTFY_TOKEN_XYZ


def test_save_ntfy_with_basic_auth_path(tmp_path, monkeypatch):
    """token is preferred but legacy user+password path must still work
    (some self-hosted ntfy installs predate access tokens)."""
    target = tmp_path / "credentials.yaml"
    monkeypatch.setenv("EMPIRICA_CREDENTIALS_PATH", str(target))

    from empirica.config.credentials_loader import CredentialsLoader
    loader = CredentialsLoader()
    loader.save_ntfy_config(
        url="https://ntfy.example.com",
        topic="t",
        user="alice",
        password=_FIXTURE_NTFY_PASSWORD,
    )

    import yaml as _yaml
    data = _yaml.safe_load(target.read_text())
    assert data["ntfy"]["user"] == "alice"
    assert data["ntfy"]["password"] == _FIXTURE_NTFY_PASSWORD
    assert "token" not in data["ntfy"] or data["ntfy"].get("token") is None


def test_save_ntfy_requires_at_least_one_field(tmp_path, monkeypatch):
    """All-None call is misuse — surface as ValueError rather than silently
    writing an empty block."""
    target = tmp_path / "credentials.yaml"
    monkeypatch.setenv("EMPIRICA_CREDENTIALS_PATH", str(target))

    from empirica.config.credentials_loader import CredentialsLoader
    loader = CredentialsLoader()
    import pytest
    with pytest.raises(ValueError, match="at least one field"):
        loader.save_ntfy_config()


def test_save_ntfy_strips_trailing_slash_on_url(tmp_path, monkeypatch):
    """Mirrors save_cortex_config — server convention is no trailing slash."""
    target = tmp_path / "credentials.yaml"
    monkeypatch.setenv("EMPIRICA_CREDENTIALS_PATH", str(target))

    from empirica.config.credentials_loader import CredentialsLoader
    loader = CredentialsLoader()
    loader.save_ntfy_config(url="https://ntfy.example.com/", topic="t", token=_FIXTURE_NTFY_TOKEN_X)

    import yaml as _yaml
    data = _yaml.safe_load(target.read_text())
    assert data["ntfy"]["url"] == "https://ntfy.example.com"
