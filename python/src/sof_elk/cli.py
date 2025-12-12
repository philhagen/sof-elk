#!/usr/bin/env python3
# SOF-ELK® Main Entry Point
# (C)2025 Lewes Technology Consulting, LLC
#
# This script serves as the central entry point for python-based SOF-ELK utilities.

import argparse
import sys
import os
from typing import Optional, Any
from types import ModuleType

# Ensure the local package is actionable
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="SOF-ELK® Python Utilities CLI"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    subparsers.required = True

    # If no arguments provided, show help
    if len(sys.argv) == 1:
        parser.print_help(sys.stderr)
        sys.exit(1)

    args = parser.parse_args()

    if hasattr(args, 'func'):
        args.func(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()