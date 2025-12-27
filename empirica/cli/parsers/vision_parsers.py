"""Vision command parsers."""


def add_vision_parsers(subparsers):
    """Add vision command parsers"""
    # Vision command
    vision_parser = subparsers.add_parser('vision', help='Process visual information')
    vision_parser.add_argument('image_path', help='Path to image file')
    vision_parser.add_argument('--output', choices=['human', 'json'], default='human', help='Output format')
