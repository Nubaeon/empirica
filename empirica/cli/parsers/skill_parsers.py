"""Skill management command parsers."""


def add_skill_parsers(subparsers):
    """Add skill management command parsers"""
    # Skill suggest command
    skill_suggest_parser = subparsers.add_parser('skill-suggest', help='Suggest skills for a task')
    skill_suggest_parser.add_argument('--task', help='Task description to suggest skills for')
    skill_suggest_parser.add_argument('--project-id', help='Project ID for context-aware suggestions')
    skill_suggest_parser.add_argument('--output', choices=['human', 'json'], default='json', help='Output format')
    skill_suggest_parser.add_argument('--verbose', action='store_true', help='Show detailed suggestions')

    # Skill fetch command
    skill_fetch_parser = subparsers.add_parser('skill-fetch', help='Fetch and normalize a skill')
    skill_fetch_parser.add_argument('--name', required=True, help='Skill name')
    skill_fetch_parser.add_argument('--url', help='URL to fetch skill from (markdown)')
    skill_fetch_parser.add_argument('--file', help='Local .skill archive file to load')
    skill_fetch_parser.add_argument('--tags', help='Comma-separated tags for the skill')
    skill_fetch_parser.add_argument('--output', choices=['human', 'json'], default='json', help='Output format')
    skill_fetch_parser.add_argument('--verbose', action='store_true', help='Show detailed output')

    # Skill extract command - extract decision frameworks from skill to YAML
    skill_extract_parser = subparsers.add_parser(
        'skill-extract',
        help='Extract decision frameworks from skill to meta-agent-config.yaml'
    )
    skill_extract_parser.add_argument(
        '--skill-dir',
        help='Path to skill directory (with SKILL.md and/or references/)'
    )
    skill_extract_parser.add_argument(
        '--skills-dir',
        help='Path to directory containing multiple skills (extracts all)'
    )
    skill_extract_parser.add_argument(
        '--output-file',
        default='meta-agent-config.yaml',
        help='Output YAML file path (default: meta-agent-config.yaml)'
    )
    skill_extract_parser.add_argument(
        '--output', choices=['human', 'json'], default='json',
        help='Output format'
    )
    skill_extract_parser.add_argument(
        '--verbose', action='store_true',
        help='Show detailed extraction progress'
    )
