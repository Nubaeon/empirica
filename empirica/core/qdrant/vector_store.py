"""
Qdrant vector store for Empirica projects — backward-compatible re-export shim.

All implementations have been modularized into sub-modules:
  connection.py      - Client, availability, embedding infrastructure
  collections.py     - Collection naming, initialization, migration
  memory.py          - Core memory embed/upsert/search
  epistemics_store.py - Epistemic learning trajectories
  global_sync.py     - Cross-project knowledge aggregation
  eidetic.py         - Stable facts with confidence scoring
  episodic.py        - Session narratives with temporal decay
  goals.py           - Goal/subtask semantic search
  calibration.py     - Grounded verification & trajectory
  intent_layer.py    - Assumptions, decisions, intent edges
  decay.py           - Confidence decay, staleness, urgency

For new code, import directly from sub-modules.
This shim re-exports everything for backward compatibility.
"""
# --- Connection infrastructure ---
from empirica.core.qdrant.connection import (  # noqa: F401
    _check_qdrant_available,
    _get_qdrant_imports,
    _get_embedding_safe,
    _get_vector_size,
    _get_qdrant_client,
    _service_url,
    _rest_search,
)

# --- Collection naming + init ---
from empirica.core.qdrant.collections import (  # noqa: F401
    _docs_collection,
    _memory_collection,
    _epistemics_collection,
    _global_learnings_collection,
    _eidetic_collection,
    _episodic_collection,
    _global_eidetic_collection,
    _goals_collection,
    _calibration_collection,
    _assumptions_collection,
    _decisions_collection,
    _intents_collection,
    init_collections,
    init_global_collection,
    recreate_collection,
    recreate_project_collections,
    recreate_global_collections,
    get_collection_info,
)

# --- Core memory operations ---
from empirica.core.qdrant.memory import (  # noqa: F401
    embed_single_memory_item,
    upsert_docs,
    upsert_memory,
    search,
)

# --- Epistemic trajectories ---
from empirica.core.qdrant.epistemics_store import (  # noqa: F401
    upsert_epistemics,
    search_epistemics,
)

# --- Global learnings ---
from empirica.core.qdrant.global_sync import (  # noqa: F401
    embed_to_global,
    search_global,
    sync_high_impact_to_global,
    embed_dead_end_with_branch_context,
    search_similar_dead_ends,
    search_global_dead_ends,
)

# --- Eidetic memory ---
from empirica.core.qdrant.eidetic import (  # noqa: F401
    embed_eidetic,
    search_eidetic,
    confirm_eidetic_fact,
)

# --- Episodic memory ---
from empirica.core.qdrant.episodic import (  # noqa: F401
    embed_episodic,
    search_episodic,
    create_session_episode,
)

# --- Goals & subtasks ---
from empirica.core.qdrant.goals import (  # noqa: F401
    embed_goal,
    embed_subtask,
    search_goals,
    update_goal_status,
    sync_goals_to_qdrant,
)

# --- Calibration ---
from empirica.core.qdrant.calibration import (  # noqa: F401
    embed_grounded_verification,
    embed_calibration_trajectory,
    search_calibration_patterns,
)

# --- Intent layer ---
from empirica.core.qdrant.intent_layer import (  # noqa: F401
    embed_assumption,
    embed_decision,
    embed_intent_edge,
    search_assumptions,
    search_decisions,
    search_intents,
)

# --- Decay & lifecycle ---
from empirica.core.qdrant.decay import (  # noqa: F401
    decay_eidetic_fact,
    decay_eidetic_by_finding,
    propagate_lesson_confidence_to_qdrant,
    auto_sync_session_to_global,
    apply_staleness_signal,
    update_assumption_urgency,
)
