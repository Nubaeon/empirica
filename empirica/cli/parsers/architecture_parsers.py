"""
Architecture Assessment Parsers

CLI argument parsers for epistemic architecture assessment commands.
"""


def add_architecture_parsers(subparsers):
    """Add architecture assessment command parsers."""

    # assess-component command
    assess_parser = subparsers.add_parser(
        'assess-component',
        help='Assess epistemic health of a code component',
        description='Applies Empirica epistemic vectors to analyze code component health, '
                    'coupling, stability, and risk.'
    )
    assess_parser.add_argument(
        'path',
        help='Path to file or package to assess (relative or absolute)'
    )
    assess_parser.add_argument(
        '--project-root',
        default='.',
        help='Root directory of the project (default: current directory)'
    )
    assess_parser.add_argument(
        '--output',
        choices=['text', 'json', 'summary'],
        default='text',
        help='Output format (default: text)'
    )

    # assess-compare command
    compare_parser = subparsers.add_parser(
        'assess-compare',
        help='Compare epistemic health of two components',
        description='Compare two code components side by side to identify which is healthier.'
    )
    compare_parser.add_argument(
        'path_a',
        help='First component path'
    )
    compare_parser.add_argument(
        'path_b',
        help='Second component path'
    )
    compare_parser.add_argument(
        '--project-root',
        default='.',
        help='Root directory of the project (default: current directory)'
    )
    compare_parser.add_argument(
        '--output',
        choices=['text', 'json'],
        default='text',
        help='Output format (default: text)'
    )

    # assess-directory command
    dir_parser = subparsers.add_parser(
        'assess-directory',
        help='Assess all Python modules in a directory',
        description='Recursively assess all Python files in a directory and rank by health.'
    )
    dir_parser.add_argument(
        'path',
        help='Directory to assess'
    )
    dir_parser.add_argument(
        '--project-root',
        default='.',
        help='Root directory of the project (default: current directory)'
    )
    dir_parser.add_argument(
        '--output',
        choices=['text', 'json'],
        default='text',
        help='Output format (default: text)'
    )
    dir_parser.add_argument(
        '--top',
        type=int,
        default=10,
        help='Show top N worst components (default: 10)'
    )
