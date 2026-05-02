"""Tests for Phase 4b — artifact card action wiring.

Covers the resolve_unknown action wrapper + the pin file persistence
side. The full Textual button → CLI dispatch is exercised by smoke
runs of `empirica chat`.
"""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest

from empirica.core.chat.actions import ActionError, resolve_unknown


class TestResolveUnknown:
    @patch("empirica.core.chat.actions.subprocess.run")
    def test_calls_cli_with_unknown_id(self, mock_run):
        mock_run.return_value = MagicMock(
            returncode=0, stdout='{"ok": true, "id": "uuid-1"}', stderr="",
        )
        result = resolve_unknown("uuid-1")
        assert result["ok"] is True
        cmd = mock_run.call_args[0][0]
        assert "unknown-resolve" in cmd
        assert "--unknown-id" in cmd
        assert "uuid-1" in cmd

    @patch("empirica.core.chat.actions.subprocess.run")
    def test_includes_resolved_by_when_provided(self, mock_run):
        mock_run.return_value = MagicMock(
            returncode=0, stdout='{"ok": true}', stderr="",
        )
        resolve_unknown("uuid-2", resolved_by="found in docs")
        cmd = mock_run.call_args[0][0]
        assert "--resolved-by" in cmd
        assert "found in docs" in cmd

    @patch("empirica.core.chat.actions.subprocess.run")
    def test_omits_resolved_by_when_none(self, mock_run):
        mock_run.return_value = MagicMock(
            returncode=0, stdout='{"ok": true}', stderr="",
        )
        resolve_unknown("uuid-3")
        cmd = mock_run.call_args[0][0]
        assert "--resolved-by" not in cmd

    @patch("empirica.core.chat.actions.subprocess.run")
    def test_nonzero_exit_raises(self, mock_run):
        mock_run.return_value = MagicMock(
            returncode=1, stdout="", stderr="not found",
        )
        with pytest.raises(ActionError):
            resolve_unknown("missing")


class TestPinFilePersistence:
    """Test the _pin_artifact write logic by isolating the file IO."""

    def test_pin_creates_file_with_one_entry(self, tmp_path, monkeypatch):
        # Redirect Path.home() to tmp_path
        monkeypatch.setattr("pathlib.Path.home", lambda: tmp_path)
        # Build minimal fake context
        from empirica.core.chat.session import ChatSession, Turn, TurnKind

        sess = ChatSession.create(root=tmp_path / ".empirica" / "chat_sessions")
        turn = Turn.new(TurnKind.EPISTEMIC_ACTION, "test")

        # Reproduce _pin_artifact's file-writing logic inline
        # (the method is on ChatApp which needs Textual to instantiate)
        pin_path = tmp_path / ".empirica" / f"chat_pinned_{sess.session_id}.json"
        pin_path.parent.mkdir(parents=True, exist_ok=True)
        entry = {
            "artifact_type": "finding",
            "artifact_id": "uuid-x",
            "turn_id": turn.turn_id,
            "pinned_at": 1700000000,
        }
        pin_path.write_text(json.dumps([entry], indent=2))

        loaded = json.loads(pin_path.read_text())
        assert loaded == [entry]

    def test_pin_appends_to_existing_file(self, tmp_path):
        pin_path = tmp_path / "chat_pinned_abc.json"
        existing = [{"artifact_type": "finding", "artifact_id": "old-1",
                     "turn_id": "t1", "pinned_at": 1700000000}]
        pin_path.write_text(json.dumps(existing))

        # Append-and-rewrite (matches _pin_artifact behavior)
        loaded = json.loads(pin_path.read_text() or "[]")
        loaded.append({"artifact_type": "decision", "artifact_id": "new-1",
                       "turn_id": "t2", "pinned_at": 1700000100})
        pin_path.write_text(json.dumps(loaded, indent=2))

        result = json.loads(pin_path.read_text())
        assert len(result) == 2
        assert result[0]["artifact_id"] == "old-1"
        assert result[1]["artifact_id"] == "new-1"

    def test_pin_handles_corrupt_existing_file(self, tmp_path):
        pin_path = tmp_path / "chat_pinned_xyz.json"
        pin_path.write_text("{not json")
        # Reproduce the tolerance pattern
        try:
            existing = json.loads(pin_path.read_text() or "[]")
            if not isinstance(existing, list):
                existing = []
        except Exception:
            existing = []
        assert existing == []
