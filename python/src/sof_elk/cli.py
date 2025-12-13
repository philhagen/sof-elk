#!/usr/bin/env python3
# SOF-ELK® Main Entry Point
# (C)2025 Lewes Technology Consulting, LLC

"""
SOF-ELK® CLI Utility
====================

This module serves as the central entry point for all Python-based SOF-ELK® utilities.
It dynamically imports available submodules (management, utils, libs) and registers
their respective subcommands with the main argument parser.

Usage:
    python3 -m sof_elk.cli [command] [subcommand] [args]

Example:
    python3 -m sof_elk.cli management clear --index syslog
"""

import argparse
import os
import sys
from types import ModuleType

# Ensure the local package is actionable
# current_dir = os.path.dirname(os.path.abspath(__file__))
# if current_dir not in sys.path:
#     sys.path.insert(0, current_dir)

# Import submodules
from .aws import cli as aws_cli
from .management import cli as mgmt_cli
from .azure import cli as azure_cli
from .geoip import cli as geoip_cli
from .gcp import cli as gcp_cli

utils_csv: ModuleType | None
try:
    from .utils import csv as utils_csv  # special case, direct module
except ImportError:
    utils_csv = None

utils_firewall: ModuleType | None
try:
    from .utils import firewall as utils_firewall
except ImportError:
    utils_firewall = None

utils_nfdump: ModuleType | None
try:
    from .utils import nfdump as utils_nfdump
except ImportError:
    utils_nfdump = None

utils_system: ModuleType | None
try:
    from .utils import system as utils_system
except ImportError:
    utils_system = None

utils_login: ModuleType | None
try:
    from .utils import login as utils_login
except ImportError:
    utils_login = None

ecs_lib: ModuleType | None
try:
    from .lib import ecs as ecs_lib
except ImportError:
    ecs_lib = None


def main() -> None:
    """
    Main entry point for the CLI.

    Initializes the argument parser and registers subcommands from available modules.
    """
    parser = argparse.ArgumentParser(description="SOF-ELK® Python Utilities CLI")

    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    subparsers.required = True

    # Register AWS commands
    aws_parser = subparsers.add_parser("aws", help="AWS Utilities")
    aws_cli.register_subcommand(aws_parser)

    # Register Management commands
    mgmt_cli.register_subcommand(subparsers)

    # Register Azure commands
    azure_cli.register_subcommand(subparsers)

    # Register GeoIP commands
    geoip_cli.register_subcommand(subparsers)

    # Register GCP commands
    gcp_cli.register_subcommand(subparsers)

    # Register ECS Generation command
    if ecs_lib:
        ecs_parser = subparsers.add_parser("ecs-gen", help="Generate ECS Fields CSV")
        ecs_parser.add_argument("-o", "--output", dest="outfile", required=True, help="Output CSV file")
        ecs_parser.set_defaults(func=lambda args: ecs_lib.generate_csv(args.outfile) if ecs_lib else None)

    # Register Utils
    # Check if ANY utils module is present to ensure the parser is created
    if any([utils_csv, utils_firewall, utils_nfdump, utils_system, utils_login]):
        utils_parser = subparsers.add_parser("utils", help="General Utilities")
        utils_sub = utils_parser.add_subparsers(dest="utils_command", required=True)

        # Register CSV if available
        if utils_csv:
            csv_parser = utils_sub.add_parser("csv2json", help="Convert CSV to JSON")
            csv_parser.add_argument("-r", "--read", dest="infile", required=True, help="Input CSV")
            csv_parser.add_argument("-w", "--write", "--output", dest="outfile", required=True, help="Output JSON")
            csv_parser.add_argument("-t", "--tag", dest="tags", action="append", help="Tags")
            csv_parser.set_defaults(
                func=lambda args: utils_csv.CSVConverter.process_csv_to_json(args.infile, args.outfile, args.tags)
                if utils_csv
                else None
            )

        if utils_firewall:
            utils_firewall.register_subcommand(utils_sub)

        if utils_nfdump:
            utils_nfdump.register_subcommand(utils_sub)

        if utils_system:
            utils_system.register_subcommand(utils_sub)

        if utils_login:
            utils_login.register_subcommand(utils_sub)

    # If no arguments provided, show help
    if len(sys.argv) == 1:
        parser.print_help(sys.stderr)
        sys.exit(1)

    args = parser.parse_args()

    if hasattr(args, "func"):
        args.func(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
