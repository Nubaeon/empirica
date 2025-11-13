#!/usr/bin/env python3
"""
Empirica CLI - Main entry point

This module serves as the entry point when running: python -m empirica.cli
It delegates to cli_core.main() which contains the full command routing logic.
"""

import sys
from .cli_core import main

if __name__ == '__main__':
    sys.exit(main())
