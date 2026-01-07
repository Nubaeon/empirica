"""Onboarding command parsers."""


def add_onboarding_parsers(subparsers):
    """Add onboarding command parsers"""
    # Onboard command - interactive introduction to Empirica
    onboard_parser = subparsers.add_parser(
        'onboard',
        help='Interactive introduction to Empirica (recommended for first-time users)'
    )
    onboard_parser.add_argument(
        '--ai-id',
        default='claude-code',
        help='AI identifier (optional, default: claude-code)'
    )
