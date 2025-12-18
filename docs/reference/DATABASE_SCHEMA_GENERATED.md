# Empirica Database Schema Reference (v4.0)

**Generated from code:** 2025-12-16
**Total tables:** 23
**Total indexes:** 45
**Source:** `session_database.py`

---

## Table of Contents

### Core
- [sessions](#sessions)
- [cascades](#cascades)
- [reflexes](#reflexes)

### Goals & Tasks
- [goals](#goals)
- [subtasks](#subtasks)

### Investigation
- [investigation_tools](#investigation-tools)
- [investigation_logs](#investigation-logs)
- [act_logs](#act-logs)
- [investigation_branches](#investigation-branches)
- [merge_decisions](#merge-decisions)

### Project Tracking
- [projects](#projects)
- [project_handoffs](#project-handoffs)
- [project_findings](#project-findings)
- [project_unknowns](#project-unknowns)
- [project_dead_ends](#project-dead-ends)
- [project_reference_docs](#project-reference-docs)
- [epistemic_sources](#epistemic-sources)

### Handoffs
- [handoff_reports](#handoff-reports)

### Monitoring
- [divergence_tracking](#divergence-tracking)
- [drift_monitoring](#drift-monitoring)
- [epistemic_snapshots](#epistemic-snapshots)

### Learning
- [bayesian_beliefs](#bayesian-beliefs)
- [mistakes_made](#mistakes-made)

---

## Core

### `sessions`

**13 columns**

**Columns:**

- **`session_id`** | Type: `TEXT` | 🔑 PRIMARY KEY
- **`ai_id`** | Type: `TEXT` | NOT NULL
- **`user_id`** | Type: `TEXT`
- **`start_time`** | Type: `TIMESTAMP` | NOT NULL
- **`end_time`** | Type: `TIMESTAMP`
- **`bootstrap_level`** | Type: `INTEGER` | NOT NULL
- **`components_loaded`** | Type: `INTEGER` | NOT NULL
- **`total_turns`** | Type: `INTEGER` | Default: `0`
- **`total_cascades`** | Type: `INTEGER` | Default: `0`
- **`avg_confidence`** | Type: `REAL`
- **`drift_detected`** | Type: `BOOLEAN` | Default: `0`
- **`session_notes`** | Type: `TEXT`
- **`created_at`** | Type: `TIMESTAMP` | Default: `CURRENT_TIMESTAMP`

---

### `cascades`

**22 columns**

**Columns:**

- **`cascade_id`** | Type: `TEXT` | 🔑 PRIMARY KEY
- **`session_id`** | Type: `TEXT` | NOT NULL
- **`task`** | Type: `TEXT` | NOT NULL
- **`context_json`** | Type: `TEXT`
- **`goal_id`** | Type: `TEXT`
- **`goal_json`** | Type: `TEXT`
- **`preflight_completed`** | Type: `BOOLEAN` | Default: `0`
- **`think_completed`** | Type: `BOOLEAN` | Default: `0`
- **`plan_completed`** | Type: `BOOLEAN` | Default: `0`
- **`investigate_completed`** | Type: `BOOLEAN` | Default: `0`
- **`check_completed`** | Type: `BOOLEAN` | Default: `0`
- **`act_completed`** | Type: `BOOLEAN` | Default: `0`
- **`postflight_completed`** | Type: `BOOLEAN` | Default: `0`
- **`final_action`** | Type: `TEXT`
- **`final_confidence`** | Type: `REAL`
- **`investigation_rounds`** | Type: `INTEGER` | Default: `0`
- **`duration_ms`** | Type: `INTEGER`
- **`started_at`** | Type: `TIMESTAMP` | NOT NULL
- **`completed_at`** | Type: `TIMESTAMP`
- **`engagement_gate_passed`** | Type: `BOOLEAN`
- **`bayesian_active`** | Type: `BOOLEAN` | Default: `0`
- **`drift_monitored`** | Type: `BOOLEAN` | Default: `0`

---

### `reflexes`

**22 columns**

**Columns:**

- **`id`** | Type: `INTEGER` | 🔑 PRIMARY KEY
- **`session_id`** | Type: `TEXT` | NOT NULL
- **`cascade_id`** | Type: `TEXT`
- **`phase`** | Type: `TEXT` | NOT NULL
- **`round`** | Type: `INTEGER` | Default: `1`
- **`timestamp`** | Type: `REAL` | NOT NULL
- **`--`** | Type: `13`
- **`know`** | Type: `REAL`
- **`do`** | Type: `REAL`
- **`context`** | Type: `REAL`
- **`clarity`** | Type: `REAL`
- **`coherence`** | Type: `REAL`
- **`signal`** | Type: `REAL`
- **`density`** | Type: `REAL`
- **`state`** | Type: `REAL`
- **`change`** | Type: `REAL`
- **`completion`** | Type: `REAL`
- **`impact`** | Type: `REAL`
- **`uncertainty`** | Type: `REAL`
- **`--`** | Type: `Metadata`
- **`reasoning`** | Type: `TEXT`
- **`evidence`** | Type: `TEXT`

---

## Goals & Tasks

### `goals`

**14 columns**

**Columns:**

- **`id`** | Type: `TEXT` | 🔑 PRIMARY KEY
- **`session_id`** | Type: `TEXT` | NOT NULL
- **`objective`** | Type: `TEXT` | NOT NULL
- **`scope`** | Type: `TEXT` | NOT NULL
- **`--`** | Type: `JSON`
- **`duration`** | Type: `TEXT`
- **`coordination}`** | Type: `estimated_complexity`
- **`created_timestamp`** | Type: `REAL` | NOT NULL
- **`completed_timestamp`** | Type: `REAL`
- **`is_completed`** | Type: `BOOLEAN` | Default: `0`
- **`goal_data`** | Type: `TEXT` | NOT NULL
- **`status`** | Type: `TEXT` | Default: `'in_progress'`
- **`--`** | Type: `TEXT`
- **`--`** | Type: `Optional`

---

### `subtasks`

**12 columns**

**Columns:**

- **`id`** | Type: `TEXT` | 🔑 PRIMARY KEY
- **`goal_id`** | Type: `TEXT` | NOT NULL
- **`description`** | Type: `TEXT` | NOT NULL
- **`status`** | Type: `TEXT` | NOT NULL | Default: `'pending'`
- **`epistemic_importance`** | Type: `TEXT` | NOT NULL | Default: `'medium'`
- **`estimated_tokens`** | Type: `INTEGER`
- **`actual_tokens`** | Type: `INTEGER`
- **`completion_evidence`** | Type: `TEXT`
- **`notes`** | Type: `TEXT`
- **`created_timestamp`** | Type: `REAL` | NOT NULL
- **`completed_timestamp`** | Type: `REAL`
- **`subtask_data`** | Type: `TEXT` | NOT NULL

---

## Investigation

### `investigation_tools`

**11 columns**

**Columns:**

- **`tool_execution_id`** | Type: `TEXT` | 🔑 PRIMARY KEY
- **`cascade_id`** | Type: `TEXT` | NOT NULL
- **`round_number`** | Type: `INTEGER` | NOT NULL
- **`tool_name`** | Type: `TEXT` | NOT NULL
- **`tool_purpose`** | Type: `TEXT`
- **`target_vector`** | Type: `TEXT`
- **`success`** | Type: `BOOLEAN` | NOT NULL
- **`confidence_gain`** | Type: `REAL`
- **`information_gained`** | Type: `TEXT`
- **`duration_ms`** | Type: `INTEGER`
- **`executed_at`** | Type: `TIMESTAMP` | Default: `CURRENT_TIMESTAMP`

---

### `investigation_logs`

**10 columns**

**Columns:**

- **`log_id`** | Type: `TEXT` | 🔑 PRIMARY KEY
- **`session_id`** | Type: `TEXT` | NOT NULL
- **`cascade_id`** | Type: `TEXT`
- **`round_number`** | Type: `INTEGER` | NOT NULL
- **`tools_mentioned`** | Type: `TEXT`
- **`findings`** | Type: `TEXT`
- **`confidence_before`** | Type: `REAL`
- **`confidence_after`** | Type: `REAL`
- **`summary`** | Type: `TEXT`
- **`assessed_at`** | Type: `TIMESTAMP` | Default: `CURRENT_TIMESTAMP`

---

### `act_logs`

**8 columns**

**Columns:**

- **`act_id`** | Type: `TEXT` | 🔑 PRIMARY KEY
- **`session_id`** | Type: `TEXT` | NOT NULL
- **`cascade_id`** | Type: `TEXT`
- **`action_type`** | Type: `TEXT` | NOT NULL
- **`action_rationale`** | Type: `TEXT`
- **`final_confidence`** | Type: `REAL`
- **`goal_id`** | Type: `TEXT`
- **`assessed_at`** | Type: `TIMESTAMP` | Default: `CURRENT_TIMESTAMP`

---

### `investigation_branches`

**17 columns**

**Columns:**

- **`id`** | Type: `TEXT` | 🔑 PRIMARY KEY
- **`session_id`** | Type: `TEXT` | NOT NULL
- **`branch_name`** | Type: `TEXT` | NOT NULL
- **`investigation_path`** | Type: `TEXT` | NOT NULL
- **`git_branch_name`** | Type: `TEXT` | NOT NULL
- **`--`** | Type: `Epistemic` | NOT NULL
- **`postflight_vectors`** | Type: `TEXT`
- **`--`** | Type: `Cost` | Default: `0`
- **`time_spent_minutes`** | Type: `INTEGER` | Default: `0`
- **`--`** | Type: `Merge`
- **`epistemic_quality`** | Type: `REAL`
- **`is_winner`** | Type: `BOOLEAN` | Default: `FALSE`
- **`--`** | Type: `Timestamps` | NOT NULL
- **`checkpoint_timestamp`** | Type: `REAL`
- **`merged_timestamp`** | Type: `REAL`
- **`status`** | Type: `TEXT` | Default: `'active'`
- **`branch_metadata`** | Type: `TEXT`

---

### `merge_decisions`

**11 columns**

**Columns:**

- **`id`** | Type: `TEXT` | 🔑 PRIMARY KEY
- **`session_id`** | Type: `TEXT` | NOT NULL
- **`investigation_round`** | Type: `INTEGER` | NOT NULL
- **`winning_branch_id`** | Type: `TEXT` | NOT NULL
- **`winning_branch_name`** | Type: `TEXT`
- **`winning_score`** | Type: `REAL` | NOT NULL
- **`other_branches`** | Type: `TEXT`
- **`decision_rationale`** | Type: `TEXT` | NOT NULL
- **`auto_merged`** | Type: `BOOLEAN` | Default: `TRUE`
- **`created_timestamp`** | Type: `REAL` | NOT NULL
- **`decision_metadata`** | Type: `TEXT`

---

## Project Tracking

### `projects`

**12 columns**

**Columns:**

- **`id`** | Type: `TEXT` | 🔑 PRIMARY KEY
- **`name`** | Type: `TEXT` | NOT NULL
- **`description`** | Type: `TEXT`
- **`repos`** | Type: `TEXT`
- **`created_timestamp`** | Type: `REAL` | NOT NULL
- **`last_activity_timestamp`** | Type: `REAL`
- **`status`** | Type: `TEXT` | Default: `'active'`
- **`metadata`** | Type: `TEXT`
- **`total_sessions`** | Type: `INTEGER` | Default: `0`
- **`total_goals`** | Type: `INTEGER` | Default: `0`
- **`total_epistemic_deltas`** | Type: `TEXT`
- **`project_data`** | Type: `TEXT` | NOT NULL

---

### `project_handoffs`

**13 columns**

**Columns:**

- **`id`** | Type: `TEXT` | 🔑 PRIMARY KEY
- **`project_id`** | Type: `TEXT` | NOT NULL
- **`created_timestamp`** | Type: `REAL` | NOT NULL
- **`project_summary`** | Type: `TEXT` | NOT NULL
- **`sessions_included`** | Type: `TEXT` | NOT NULL
- **`total_learning_deltas`** | Type: `TEXT`
- **`key_decisions`** | Type: `TEXT`
- **`patterns_discovered`** | Type: `TEXT`
- **`mistakes_summary`** | Type: `TEXT`
- **`remaining_work`** | Type: `TEXT`
- **`repos_touched`** | Type: `TEXT`
- **`next_session_bootstrap`** | Type: `TEXT`
- **`handoff_data`** | Type: `TEXT` | NOT NULL

---

### `project_findings`

**8 columns**

**Columns:**

- **`id`** | Type: `TEXT` | 🔑 PRIMARY KEY
- **`project_id`** | Type: `TEXT` | NOT NULL
- **`session_id`** | Type: `TEXT` | NOT NULL
- **`goal_id`** | Type: `TEXT`
- **`subtask_id`** | Type: `TEXT`
- **`finding`** | Type: `TEXT` | NOT NULL
- **`created_timestamp`** | Type: `REAL` | NOT NULL
- **`finding_data`** | Type: `TEXT` | NOT NULL

---

### `project_unknowns`

**11 columns**

**Columns:**

- **`id`** | Type: `TEXT` | 🔑 PRIMARY KEY
- **`project_id`** | Type: `TEXT` | NOT NULL
- **`session_id`** | Type: `TEXT` | NOT NULL
- **`goal_id`** | Type: `TEXT`
- **`subtask_id`** | Type: `TEXT`
- **`unknown`** | Type: `TEXT` | NOT NULL
- **`is_resolved`** | Type: `BOOLEAN` | Default: `FALSE`
- **`resolved_by`** | Type: `TEXT`
- **`created_timestamp`** | Type: `REAL` | NOT NULL
- **`resolved_timestamp`** | Type: `REAL`
- **`unknown_data`** | Type: `TEXT` | NOT NULL

---

### `project_dead_ends`

**9 columns**

**Columns:**

- **`id`** | Type: `TEXT` | 🔑 PRIMARY KEY
- **`project_id`** | Type: `TEXT` | NOT NULL
- **`session_id`** | Type: `TEXT` | NOT NULL
- **`goal_id`** | Type: `TEXT`
- **`subtask_id`** | Type: `TEXT`
- **`approach`** | Type: `TEXT` | NOT NULL
- **`why_failed`** | Type: `TEXT` | NOT NULL
- **`created_timestamp`** | Type: `REAL` | NOT NULL
- **`dead_end_data`** | Type: `TEXT` | NOT NULL

---

### `project_reference_docs`

**7 columns**

**Columns:**

- **`id`** | Type: `TEXT` | 🔑 PRIMARY KEY
- **`project_id`** | Type: `TEXT` | NOT NULL
- **`doc_path`** | Type: `TEXT` | NOT NULL
- **`doc_type`** | Type: `TEXT`
- **`description`** | Type: `TEXT`
- **`created_timestamp`** | Type: `REAL` | NOT NULL
- **`doc_data`** | Type: `TEXT` | NOT NULL

---

### `epistemic_sources`

**14 columns**

**Columns:**

- **`id`** | Type: `TEXT` | 🔑 PRIMARY KEY
- **`project_id`** | Type: `TEXT` | NOT NULL
- **`session_id`** | Type: `TEXT`
- **`source_type`** | Type: `TEXT` | NOT NULL
- **`source_url`** | Type: `TEXT`
- **`title`** | Type: `TEXT` | NOT NULL
- **`description`** | Type: `TEXT`
- **`confidence`** | Type: `REAL` | Default: `0.5`
- **`epistemic_layer`** | Type: `TEXT`
- **`supports_vectors`** | Type: `TEXT`
- **`related_findings`** | Type: `TEXT`
- **`discovered_by_ai`** | Type: `TEXT`
- **`discovered_at`** | Type: `TIMESTAMP` | NOT NULL
- **`source_metadata`** | Type: `TEXT`

---

## Handoffs

### `handoff_reports`

**18 columns**

**Columns:**

- **`session_id`** | Type: `TEXT` | 🔑 PRIMARY KEY
- **`ai_id`** | Type: `TEXT` | NOT NULL
- **`timestamp`** | Type: `TEXT` | NOT NULL
- **`task_summary`** | Type: `TEXT`
- **`duration_seconds`** | Type: `REAL`
- **`epistemic_deltas`** | Type: `TEXT`
- **`key_findings`** | Type: `TEXT`
- **`knowledge_gaps_filled`** | Type: `TEXT`
- **`remaining_unknowns`** | Type: `TEXT`
- **`investigation_tools`** | Type: `TEXT`
- **`next_session_context`** | Type: `TEXT`
- **`recommended_next_steps`** | Type: `TEXT`
- **`artifacts_created`** | Type: `TEXT`
- **`calibration_status`** | Type: `TEXT`
- **`overall_confidence_delta`** | Type: `REAL`
- **`compressed_json`** | Type: `TEXT`
- **`markdown_report`** | Type: `TEXT`
- **`created_at`** | Type: `REAL` | NOT NULL

---

## Monitoring

### `divergence_tracking`

**16 columns**

**Columns:**

- **`divergence_id`** | Type: `TEXT` | 🔑 PRIMARY KEY
- **`cascade_id`** | Type: `TEXT` | NOT NULL
- **`turn_number`** | Type: `INTEGER` | NOT NULL
- **`delegate_perspective`** | Type: `TEXT`
- **`trustee_perspective`** | Type: `TEXT`
- **`divergence_score`** | Type: `REAL` | NOT NULL
- **`divergence_reason`** | Type: `TEXT`
- **`synthesis_needed`** | Type: `BOOLEAN` | NOT NULL
- **`delegate_weight`** | Type: `REAL`
- **`trustee_weight`** | Type: `REAL`
- **`tension_acknowledged`** | Type: `BOOLEAN`
- **`final_response`** | Type: `TEXT`
- **`synthesis_strategy`** | Type: `TEXT`
- **`user_alerted`** | Type: `BOOLEAN` | Default: `0`
- **`sycophancy_reset`** | Type: `BOOLEAN` | Default: `0`
- **`recorded_at`** | Type: `TIMESTAMP` | Default: `CURRENT_TIMESTAMP`

---

### `drift_monitoring`

**15 columns**

**Columns:**

- **`drift_id`** | Type: `TEXT` | 🔑 PRIMARY KEY
- **`session_id`** | Type: `TEXT` | NOT NULL
- **`analysis_window_start`** | Type: `TIMESTAMP`
- **`analysis_window_end`** | Type: `TIMESTAMP`
- **`sycophancy_detected`** | Type: `BOOLEAN` | Default: `0`
- **`delegate_weight_early`** | Type: `REAL`
- **`delegate_weight_recent`** | Type: `REAL`
- **`delegate_weight_drift`** | Type: `REAL`
- **`tension_avoidance_detected`** | Type: `BOOLEAN` | Default: `0`
- **`tension_rate_early`** | Type: `REAL`
- **`tension_rate_recent`** | Type: `REAL`
- **`tension_rate_drift`** | Type: `REAL`
- **`recommendation`** | Type: `TEXT`
- **`severity`** | Type: `TEXT`
- **`analyzed_at`** | Type: `TIMESTAMP` | Default: `CURRENT_TIMESTAMP`

---

### `epistemic_snapshots`

**20 columns**

**Columns:**

- **`snapshot_id`** | Type: `TEXT` | 🔑 PRIMARY KEY
- **`session_id`** | Type: `TEXT` | NOT NULL
- **`ai_id`** | Type: `TEXT` | NOT NULL
- **`timestamp`** | Type: `TEXT` | NOT NULL
- **`cascade_phase`** | Type: `TEXT`
- **`cascade_id`** | Type: `TEXT`
- **`vectors`** | Type: `TEXT` | NOT NULL
- **`delta`** | Type: `TEXT`
- **`previous_snapshot_id`** | Type: `TEXT`
- **`context_summary`** | Type: `TEXT`
- **`evidence_refs`** | Type: `TEXT`
- **`db_session_ref`** | Type: `TEXT`
- **`domain_vectors`** | Type: `TEXT`
- **`original_context_tokens`** | Type: `INTEGER` | Default: `0`
- **`snapshot_tokens`** | Type: `INTEGER` | Default: `0`
- **`compression_ratio`** | Type: `REAL` | Default: `0.0`
- **`information_loss_estimate`** | Type: `REAL` | Default: `0.0`
- **`fidelity_score`** | Type: `REAL` | Default: `1.0`
- **`transfer_count`** | Type: `INTEGER` | Default: `0`
- **`created_at`** | Type: `TEXT` | Default: `CURRENT_TIMESTAMP`

---

## Learning

### `bayesian_beliefs`

**9 columns**

**Columns:**

- **`belief_id`** | Type: `TEXT` | 🔑 PRIMARY KEY
- **`cascade_id`** | Type: `TEXT` | NOT NULL
- **`vector_name`** | Type: `TEXT` | NOT NULL
- **`mean`** | Type: `REAL` | NOT NULL
- **`variance`** | Type: `REAL` | NOT NULL
- **`evidence_count`** | Type: `INTEGER` | Default: `0`
- **`prior_mean`** | Type: `REAL` | NOT NULL
- **`prior_variance`** | Type: `REAL` | NOT NULL
- **`last_updated`** | Type: `TIMESTAMP`

---

### `mistakes_made`

**10 columns**

**Columns:**

- **`id`** | Type: `TEXT` | 🔑 PRIMARY KEY
- **`session_id`** | Type: `TEXT` | NOT NULL
- **`goal_id`** | Type: `TEXT`
- **`mistake`** | Type: `TEXT` | NOT NULL
- **`why_wrong`** | Type: `TEXT` | NOT NULL
- **`cost_estimate`** | Type: `TEXT`
- **`root_cause_vector`** | Type: `TEXT`
- **`prevention`** | Type: `TEXT`
- **`created_timestamp`** | Type: `REAL` | NOT NULL
- **`mistake_data`** | Type: `TEXT` | NOT NULL

---

## Indexes

**45 indexes defined**

### `bayesian_beliefs`

- `idx_beliefs_cascade` on `(cascade_id)`

### `cascades`

- `idx_cascades_session` on `(session_id)`
- `idx_cascades_confidence` on `(final_confidence)`

### `divergence_tracking`

- `idx_divergence_cascade` on `(cascade_id)`

### `epistemic_snapshots`

- `idx_snapshots_session` on `(session_id)`
- `idx_snapshots_ai` on `(ai_id)`
- `idx_snapshots_cascade` on `(cascade_id)`
- `idx_snapshots_created` on `(created_at)`

### `epistemic_sources`

- `idx_epistemic_sources_project` on `(project_id)`
- `idx_epistemic_sources_session` on `(session_id)`
- `idx_epistemic_sources_type` on `(source_type)`
- `idx_epistemic_sources_confidence` on `(confidence)`

### `goals`

- `idx_goals_beads_issue_id` on `(beads_issue_id)`
- `idx_goals_session` on `(session_id)`
- `idx_goals_status` on `(status)`

### `handoff_reports`

- `idx_handoff_ai` on `(ai_id)`
- `idx_handoff_timestamp` on `(timestamp)`
- `idx_handoff_created` on `(created_at)`

### `investigation_branches`

- `idx_investigation_branches_session` on `(session_id)`
- `idx_investigation_branches_status` on `(status)`
- `idx_investigation_branches_winner` on `(is_winner)`
- `idx_investigation_branches_merge_score` on `(merge_score)`

### `investigation_tools`

- `idx_tools_cascade` on `(cascade_id)`

### `merge_decisions`

- `idx_merge_decisions_session` on `(session_id)`
- `idx_merge_decisions_round` on `(investigation_round)`
- `idx_merge_decisions_winning_branch` on `(winning_branch_id)`

### `mistakes_made`

- `idx_mistakes_session` on `(session_id)`
- `idx_mistakes_goal` on `(goal_id)`

### `project_dead_ends`

- `idx_project_dead_ends_project` on `(project_id)`

### `project_findings`

- `idx_project_findings_project` on `(project_id)`
- `idx_project_findings_session` on `(session_id)`

### `project_handoffs`

- `idx_project_handoffs_project` on `(project_id)`
- `idx_project_handoffs_timestamp` on `(created_timestamp)`

### `project_reference_docs`

- `idx_project_reference_docs_project` on `(project_id)`

### `project_unknowns`

- `idx_project_unknowns_project` on `(project_id)`
- `idx_project_unknowns_resolved` on `(is_resolved)`

### `projects`

- `idx_projects_status` on `(status)`
- `idx_projects_activity` on `(last_activity_timestamp)`

### `reflexes`

- `idx_reflexes_session` on `(session_id)`
- `idx_reflexes_phase` on `(phase)`

### `sessions`

- `idx_sessions_ai` on `(ai_id)`
- `idx_sessions_start` on `(start_time)`
- `idx_sessions_project` on `(project_id)`

### `subtasks`

- `idx_subtasks_goal` on `(goal_id)`
- `idx_subtasks_status` on `(status)`

---

## Notes

- **Generated documentation:** This file is auto-generated from the codebase.
- **100% accuracy:** Every table/column listed here exists in the current database schema.
- **Schema evolution:** This represents the current v4.0 schema.

**To regenerate this documentation:**
```bash
cd dev_scripts/doc_regeneration
python3 extract_database_schema.py
python3 generate_database_schema_markdown.py
```

**Last updated:** 2025-12-16 20:42:55 UTC
