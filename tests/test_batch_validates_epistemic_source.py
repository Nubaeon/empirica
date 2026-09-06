"""The batch path must enforce the enum the single verbs enforce.

`finding-log --epistemic-source ran` is refused by argparse `choices`. The same
value inside a `log-artifacts` payload was accepted, passed to a writer that
discarded anything unrecognised, and stored NULL — node created, `ok` returned,
provenance silently gone.

Same field, two paths, opposite behaviour. And the batch path is the one the
guidance tells practitioners to PREFER, so it is the one that loses provenance.

Measured 2026-09-06: one practitioner batch-logged a long session's artifacts
with `"epistemic_source": "ran"` throughout. Every one stored NULL. The single
verb would have refused the first call; the batch path said nothing across dozens.
"""

from __future__ import annotations

import pytest

from empirica.cli.command_handlers.graph_commands import _validate_graph
from empirica.data.epistemic_source import EPISTEMIC_SOURCES


def _payload(src):
    return {
        "nodes": [{"ref": "f1", "type": "finding", "data": {"finding": "x", "epistemic_source": src}}],
        "edges": [],
    }


@pytest.mark.parametrize("src", sorted(EPISTEMIC_SOURCES))
def test_every_valid_source_is_accepted(src):
    """Positive control. Without it, a validator that rejected EVERYTHING would
    pass the rejection test below and break all batch logging."""
    assert _validate_graph(_payload(src)) == []


def test_omitting_the_source_is_still_allowed():
    assert _validate_graph({"nodes": [{"ref": "f1", "type": "finding", "data": {"finding": "x"}}], "edges": []}) == []


@pytest.mark.parametrize("src", ["ran", "read", "retrieved", "assumed", "", "SEARCH"])
def test_an_out_of_vocabulary_source_is_REFUSED_not_dropped(src):
    errors = _validate_graph(_payload(src))
    assert errors, f"{src!r} was accepted — it will be silently discarded at write time"
    assert "epistemic_source" in errors[0]


def test_the_error_names_the_confusion_that_causes_it():
    """`ran`/`read`/`retrieved` are CHECK grounding values. A practitioner fluent
    in one vocabulary reaches for it in the other; the message has to say so, or
    the fix is a guess."""
    err = _validate_graph(_payload("ran"))[0]
    assert "grounding" in err
    assert "search" in err
    for valid in EPISTEMIC_SOURCES:
        assert valid in err, "the message must list what IS allowed, not only what is not"


def test_validation_happens_BEFORE_anything_is_written():
    """A mid-batch raise leaves half a graph committed. The bad node must be
    caught alongside the other shape errors, with the good nodes not created."""
    payload = {
        "nodes": [
            {"ref": "ok1", "type": "finding", "data": {"finding": "fine", "epistemic_source": "search"}},
            {"ref": "bad", "type": "finding", "data": {"finding": "x", "epistemic_source": "ran"}},
        ],
        "edges": [],
    }
    errors = _validate_graph(payload)
    assert len(errors) == 1 and "bad" in errors[0], "the whole payload must fail, naming the offending ref"
