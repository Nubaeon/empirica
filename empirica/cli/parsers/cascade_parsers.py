"""CASCADE workflow command parsers."""

def add_cascade_parsers(subparsers):
    """Add cascade command parsers (Primary CLI interface for epistemic assessments)

    The CASCADE workflow commands are the primary interface for AI-based epistemic assessments.
    MCP tools route to these CLI commands:
    - preflight-submit: Submit preflight assessment vectors
    - check / check-submit: Execute/submit check assessment
    - postflight-submit: Submit postflight assessment vectors

    This function provides the core CLI interface for epistemic self-assessment.
    """
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


