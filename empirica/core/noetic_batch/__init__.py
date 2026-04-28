"""Batched investigation primitive — bundles ≥3 investigation operations into
one call that returns a single merged structured response.

Use when you have multiple reads/greps/globs/investigate queries that belong
to the same investigation intent. Individual Read/Grep/Glob/investigate are
already noetic in any phase — they don't need batching for gating reasons.
The value of noetic-batch is operational: fewer round-trips, one merged
result in your conversation, ergonomic for cross-cutting investigations.

NOT a Sentinel bypass. Calling it once for a single read is misuse —
just use the underlying tool directly.

Same architectural pattern as `cortex_log_artifacts`: a graph schema
replacing N individual logging calls.

Public API:
    run_batch(payload: dict) -> dict
    NoeticBatchInput  (pydantic model)
    NoeticBatchResult (pydantic model)
    SCHEMA_VERSION

See docs/architecture/NOETIC_BATCH_SPEC.md for the full design.
"""

from .executor import run_batch
from .schema import (
    SCHEMA_VERSION,
    GlobOperation,
    GrepOperation,
    InvestigateOperation,
    NoeticBatchInput,
    NoeticBatchResult,
    ReadOperation,
)

__all__ = [
    "SCHEMA_VERSION",
    "GlobOperation",
    "GrepOperation",
    "InvestigateOperation",
    "NoeticBatchInput",
    "NoeticBatchResult",
    "ReadOperation",
    "run_batch",
]
