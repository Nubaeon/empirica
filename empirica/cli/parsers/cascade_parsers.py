"""CASCADE workflow command parsers."""

def add_cascade_parsers(subparsers):
    """Add cascade command parsers (Primary CLI interface for epistemic assessments)

    The CASCADE workflow commands are the primary interface for AI-based epistemic assessments.
    MCP tools are available as GUI/IDE interfaces that map to these CLI commands:
    - MCP execute-preflight maps to CLI preflight command
    - MCP execute-check maps to CLI check command
    - MCP execute-postflight maps to CLI postflight command

    This function provides the core CLI interface for epistemic self-assessment.
    """
    # Deprecated - CASCADE workflow now uses MCP tools
    pass
    
    # Enhanced decision analysis command with ModalitySwitcher
    # Preflight command
    preflight_parser = subparsers.add_parser('preflight', help='Execute preflight epistemic assessment')
    preflight_parser.add_argument('prompt', help='Task description to assess')
    preflight_parser.add_argument('--session-id', help='Optional session ID (auto-generated if not provided)')
    preflight_parser.add_argument('--ai-id', default='empirica_cli', help='AI identifier for session tracking')
    preflight_parser.add_argument('--no-git', action='store_true', help='Disable automatic git checkpoint creation')
    preflight_parser.add_argument('--sign', action='store_true', help='Sign assessment with AI keypair (Phase 2: EEP-1)')
    preflight_parser.add_argument('--prompt-only', action='store_true', help='Return ONLY the self-assessment prompt as JSON (no waiting, for genuine AI assessment)')
    preflight_parser.add_argument('--assessment-json', help='Genuine AI self-assessment JSON (required for genuine assessment)')
    preflight_parser.add_argument('--sentinel-assess', action='store_true', help='Route to Sentinel assessment system (future feature)')
    preflight_parser.add_argument('--json', action='store_const', const='json', dest='output_format', help='Output as JSON (deprecated, use --output json)')
    preflight_parser.add_argument('--output', choices=['human', 'json'], default='json', help='Output format (default: json for programmatic use; --output human for inspection)')
    preflight_parser.add_argument('--sentinel', action='store_true', help='Route to Sentinel for interactive decision-making (future: Sentinel assessment routing)')
    preflight_parser.add_argument('--compact', action='store_true', help='Output as single-line key=value (human format only)')
    preflight_parser.add_argument('--kv', action='store_true', help='Output as multi-line key=value (human format only)')
    preflight_parser.add_argument('--verbose', action='store_true', help='Show detailed assessment (human format only)')
    preflight_parser.add_argument('--quiet', action='store_true', help='Quiet mode (requires --assessment-json)')
    
    # Workflow command
    workflow_parser = subparsers.add_parser('workflow', help='Execute full preflight→work→postflight workflow')
    workflow_parser.add_argument('prompt', help='Task description')
    workflow_parser.add_argument('--auto', action='store_true', help='Skip manual pause between steps')
    workflow_parser.add_argument('--verbose', action='store_true', help='Show detailed workflow steps')

    # NEW: MCP v2 Workflow Commands (Critical Priority)
    
    # Preflight submit command (AI-first with config file support)
    preflight_submit_parser = subparsers.add_parser('preflight-submit',
        help='Submit preflight assessment (AI-first: use config file, Legacy: use flags)')

    # AI-FIRST: Positional config file argument
    preflight_submit_parser.add_argument('config', nargs='?',
        help='JSON config file path or "-" for stdin (AI-first mode)')

    # LEGACY: Flag-based arguments (backward compatible)
    preflight_submit_parser.add_argument('--session-id', help='Session ID (legacy)')
    preflight_submit_parser.add_argument('--vectors', help='Epistemic vectors as JSON string or dict (legacy)')
    preflight_submit_parser.add_argument('--reasoning', help='Reasoning for assessment scores (legacy)')
    preflight_submit_parser.add_argument('--output', choices=['human', 'json'], default='json', help='Output format (default: json for AI)')
    preflight_submit_parser.add_argument('--verbose', action='store_true', help='Show detailed operation info')
    
    # Check command (AI-first with config file support)
    check_parser = subparsers.add_parser('check',
        help='Execute epistemic check (AI-first: use config file, Legacy: use flags)')

    # AI-FIRST: Positional config file argument
    check_parser.add_argument('config', nargs='?',
        help='JSON config file path or "-" for stdin (AI-first mode)')

    # LEGACY: Flag-based arguments (backward compatible)
    check_parser.add_argument('--session-id', help='Session ID (legacy)')
    check_parser.add_argument('--findings', help='Investigation findings as JSON array (legacy)')
    # Create mutually exclusive group for unknowns (accept either name)
    unknowns_group = check_parser.add_mutually_exclusive_group(required=False)
    unknowns_group.add_argument('--unknowns', dest='unknowns', help='Remaining unknowns as JSON array (legacy)')
    unknowns_group.add_argument('--remaining-unknowns', dest='unknowns', help='Alias for --unknowns (legacy)')
    check_parser.add_argument('--confidence', type=float, help='Confidence score (0.0-1.0) (legacy)')
    check_parser.add_argument('--output', choices=['human', 'json'], default='json', help='Output format (default: json for AI)')
    check_parser.add_argument('--verbose', action='store_true', help='Show detailed analysis')
    
    # Check submit command (AI-first with config file support)
    check_submit_parser = subparsers.add_parser('check-submit', 
        help='Submit check assessment (AI-first: use config file, Legacy: use flags)')
    
    # AI-FIRST: Positional config file argument
    check_submit_parser.add_argument('config', nargs='?',
        help='JSON config file path or "-" for stdin (AI-first mode)')
    
    # LEGACY: Flag-based arguments (backward compatible)
    check_submit_parser.add_argument('--session-id', help='Session ID (legacy)')
    check_submit_parser.add_argument('--vectors', help='Epistemic vectors as JSON string or dict (legacy)')
    check_submit_parser.add_argument('--decision', choices=['proceed', 'investigate', 'proceed_with_caution'], help='Decision made (legacy)')
    check_submit_parser.add_argument('--reasoning', help='Reasoning for decision (legacy)')
    check_submit_parser.add_argument('--cycle', type=int, help='Investigation cycle number (legacy)')
    check_submit_parser.add_argument('--round', type=int, help='Round number (for checkpoint tracking) (legacy)')
    check_submit_parser.add_argument('--output', choices=['human', 'json'], default='human', help='Output format')
    check_submit_parser.add_argument('--verbose', action='store_true', help='Show detailed operation info')
    
    # Postflight command (primary, non-blocking)
    postflight_parser = subparsers.add_parser('postflight', help='Submit postflight epistemic assessment results')
    postflight_parser.add_argument('--session-id', required=True, help='Session ID')
    postflight_parser.add_argument('--vectors', required=True, help='Epistemic vectors as JSON string or dict (reassessment of same 13 dimensions as preflight)')
    postflight_parser.add_argument('--reasoning', help='Task summary or description of learning/changes from preflight')
    postflight_parser.add_argument('--output', choices=['human', 'json'], default='human', help='Output format')
    postflight_parser.add_argument('--verbose', action='store_true', help='Show detailed operation info')

    # Postflight submit command (AI-first with config file support)
    postflight_submit_parser = subparsers.add_parser('postflight-submit',
        help='Submit postflight assessment (AI-first: use config file, Legacy: use flags)')

    # AI-FIRST: Positional config file argument
    postflight_submit_parser.add_argument('config', nargs='?',
        help='JSON config file path or "-" for stdin (AI-first mode)')

    # LEGACY: Flag-based arguments (backward compatible)
    postflight_submit_parser.add_argument('--session-id', help='Session ID (legacy)')
    postflight_submit_parser.add_argument('--vectors', help='Epistemic vectors as JSON string or dict (legacy)')
    postflight_submit_parser.add_argument('--reasoning', help='Description of what changed from preflight (legacy)')
    postflight_submit_parser.add_argument('--changes', help='Alias for --reasoning (deprecated, use --reasoning)', dest='reasoning')
    postflight_submit_parser.add_argument('--output', choices=['human', 'json'], default='json', help='Output format (default: json for AI)')
    postflight_submit_parser.add_argument('--verbose', action='store_true', help='Show detailed operation info')


