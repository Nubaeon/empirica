"""Git checkpoint and project management command parsers."""

from . import format_help_text

def add_checkpoint_parsers(subparsers):
    """Add git checkpoint management command parsers (Phase 2)"""
    # Checkpoint create command
    checkpoint_create_parser = subparsers.add_parser(
        'checkpoint-create',
        help='Create git checkpoint for session (Phase 1.5/2.0)'
    )
    checkpoint_create_parser.add_argument(
        '--session-id',
        required=True,
        help=format_help_text('Session ID', required=True)
    )
    checkpoint_create_parser.add_argument(
        '--phase',
        choices=['PREFLIGHT', 'CHECK', 'ACT', 'POSTFLIGHT'],
        required=True,
        help=format_help_text('Workflow phase', required=True)
    )
    checkpoint_create_parser.add_argument(
        '--round',
        type=int,
        default=1,
        help=format_help_text('Round number', default=1)
    )
    checkpoint_create_parser.add_argument(
        '--metadata',
        help=format_help_text('JSON metadata')
    )
    checkpoint_create_parser.add_argument('--output', choices=['human', 'json'], default='human', help='Output format')
    checkpoint_create_parser.add_argument('--verbose', action='store_true', help='Show detailed operation info')

    # Checkpoint load command
    checkpoint_load_parser = subparsers.add_parser(
        'checkpoint-load',
        help='Load latest checkpoint for session'
    )
    checkpoint_load_parser.add_argument('--session-id', required=True, help='Session ID')
    checkpoint_load_parser.add_argument('--max-age', type=int, default=24, help='Max age in hours (default: 24)')
    checkpoint_load_parser.add_argument('--phase', help='Filter by specific phase (optional)')
    checkpoint_load_parser.add_argument(
        '--output',
        choices=['table', 'json'],
        default='table',
        help='Output format (also accepts --output json)'
    )
    # Add backward compatibility with --format
    checkpoint_load_parser.add_argument(
        '--format',
        dest='output',
        choices=['json', 'table'],
        help='Output format (deprecated, use --output)'
    )
    checkpoint_load_parser.add_argument('--verbose', action='store_true', help='Show detailed operation info')

    # Checkpoint list command
    checkpoint_list_parser = subparsers.add_parser(
        'checkpoint-list',
        help='List checkpoints for session'
    )
    checkpoint_list_parser.add_argument('--session-id', help='Session ID (optional, lists all if omitted)')
    checkpoint_list_parser.add_argument('--limit', type=int, default=10, help='Maximum checkpoints to show')
    checkpoint_list_parser.add_argument('--phase', help='Filter by phase (optional)')
    checkpoint_list_parser.add_argument('--output', choices=['human', 'json'], default='human', help='Output format')
    checkpoint_list_parser.add_argument('--verbose', action='store_true', help='Show detailed operation info')

    # Checkpoint diff command
    checkpoint_diff_parser = subparsers.add_parser(
        'checkpoint-diff',
        help='Show vector differences from last checkpoint'
    )
    checkpoint_diff_parser.add_argument('--session-id', required=True, help='Session ID')
    checkpoint_diff_parser.add_argument('--threshold', type=float, default=0.15, help='Significance threshold')
    checkpoint_diff_parser.add_argument('--output', choices=['human', 'json'], default='human', help='Output format')
    checkpoint_diff_parser.add_argument('--verbose', action='store_true', help='Show detailed operation info')

    # Efficiency report command
    checkpoint_sign_parser = subparsers.add_parser(
        'checkpoint-sign',
        help='Sign checkpoint with AI identity (Phase 2 - Crypto)'
    )
    checkpoint_sign_parser.add_argument('--session-id', required=True, help='Session ID')
    checkpoint_sign_parser.add_argument(
        '--phase',
        choices=['PREFLIGHT', 'CHECK', 'ACT', 'POSTFLIGHT'],
        required=True,
        help='Workflow phase'
    )
    checkpoint_sign_parser.add_argument('--round', type=int, required=True, help='Round number')
    checkpoint_sign_parser.add_argument('--ai-id', required=True, help='AI identity to sign with')
    checkpoint_sign_parser.add_argument('--output', choices=['human', 'json'], default='human', help='Output format')
    checkpoint_sign_parser.add_argument('--verbose', action='store_true', help='Show detailed operation info')

    # Checkpoint verify command
    checkpoint_verify_parser = subparsers.add_parser(
        'checkpoint-verify',
        help='Verify signed checkpoint (Phase 2 - Crypto)'
    )
    checkpoint_verify_parser.add_argument('--session-id', required=True, help='Session ID')
    checkpoint_verify_parser.add_argument(
        '--phase',
        choices=['PREFLIGHT', 'CHECK', 'ACT', 'POSTFLIGHT'],
        required=True,
        help='Workflow phase'
    )
    checkpoint_verify_parser.add_argument('--round', type=int, required=True, help='Round number')
    checkpoint_verify_parser.add_argument('--ai-id', help='AI identity (uses embedded public key if omitted)')
    checkpoint_verify_parser.add_argument('--public-key', help='Public key hex (overrides AI ID)')
    checkpoint_verify_parser.add_argument('--output', choices=['human', 'json'], default='human', help='Output format')
    checkpoint_verify_parser.add_argument('--verbose', action='store_true', help='Show detailed operation info')

    # Checkpoint signatures command
    checkpoint_signatures_parser = subparsers.add_parser(
        'checkpoint-signatures',
        help='List all signed checkpoints (Phase 2 - Crypto)'
    )
    checkpoint_signatures_parser.add_argument('--session-id', help='Filter by session ID (optional)')
    checkpoint_signatures_parser.add_argument('--ai-id', help='AI identity (only needed if no local identities exist)')
    checkpoint_signatures_parser.add_argument('--output', choices=['human', 'json'], default='human', help='Output format')
    checkpoint_signatures_parser.add_argument('--verbose', action='store_true', help='Show detailed operation info')

    # Handoff Reports Commands (Phase 1.6)
    
    # Handoff create command
    handoff_create_parser = subparsers.add_parser(
        'handoff-create',
        help='Create handoff report: epistemic (with CASCADE deltas) or planning (documentation-only)'
    )

    # AI-FIRST: Positional config file argument
    handoff_create_parser.add_argument('config', nargs='?',
        help='JSON config file path or "-" for stdin (AI-first mode)')

    # LEGACY: Flag-based arguments (backward compatible)
    handoff_create_parser.add_argument('--session-id', help=format_help_text('Session UUID', required=True))
    handoff_create_parser.add_argument('--task-summary', help=format_help_text('What was accomplished (2-3 sentences)', required=True))
    handoff_create_parser.add_argument('--summary', dest='task_summary', help='Alias for --task-summary')
    handoff_create_parser.add_argument('--key-findings', help=format_help_text('JSON array of findings', required=True))
    handoff_create_parser.add_argument('--findings', dest='key_findings', help='Alias for --key-findings')
    handoff_create_parser.add_argument('--remaining-unknowns', help=format_help_text('JSON array of unknowns'))
    handoff_create_parser.add_argument('--unknowns', dest='remaining_unknowns', help='Alias for --remaining-unknowns')
    handoff_create_parser.add_argument('--next-session-context', help=format_help_text('Critical context for next session', required=True))
    handoff_create_parser.add_argument('--artifacts', help=format_help_text('JSON array of files created'))
    handoff_create_parser.add_argument('--planning-only', action='store_true', help='Create planning handoff (no CASCADE workflow required) instead of epistemic handoff')
    handoff_create_parser.add_argument('--output', choices=['human', 'json'], default='human', help='Output format')
    handoff_create_parser.add_argument('--verbose', action='store_true', help='Show detailed operation info')

    # Handoff query command
    handoff_query_parser = subparsers.add_parser(
        'handoff-query',
        help='Query handoff reports'
    )
    handoff_query_parser.add_argument('--session-id', help='Specific session UUID')
    handoff_query_parser.add_argument('--ai-id', help='Filter by AI ID')
    handoff_query_parser.add_argument('--limit', type=int, default=5, help='Number of results (default: 5)')
    handoff_query_parser.add_argument('--output', choices=['human', 'json'], default='human', help='Output format')
    handoff_query_parser.add_argument('--verbose', action='store_true', help='Show detailed operation info')

    # Mistake Logging Commands (Learning from Failures)
    
    # Mistake log command
    mistake_log_parser = subparsers.add_parser(
        'mistake-log',
        help='Log a mistake for learning and future prevention'
    )
    mistake_log_parser.add_argument('--project-id', help='Project UUID')
    mistake_log_parser.add_argument('--session-id', required=True, help='Session UUID')
    mistake_log_parser.add_argument('--mistake', required=True, help='What was done wrong')
    mistake_log_parser.add_argument('--why-wrong', required=True, help='Explanation of why it was wrong')
    mistake_log_parser.add_argument('--cost-estimate', help='Estimated time/effort wasted (e.g., "2 hours")')
    mistake_log_parser.add_argument('--root-cause-vector', help='Epistemic vector that caused the mistake (e.g., "KNOW", "CONTEXT")')
    mistake_log_parser.add_argument('--prevention', help='How to prevent this mistake in the future')
    mistake_log_parser.add_argument('--goal-id', help='Optional goal identifier this mistake relates to')
    mistake_log_parser.add_argument('--scope', choices=['session', 'project', 'both'], help='Scope: session (ephemeral), project (persistent), or both (dual-log). Auto-inferred if omitted.')
    mistake_log_parser.add_argument('--output', choices=['human', 'json'], default='human', help='Output format')
    mistake_log_parser.add_argument('--verbose', action='store_true', help='Show detailed operation info')

    # Mistake query command
    mistake_query_parser = subparsers.add_parser(
        'mistake-query',
        help='Query logged mistakes'
    )
    mistake_query_parser.add_argument('--session-id', help='Filter by session UUID')
    mistake_query_parser.add_argument('--goal-id', help='Filter by goal UUID')
    mistake_query_parser.add_argument('--limit', type=int, default=10, help='Number of results (default: 10)')
    mistake_query_parser.add_argument('--output', choices=['human', 'json'], default='human', help='Output format')
    mistake_query_parser.add_argument('--verbose', action='store_true', help='Show detailed operation info')

    # Project Tracking Commands (Multi-repo/multi-session)
    
    # Project init command (NEW: initialize Empirica in a new repo)
    project_init_parser = subparsers.add_parser(
        'project-init',
        help='Initialize Empirica in a new git repository (creates config files)'
    )
    project_init_parser.add_argument('--project-name', help='Project name (defaults to repo name)')
    project_init_parser.add_argument('--project-description', help='Project description')
    project_init_parser.add_argument('--enable-beads', action='store_true', help='Enable BEADS by default')
    project_init_parser.add_argument('--create-semantic-index', action='store_true', help='Create SEMANTIC_INDEX.yaml template')
    project_init_parser.add_argument('--non-interactive', action='store_true', help='Skip interactive prompts')
    project_init_parser.add_argument('--force', action='store_true', help='Reinitialize if already initialized')
    project_init_parser.add_argument('--output', choices=['human', 'json'], default='human', help='Output format')
    project_init_parser.add_argument('--verbose', action='store_true', help='Show detailed operation info')

    # Project create command
    project_create_parser = subparsers.add_parser(
        'project-create',
        help='Create a new project for multi-repo tracking'
    )
    project_create_parser.add_argument('--name', required=True, help='Project name')
    project_create_parser.add_argument('--description', help='Project description')
    project_create_parser.add_argument('--repos', help='JSON array of repository names (e.g., \'["empirica", "empirica-dev"]\')')
    project_create_parser.add_argument('--output', choices=['human', 'json'], default='human', help='Output format')
    project_create_parser.add_argument('--verbose', action='store_true', help='Show detailed operation info')

    # Project handoff command
    project_handoff_parser = subparsers.add_parser(
        'project-handoff',
        help='Create project-level handoff report'
    )
    project_handoff_parser.add_argument('--project-id', required=True, help='Project UUID')
    project_handoff_parser.add_argument('--summary', required=True, help='Project summary')
    project_handoff_parser.add_argument('--key-decisions', help='JSON array of key decisions')
    project_handoff_parser.add_argument('--patterns', help='JSON array of patterns discovered')
    project_handoff_parser.add_argument('--remaining-work', help='JSON array of remaining work')
    project_handoff_parser.add_argument('--output', choices=['human', 'json'], default='human', help='Output format')
    project_handoff_parser.add_argument('--verbose', action='store_true', help='Show detailed operation info')

    # Project list command
    project_list_parser = subparsers.add_parser(
        'project-list',
        help='List all projects'
    )
    project_list_parser.add_argument('--output', choices=['human', 'json'], default='human', help='Output format')
    project_list_parser.add_argument('--verbose', action='store_true', help='Show detailed operation info')

    # Project bootstrap command
    project_bootstrap_parser = subparsers.add_parser(
        'project-bootstrap',
        help='Show epistemic breadcrumbs for project'
    )
    project_bootstrap_parser.add_argument('--project-id', required=False, help='Project UUID or name (auto-detected from git remote if omitted)')
    project_bootstrap_parser.add_argument('--session-id', required=False, help='Session UUID (auto-resolved from project if omitted)')
    project_bootstrap_parser.add_argument('--ai-id', required=False, help='AI identifier to load epistemic handoff for (e.g., claude-code)')
    project_bootstrap_parser.add_argument('--subject', help='Subject/workstream to filter by (auto-detected from directory if omitted)')
    project_bootstrap_parser.add_argument('--check-integrity', action='store_true', help='Analyze doc-code integrity (adds ~2s)')
    project_bootstrap_parser.add_argument('--context-to-inject', action='store_true', help='Generate markdown context for AI prompt injection')
    project_bootstrap_parser.add_argument('--task-description', help='Task description for context load balancing')
    project_bootstrap_parser.add_argument('--epistemic-state', help='Epistemic vectors from PREFLIGHT as JSON string (e.g., \'{"uncertainty":0.8,"know":0.3}\')')
    project_bootstrap_parser.add_argument('--include-live-state', action='store_true', help='Include current epistemic vectors + git state')
    project_bootstrap_parser.add_argument('--fresh-assess', action='store_true', help='Capture fresh state instead of loading latest checkpoint (requires --include-live-state)')
    project_bootstrap_parser.add_argument('--trigger', choices=['pre_compact', 'post_compact', 'manual'], help='Compact boundary trigger for session auto-resolution')
    project_bootstrap_parser.add_argument('--depth', choices=['minimal', 'moderate', 'full', 'auto'], default='auto', help='Context depth: minimal (~500 tokens), moderate (~1500), full (~3000-5000), auto (drift-based)')
    project_bootstrap_parser.add_argument('--output', choices=['human', 'json'], default='human', help='Output format')
    project_bootstrap_parser.add_argument('--verbose', action='store_true', help='Show detailed operation info')

    # Workspace overview command
    workspace_overview_parser = subparsers.add_parser(
        'workspace-overview',
        help='Show epistemic health overview of all projects in workspace'
    )
    workspace_overview_parser.add_argument('--output', choices=['human', 'json'], default='human', help='Output format')
    workspace_overview_parser.add_argument('--sort-by', choices=['activity', 'knowledge', 'uncertainty', 'name'], default='activity', help='Sort projects by')
    workspace_overview_parser.add_argument('--filter', choices=['active', 'inactive', 'complete'], help='Filter projects by status')
    workspace_overview_parser.add_argument('--verbose', action='store_true', help='Show detailed operation info')

    # Workspace map command
    workspace_map_parser = subparsers.add_parser(
        'workspace-map',
        help='Discover git repositories in parent directory and show epistemic health'
    )
    workspace_map_parser.add_argument('--output', choices=['human', 'json'], default='human', help='Output format')
    workspace_map_parser.add_argument('--verbose', action='store_true', help='Show detailed operation info')

    # Workspace init command - EPISTEMIC INITIALIZATION
    workspace_init_parser = subparsers.add_parser(
        'workspace-init',
        help='Initialize workspace with epistemic self-awareness (uses CASCADE workflow)'
    )
    workspace_init_parser.add_argument('--path', type=str, help='Workspace path (defaults to current directory)')
    workspace_init_parser.add_argument('--output', choices=['human', 'json'], default='human', help='Output format')
    workspace_init_parser.add_argument('--non-interactive', action='store_true', help='Skip user questions, use defaults')
    workspace_init_parser.add_argument('--verbose', action='store_true', help='Show detailed operation info')

    # Project semantic search command (Qdrant-backed)
    project_search_parser = subparsers.add_parser(
        'project-search',
        help='Semantic search for relevant docs/memory by task description'
    )
    project_search_parser.add_argument('--project-id', required=True, help='Project UUID')
    project_search_parser.add_argument('--task', required=True, help='Task description to search for')
    project_search_parser.add_argument('--type', choices=['all', 'docs', 'memory'], default='all', help='Result type (default: all)')
    project_search_parser.add_argument('--limit', type=int, default=5, help='Number of results to return (default: 5)')
    project_search_parser.add_argument('--output', choices=['human', 'json'], default='human', help='Output format')
    project_search_parser.add_argument('--verbose', action='store_true', help='Show detailed operation info')

    # Project embed (build vectors) command
    project_embed_parser = subparsers.add_parser(
        'project-embed',
        help='Embed project docs & memory into Qdrant for semantic search'
    )
    project_embed_parser.add_argument('--project-id', required=True, help='Project UUID')
    project_embed_parser.add_argument('--output', choices=['human', 'json'], default='human', help='Output format')
    project_embed_parser.add_argument('--verbose', action='store_true', help='Show detailed operation info')

    # Documentation completeness check
    doc_check_parser = subparsers.add_parser(
        'doc-check',
        help='Compute documentation completeness and suggest updates'
    )
    doc_check_parser.add_argument('--project-id', required=True, help='Project UUID')
    doc_check_parser.add_argument('--session-id', help='Optional session UUID for context')
    doc_check_parser.add_argument('--goal-id', help='Optional goal UUID for context')
    doc_check_parser.add_argument('--output', choices=['human', 'json'], default='human', help='Output format')
    doc_check_parser.add_argument('--verbose', action='store_true', help='Show detailed operation info')

    # NOTE: skill-suggest and skill-fetch are NOT YET IMPLEMENTED
    # Placeholder parsers removed to avoid confusion (use project-bootstrap instead)
    # TODO: Implement skill discovery and fetching in Phase 4
    
    # Finding log command
    finding_log_parser = subparsers.add_parser(
        'finding-log',
        help='Log a project finding (what was learned/discovered)'
    )
    finding_log_parser.add_argument('config', nargs='?', help='JSON config file or - for stdin (AI-first mode)')
    finding_log_parser.add_argument('--project-id', required=False, help='Project UUID')
    finding_log_parser.add_argument('--session-id', required=False, help='Session UUID')
    finding_log_parser.add_argument('--finding', required=False, help='What was learned/discovered')
    finding_log_parser.add_argument('--goal-id', help='Optional goal UUID')
    finding_log_parser.add_argument('--subtask-id', help='Optional subtask UUID')
    finding_log_parser.add_argument('--subject', help='Subject/workstream identifier (auto-detected from directory if omitted)')
    finding_log_parser.add_argument('--impact', type=float, help='Impact score 0.0-1.0 (importance of this finding, auto-derived from CASCADE if omitted)')
    finding_log_parser.add_argument('--scope', choices=['session', 'project', 'both'], help='Scope: session (ephemeral), project (persistent), or both (dual-log). Auto-inferred if omitted.')
    finding_log_parser.add_argument('--output', choices=['human', 'json'], default='human', help='Output format')
    finding_log_parser.add_argument('--verbose', action='store_true', help='Show detailed operation info')

    # Unknown log command
    unknown_log_parser = subparsers.add_parser(
        'unknown-log',
        help='Log a project unknown (what\'s still unclear)'
    )
    unknown_log_parser.add_argument('config', nargs='?', help='JSON config file or - for stdin (AI-first mode)')
    unknown_log_parser.add_argument('--project-id', required=False, help='Project UUID')
    unknown_log_parser.add_argument('--session-id', required=False, help='Session UUID')
    unknown_log_parser.add_argument('--unknown', required=False, help='What is unclear/unknown')
    unknown_log_parser.add_argument('--goal-id', help='Optional goal UUID')
    unknown_log_parser.add_argument('--subtask-id', help='Optional subtask UUID')
    unknown_log_parser.add_argument('--subject', help='Subject/workstream identifier (auto-detected from directory if omitted)')
    unknown_log_parser.add_argument('--impact', type=float, help='Impact score 0.0-1.0 (importance of this unknown, auto-derived from CASCADE if omitted)')
    unknown_log_parser.add_argument('--scope', choices=['session', 'project', 'both'], help='Scope: session (ephemeral), project (persistent), or both (dual-log). Auto-inferred if omitted.')
    unknown_log_parser.add_argument('--output', choices=['human', 'json'], default='human', help='Output format')
    unknown_log_parser.add_argument('--verbose', action='store_true', help='Show detailed operation info')

    # Unknown resolve command
    unknown_resolve_parser = subparsers.add_parser(
        'unknown-resolve',
        help='Mark unknown as resolved'
    )
    unknown_resolve_parser.add_argument('--unknown-id', required=True, help='Unknown UUID')
    unknown_resolve_parser.add_argument('--resolved-by', required=True, help='How was this unknown resolved?')
    unknown_resolve_parser.add_argument('--output', choices=['human', 'json'], default='json', help='Output format (default: json)')
    unknown_resolve_parser.add_argument('--verbose', action='store_true', help='Show detailed operation info')

    # Dead end log command
    deadend_log_parser = subparsers.add_parser(
        'deadend-log',
        help='Log a project dead end (what didn\'t work)'
    )
    deadend_log_parser.add_argument('config', nargs='?', help='JSON config file or - for stdin (AI-first mode)')
    deadend_log_parser.add_argument('--project-id', required=False, help='Project UUID')
    deadend_log_parser.add_argument('--session-id', required=False, help='Session UUID')
    deadend_log_parser.add_argument('--approach', required=False, help='What approach was tried')
    deadend_log_parser.add_argument('--why-failed', required=False, help='Why it failed')
    deadend_log_parser.add_argument('--goal-id', help='Optional goal UUID')
    deadend_log_parser.add_argument('--subtask-id', help='Optional subtask UUID')
    deadend_log_parser.add_argument('--subject', help='Subject/workstream identifier (auto-detected from directory if omitted)')
    deadend_log_parser.add_argument('--impact', type=float, help='Impact score 0.0-1.0 (importance of this dead end, auto-derived from CASCADE if omitted)')
    deadend_log_parser.add_argument('--scope', choices=['session', 'project', 'both'], help='Scope: session (ephemeral), project (persistent), or both (dual-log). Auto-inferred if omitted.')
    deadend_log_parser.add_argument('--output', choices=['human', 'json'], default='human', help='Output format')
    deadend_log_parser.add_argument('--verbose', action='store_true', help='Show detailed operation info')

    # Reference doc add command
    refdoc_add_parser = subparsers.add_parser(
        'refdoc-add',
        help='Add a reference document to project'
    )
    refdoc_add_parser.add_argument('--project-id', required=True, help='Project UUID')
    refdoc_add_parser.add_argument('--doc-path', required=True, help='Document path')
    refdoc_add_parser.add_argument('--doc-type', help='Document type (architecture, guide, api, design)')
    refdoc_add_parser.add_argument('--description', help='Document description')
    refdoc_add_parser.add_argument('--output', choices=['human', 'json'], default='human', help='Output format')

    # NEW: Goal Management Commands (MCP v2 Integration)
    
    # Goals create command (AI-first with config file support)
    goals_create_parser = subparsers.add_parser('goals-create',
        help='Create new goal (AI-first: use config file, Legacy: use flags)')

    # AI-FIRST: Positional config file argument (optional, takes precedence)
    goals_create_parser.add_argument('config', nargs='?',
        help='JSON config file path or "-" for stdin (AI-first mode)')

    # LEGACY: Flag-based arguments (backward compatible)
    goals_create_parser.add_argument('--session-id', help='Session ID (legacy)')
    goals_create_parser.add_argument('--ai-id', default='empirica_cli', help='AI identifier (legacy)')
    goals_create_parser.add_argument('--objective', help='Goal objective text (legacy)')
    goals_create_parser.add_argument('--scope-breadth', type=float, default=0.3, help='Goal breadth (0.0-1.0, how wide the goal spans)')
    goals_create_parser.add_argument('--scope-duration', type=float, default=0.2, help='Goal duration (0.0-1.0, expected lifetime)')
    goals_create_parser.add_argument('--scope-coordination', type=float, default=0.1, help='Goal coordination (0.0-1.0, multi-agent coordination needed)')
    goals_create_parser.add_argument('--success-criteria', help='Success criteria as JSON array (or "-" to read from stdin)')
    goals_create_parser.add_argument('--success-criteria-file', help='Read success criteria from file (avoids shell quoting issues)')
    goals_create_parser.add_argument('--estimated-complexity', type=float, help='Complexity estimate (0.0-1.0)')
    goals_create_parser.add_argument('--constraints', help='Constraints as JSON object')
    goals_create_parser.add_argument('--metadata', help='Metadata as JSON object')
    goals_create_parser.add_argument('--use-beads', action='store_true', help='Create BEADS issue and link to goal')
    goals_create_parser.add_argument('--output', choices=['human', 'json'], default='human', help='Output format')
    goals_create_parser.add_argument('--verbose', action='store_true', help='Show detailed operation info')

    # Goals add-subtask command
    goals_add_subtask_parser = subparsers.add_parser('goals-add-subtask', help='Add subtask to existing goal')
    goals_add_subtask_parser.add_argument('--goal-id', required=True, help='Goal UUID')
    goals_add_subtask_parser.add_argument('--description', required=True, help='Subtask description')
    goals_add_subtask_parser.add_argument('--importance', choices=['critical', 'high', 'medium', 'low'], default='medium', help='Epistemic importance')
    goals_add_subtask_parser.add_argument('--dependencies', help='Dependencies as JSON array')
    goals_add_subtask_parser.add_argument('--estimated-tokens', type=int, help='Estimated token usage')
    goals_add_subtask_parser.add_argument('--use-beads', action='store_true', help='Create BEADS subtask and link to goal')
    goals_add_subtask_parser.add_argument('--output', choices=['human', 'json'], default='human', help='Output format')
    
    # Goals complete-subtask command
    goals_complete_subtask_parser = subparsers.add_parser('goals-complete-subtask', help='Mark subtask as complete')
    # Use subtask-id as primary parameter, with task-id as deprecated alias for backward compatibility
    goals_complete_subtask_parser.add_argument('--subtask-id', help='Subtask UUID (preferred)')
    goals_complete_subtask_parser.add_argument('--task-id', help='Subtask UUID (deprecated, use --subtask-id)')
    goals_complete_subtask_parser.add_argument('--evidence', help='Completion evidence (commit hash, file path, etc.)')
    goals_complete_subtask_parser.add_argument('--output', choices=['human', 'json'], default='human', help='Output format')
    
    # Goals progress command
    goals_progress_parser = subparsers.add_parser('goals-progress', help='Get goal completion progress')
    goals_progress_parser.add_argument('--goal-id', required=True, help='Goal UUID')
    goals_progress_parser.add_argument('--output', choices=['human', 'json'], default='human', help='Output format')
    goals_progress_parser.add_argument('--verbose', action='store_true', help='Show detailed operation info')

    # Goals get-subtasks command (NEW)
    goals_get_subtasks_parser = subparsers.add_parser('goals-get-subtasks', help='Get detailed subtask information')
    goals_get_subtasks_parser.add_argument('--goal-id', required=True, help='Goal UUID')
    goals_get_subtasks_parser.add_argument('--output', choices=['human', 'json'], default='human', help='Output format')
    
    # Goals list command
    goals_list_parser = subparsers.add_parser('goals-list', help='List goals')
    goals_list_parser.add_argument('--ai-id', help='Filter by AI identifier')
    goals_list_parser.add_argument('--session-id', help='Filter by session ID')
    goals_list_parser.add_argument('--scope-breadth-min', type=float, help='Filter by minimum breadth (0.0-1.0)')
    goals_list_parser.add_argument('--scope-breadth-max', type=float, help='Filter by maximum breadth (0.0-1.0)')
    goals_list_parser.add_argument('--scope-duration-min', type=float, help='Filter by minimum duration (0.0-1.0)')
    goals_list_parser.add_argument('--scope-duration-max', type=float, help='Filter by maximum duration (0.0-1.0)')
    goals_list_parser.add_argument('--scope-coordination-min', type=float, help='Filter by minimum coordination (0.0-1.0)')
    goals_list_parser.add_argument('--scope-coordination-max', type=float, help='Filter by maximum coordination (0.0-1.0)')
    goals_list_parser.add_argument('--completed', action='store_true', help='Filter by completion status')
    goals_list_parser.add_argument('--output', choices=['human', 'json'], default='human', help='Output format')
    goals_list_parser.add_argument('--verbose', action='store_true', help='Show detailed operation info')

    # goals-ready command (BEADS integration - Phase 1)
    goals_ready_parser = subparsers.add_parser('goals-ready', help='Query ready work (BEADS + epistemic filtering)')
    goals_ready_parser.add_argument('--session-id', required=False, help='Session UUID (auto-detects active session if not provided)')
    goals_ready_parser.add_argument('--min-confidence', type=float, default=0.7, help='Minimum confidence threshold (0.0-1.0)')
    goals_ready_parser.add_argument('--max-uncertainty', type=float, default=0.3, help='Maximum uncertainty threshold (0.0-1.0)')
    goals_ready_parser.add_argument('--min-priority', type=int, help='Minimum BEADS priority (1, 2, or 3)')
    goals_ready_parser.add_argument('--output', choices=['human', 'json'], default='human', help='Output format')
    goals_ready_parser.add_argument('--verbose', action='store_true', help='Show detailed operation info')

    # Goals-discover command (NEW: Phase 1 - Cross-AI Goal Discovery)
    goals_discover_parser = subparsers.add_parser('goals-discover', help='Discover goals from other AIs via git')
    goals_discover_parser.add_argument('--from-ai-id', help='Filter by AI creator')
    goals_discover_parser.add_argument('--session-id', help='Filter by session')
    goals_discover_parser.add_argument('--output', choices=['human', 'json'], default='human', help='Output format')
    goals_discover_parser.add_argument('--verbose', action='store_true', help='Show detailed operation info')

    # Goals-resume command (NEW: Phase 1 - Cross-AI Goal Handoff)
    goals_resume_parser = subparsers.add_parser('goals-resume', help='Resume another AI\'s goal')
    goals_resume_parser.add_argument('goal_id', help='Goal ID to resume')
    goals_resume_parser.add_argument('--ai-id', default='empirica_cli', help='Your AI identifier')
    goals_resume_parser.add_argument('--output', choices=['human', 'json'], default='human', help='Output format')
    goals_resume_parser.add_argument('--verbose', action='store_true', help='Show detailed operation info')

    # Goals-claim command (NEW: Phase 3a - Git Bridge)
    goals_claim_parser = subparsers.add_parser('goals-claim', help='Claim goal, create git branch, link to BEADS')
    goals_claim_parser.add_argument('--goal-id', required=True, help='Goal UUID to claim')
    goals_claim_parser.add_argument('--create-branch', action='store_true', default=True, help='Create git branch (default: True)')
    goals_claim_parser.add_argument('--no-branch', dest='create_branch', action='store_false', help='Skip branch creation')
    goals_claim_parser.add_argument('--run-preflight', action='store_true', help='Run PREFLIGHT after claiming')
    goals_claim_parser.add_argument('--output', choices=['human', 'json'], default='human', help='Output format')
    goals_claim_parser.add_argument('--verbose', action='store_true', help='Show detailed operation info')

    # Goals-complete command (NEW: Phase 3a - Git Bridge)
    goals_complete_parser = subparsers.add_parser('goals-complete', help='Complete goal, merge branch, close BEADS issue')
    goals_complete_parser.add_argument('--goal-id', required=True, help='Goal UUID to complete')
    goals_complete_parser.add_argument('--run-postflight', action='store_true', help='Run POSTFLIGHT before completing')
    goals_complete_parser.add_argument('--merge-branch', action='store_true', help='Merge git branch to main')
    goals_complete_parser.add_argument('--delete-branch', action='store_true', help='Delete branch after merge')
    goals_complete_parser.add_argument('--create-handoff', action='store_true', help='Create handoff report')
    goals_complete_parser.add_argument('--reason', default='completed', help='Completion reason (for BEADS)')
    goals_complete_parser.add_argument('--output', choices=['human', 'json'], default='human', help='Output format')
    goals_complete_parser.add_argument('--verbose', action='store_true', help='Show detailed operation info')

    # Identity commands (NEW: Phase 2 - Cryptographic Trust / EEP-1)
    identity_create_parser = subparsers.add_parser('identity-create', help='Create new AI identity with Ed25519 keypair')
    identity_create_parser.add_argument('--ai-id', required=True, help='AI identifier')
    identity_create_parser.add_argument('--overwrite', action='store_true', help='Overwrite existing identity')
    identity_create_parser.add_argument('--output', choices=['human', 'json'], default='human', help='Output format')
    identity_create_parser.add_argument('--verbose', action='store_true', help='Show detailed operation info')

    identity_list_parser = subparsers.add_parser('identity-list', help='List all AI identities')
    identity_list_parser.add_argument('--output', choices=['human', 'json'], default='human', help='Output format')
    
    identity_export_parser = subparsers.add_parser('identity-export', help='Export public key for sharing')
    identity_export_parser.add_argument('--ai-id', required=True, help='AI identifier')
    identity_export_parser.add_argument('--output', choices=['human', 'json'], default='human', help='Output format')
    
    identity_verify_parser = subparsers.add_parser('identity-verify', help='Verify signed session')
    identity_verify_parser.add_argument('session_id', help='Session ID to verify')
    identity_verify_parser.add_argument('--output', choices=['human', 'json'], default='human', help='Output format')
    identity_verify_parser.add_argument('--verbose', action='store_true', help='Show detailed operation info')

    # Sessions resume command
    sessions_resume_parser = subparsers.add_parser('sessions-resume', help='Resume previous sessions')
    sessions_resume_parser.add_argument('--ai-id', help='Filter by AI ID')
    sessions_resume_parser.add_argument('--count', type=int, default=1, help='Number of sessions to retrieve')
    sessions_resume_parser.add_argument('--detail-level', choices=['summary', 'detailed', 'full'], default='summary', help='Detail level')
    sessions_resume_parser.add_argument('--output', choices=['human', 'json'], default='human', help='Output format')
    sessions_resume_parser.add_argument('--verbose', action='store_true', help='Show detailed operation info')

    # Session create command (AI-first with config file support)
    session_create_parser = subparsers.add_parser('session-create',
        help='Create new session (AI-first: use config file, Legacy: use flags)')

    # AI-FIRST: Positional config file argument
    session_create_parser.add_argument('config', nargs='?',
        help='JSON config file path or "-" for stdin (AI-first mode)')

    # LEGACY: Flag-based arguments (backward compatible)
    session_create_parser.add_argument('--ai-id', help='AI agent identifier (legacy)')
    session_create_parser.add_argument('--user-id', help='User identifier (legacy)')
    session_create_parser.add_argument('--project-id', help='Project UUID to link session to (optional, auto-detected from git remote if omitted)')
    session_create_parser.add_argument('--subject', help='Subject/workstream identifier (auto-detected from directory if omitted)')
    session_create_parser.add_argument('--output', choices=['human', 'json'], default='json', help='Output format (default: json for AI)')
    session_create_parser.add_argument('--verbose', action='store_true', help='Show detailed operation info')


