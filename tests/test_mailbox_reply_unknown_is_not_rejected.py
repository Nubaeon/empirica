"""`mailbox reply` must not treat "no answer" as "the server said no".

`_default_http_post` returns -1 only from its bare-exception branch: no HTTP
response arrived. An HTTP 4xx/5xx returns its real code, so -1 is categorically
"I never heard back" — and the server may well have committed.

The handler aborted on it. Measured 2026-09-06: a read timeout left the peer
holding the reply while the sender's parent stayed `accepted` with `completed_at`
null — precisely the stalled handshake this verb exists to prevent. A second
practice hit the other half and double-sent after a "failed" reply that had
succeeded.

The asymmetry that made it hard to see: the step-2 (parent close) failure was
already handled gracefully with a precise message. The author reasoned about a
partial apply BETWEEN steps and not about an unknown outcome WITHIN one.
"""

from __future__ import annotations

from argparse import Namespace

import pytest

from empirica.cli.command_handlers.mailbox_commands import handle_mailbox_reply_command

TIMEOUT = (-1, {"error": "TimeoutError: The read operation timed out"})
OK = (200, {"proposal_id": "prop_new"})
COMPLETED = (200, {"ok": True})
REJECTED = (403, {"error": "not permitted"})


def _args(**over):
    base = {
        "parent_id": "prop_parent",
        "summary": "done",
        "result": "shipped",
        "title": "Re: t",
        "payload": None,
        "commit_sha": None,
        "no_close": False,
        "no_archive": True,
        "output": "json",
        "target": None,
    }
    base.update(over)
    return Namespace(**base)


def _harness(sequence):
    calls: list[dict] = []
    it = iter(sequence)

    def post(url, body, api_key, timeout):
        calls.append({"url": url, "body": body})
        try:
            return next(it)
        except StopIteration:
            return OK

    return {
        "_resolve_cortex_creds": lambda: ("https://cortex.example", "key"),
        "_resolve_ai_id": lambda: "empirica.david.empirica",
        "_http_post": post,
        "_fetch_parent": lambda *a, **k: {"title": "t", "source_claude": "empirica.david.peer"},
    }, calls


def test_a_timeout_is_RETRIED_rather_than_aborted(capsys):
    """The defect: one timeout ended the command before the parent was closed."""
    kw, calls = _harness([TIMEOUT, OK, COMPLETED])
    rc = handle_mailbox_reply_command(_args(), **kw)

    propose_calls = [c for c in calls if c["url"].endswith("/propose")]
    assert len(propose_calls) == 2, "a timeout must be retried, not treated as a refusal"
    assert rc == 0, f"the reply succeeded on retry and must report success, got rc={rc}"


def test_the_retry_carries_the_SAME_idempotency_key():
    """The retry is only safe because the key is stable — otherwise it double-posts."""
    kw, calls = _harness([TIMEOUT, OK, COMPLETED])
    handle_mailbox_reply_command(_args(), **kw)

    keys = [c["body"]["payload"].get("idempotency_key") for c in calls if c["url"].endswith("/propose")]
    assert len(keys) == 2
    assert keys[0] and keys[0] == keys[1], "differing keys would make the retry a double-send"


def test_two_timeouts_report_UNKNOWN_not_rejected(capsys):
    """The claim that must never be made: that the peer refused, when nobody answered."""
    kw, _ = _harness([TIMEOUT, TIMEOUT])
    rc = handle_mailbox_reply_command(_args(), **kw)

    err = capsys.readouterr().err
    assert rc == 2, "unknown needs an exit code distinct from a real refusal (1)"
    assert "UNKNOWN, not rejected" in err or "UNKNOWN" in err
    assert "REJECTED" not in err, "must not claim a refusal that may not have happened"
    assert "mailbox poll --outbox" in err, "must say how to check whether it landed"
    assert "cortex_complete_proposal" in err, "must say how to close the parent if it did"


def test_a_REAL_refusal_still_says_rejected_and_exits_1(capsys):
    """Positive control. The three tests above all assert on the timeout path and
    would pass against a build that had stopped distinguishing anything at all."""
    kw, _ = _harness([REJECTED])
    rc = handle_mailbox_reply_command(_args(), **kw)

    err = capsys.readouterr().err
    assert rc == 1, "a server refusal is a different outcome from no answer"
    assert "REJECTED" in err


def test_the_happy_path_posts_once(capsys):
    """Second control: the retry must not fire when nothing went wrong."""
    kw, calls = _harness([OK, COMPLETED])
    rc = handle_mailbox_reply_command(_args(), **kw)

    assert rc == 0
    assert len([c for c in calls if c["url"].endswith("/propose")]) == 1


@pytest.mark.parametrize("http_status", [400, 401, 403, 409, 500, 502])
def test_every_real_http_status_is_a_refusal_not_an_unknown(http_status, capsys):
    """Only -1 means 'no answer'. A 500 IS an answer — the server replied."""
    kw, _ = _harness([(http_status, {"error": "x"})])
    assert handle_mailbox_reply_command(_args(), **kw) == 1


# --------------------------------------------------------------------------
# The control that was WRITTEN, then LOST IN A REWRITE, then shipped a
# regression. Restored here permanently.
# --------------------------------------------------------------------------


def test_DIFFERENT_replies_do_not_collide_into_one_key():
    """The regression this file failed to prevent, and the reason it failed.

    `parent_id` and `summary` are both in `_VOLATILE_PARAM_KEYS` — correctly, for
    a generic propose. Passing them as the key's params therefore left `{}`, so
    EVERY reply of the same type to the same peer computed the identical key. The
    ledger swallowed genuinely new replies as replays and returned ok:true.
    Reported 2026-09-08 after a distinct message was lost.

    An assertion in this exact shape existed in the first draft of this file and
    was dropped when the file was rewritten to drive the handler through its
    injected poster. The rewrite was the right call and it silently removed the
    one control that mattered — so this is pinned below the retry test rather
    than folded into it, where a future rewrite would have to delete it on
    purpose.
    """
    kw_a, calls_a = _harness([OK, COMPLETED])
    handle_mailbox_reply_command(_args(parent_id="prop_ONE", summary="first"), **kw_a)

    kw_b, calls_b = _harness([OK, COMPLETED])
    handle_mailbox_reply_command(_args(parent_id="prop_TWO", summary="second"), **kw_b)

    key_a = next(c["body"]["payload"]["idempotency_key"] for c in calls_a if c["url"].endswith("/propose"))
    key_b = next(c["body"]["payload"]["idempotency_key"] for c in calls_b if c["url"].endswith("/propose"))
    assert key_a and key_b
    assert key_a != key_b, "two different replies collapsed to one key — the ledger will swallow the second"


def test_the_SAME_reply_body_to_a_DIFFERENT_parent_is_still_distinct():
    """The narrower half: identical prose, different thread. Acking two peers'
    requests with the same wording is ordinary, and must not dedupe."""
    kw_a, calls_a = _harness([OK, COMPLETED])
    handle_mailbox_reply_command(_args(parent_id="prop_ONE", summary="done"), **kw_a)
    kw_b, calls_b = _harness([OK, COMPLETED])
    handle_mailbox_reply_command(_args(parent_id="prop_TWO", summary="done"), **kw_b)

    key_a = next(c["body"]["payload"]["idempotency_key"] for c in calls_a if c["url"].endswith("/propose"))
    key_b = next(c["body"]["payload"]["idempotency_key"] for c in calls_b if c["url"].endswith("/propose"))
    assert key_a != key_b, "same wording to a different parent is a different action"
