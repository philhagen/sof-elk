import argparse

from .flow import AzureFlowProcessor
from typing import Any

def register_subcommand(subparsers: Any) -> None:
    parser = subparsers.add_parser("azure", help="Azure log processing utilities")
    sub_subparsers = parser.add_subparsers(dest="azure_command", required=True)

    flow_parser = sub_subparsers.add_parser("flow", help="Process Azure Flow logs")
    flow_parser.add_argument("-r", "--read", dest="infile", required=True, help="Azure Flow log file or directory")
    flow_parser.add_argument("-w", "--write", "--output", dest="outfile", required=True, help="Output file")
    flow_parser.add_argument("-f", "--force", dest="force", action="store_true", help="Force output location")
    flow_parser.add_argument("-a", "--append", dest="append", action="store_true", help="Append to output file")
    flow_parser.add_argument("-v", "--verbose", dest="verbose", action="store_true", help="Verbose output")
    flow_parser.set_defaults(func=flow_command)

def flow_command(args: argparse.Namespace) -> None:
    processor = AzureFlowProcessor(
        infile=args.infile,
        outfile=args.outfile,
        append=args.append,
        force=args.force,
        verbose=args.verbose
    )
    processor.run()
