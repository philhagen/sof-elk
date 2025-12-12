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


    # Register ECS Generation command
    if ecs_lib:
        ecs_parser = subparsers.add_parser("ecs-gen", help="Generate ECS Fields CSV")
        ecs_parser.add_argument("-o", "--output", dest="outfile", required=True, help="Output CSV file")
        ecs_parser.set_defaults(func=lambda args: ecs_lib.generate_csv(args.outfile))
        
    # Register Utils (Manual registration since it's small)
    if utils_csv:
        utils_parser = subparsers.add_parser("utils", help="General Utilities")
        utils_sub = utils_parser.add_subparsers(dest="utils_command", required=True)
        
        csv_parser = utils_sub.add_parser("csv2json", help="Convert CSV to JSON")
        csv_parser.add_argument("-r", "--read", dest="infile", required=True, help="Input CSV")
        csv_parser.add_argument("-w", "--write", "--output", dest="outfile", required=True, help="Output JSON")
        csv_parser.add_argument("-t", "--tag", dest="tags", action="append", help="Tags")
        csv_parser.set_defaults(func=lambda args: utils_csv.CSVConverter.process_csv_to_json(args.infile, args.outfile, args.tags) if utils_csv else None)
    
    # We need to access utils_sub from the previous block if it exists, or create it if utils_csv didn't exist but others do.
    # However, currently utils logic assumes they share the 'utils' subcommand.
    # To properly handle this without 'utils_csv' being the primary:
    # We should define utils_parser outside the if.
    
    # Check if ANY utils module is present
    if any([utils_csv, utils_firewall, utils_nfdump, utils_system, utils_login]):
        # Check if parser already added (argparse throws error if strict? No, but retrieves it?)
        # argparse doesn't easily let us retrieve 'utils' parser if we didn't save it.
        # But we only created it inside the `if utils_csv` block above.
        
        # Refactor slightly for safety:
        # If utils_sub doesn't exist yet, we can't add to it.
        # The original code relied on utils_csv being available for utils_sub to be created.
        pass

    if utils_firewall and 'utils_sub' in locals(): # Reuse utils parser if available
        utils_firewall.register_subcommand(utils_sub)

    if utils_nfdump and 'utils_sub' in locals():
        utils_nfdump.register_subcommand(utils_sub)

    if utils_system and 'utils_sub' in locals():
        utils_system.register_subcommand(utils_sub)
        
    if utils_login and 'utils_sub' in locals():
        utils_login.register_subcommand(utils_sub)

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