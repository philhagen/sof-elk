import argparse
import json
import os
import sys

from .cloudtrail import CloudTrailProcessor
from .common import AWSCommon
from .vpcflow import VPCFlowProcessor

DEFAULT_DESTDIR_AWS = os.path.join(os.sep, "logstash", "aws")
DEFAULT_DESTDIR_NFARCH = os.path.join(os.sep, "logstash", "nfarch")


def register_subcommand(parser: argparse.ArgumentParser) -> None:
    """
    Register AWS subcommands (cloudtrail, vpcflow) to the provided parser.
    """
    aws_subparsers = parser.add_subparsers(dest="aws_command", help="AWS specific commands")
    aws_subparsers.required = True

    # CloudTrail Subcommand
    ct_parser = aws_subparsers.add_parser("cloudtrail", help="Process AWS CloudTrail logs")
    ct_parser.add_argument(
        "-r", "--read", dest="input", required=True, help="AWS CloudTrail log file or directory to read."
    )
    ct_parser.add_argument(
        "-o",
        "--output",
        dest="outdir",
        help='Base directory to store processed daily output files (default: "processed-logs-json").',
    )
    ct_parser.add_argument(
        "-f",
        "--force",
        dest="force_outfile",
        action="store_true",
        default=False,
        help=f"Force creating output in location other than default {DEFAULT_DESTDIR_AWS}",
    )
    ct_parser.add_argument(
        "-a",
        "--append",
        dest="append",
        action="store_true",
        default=False,
        help="Append to the output file if it exists.",
    )
    ct_parser.add_argument(
        "--reduce-noise", dest="reduce_noise", action="store_true", default=False, help="Filter out noisy events."
    )
    ct_parser.add_argument(
        "-v", "--verbose", dest="verbose", action="store_true", help="Display progress and status information."
    )
    ct_parser.set_defaults(func=handle_cloudtrail)

    # VPCFlow Subcommand
    vf_parser = aws_subparsers.add_parser("vpcflow", help="Process AWS VPC Flow logs")
    vf_parser.add_argument("-r", "--read", dest="input", required=True, help="VPC Flow log file or directory to read.")
    vf_parser.add_argument(
        "-w", "--write", dest="outfile", required=True, help="Destination file to write parsed logs to."
    )
    vf_parser.add_argument(
        "-v", "--verbose", dest="verbose", action="store_true", help="Display progress and status information."
    )
    vf_parser.set_defaults(func=handle_vpcflow)

    # Kick Subcommand
    kick_parser = aws_subparsers.add_parser(
        "kick", help="Append newline to JSON files if missing (fixes CloudTrail issues)"
    )
    kick_parser.add_argument(
        "-t",
        "--target",
        dest="target",
        default=DEFAULT_DESTDIR_AWS,
        help=f"Target directory to scan (default: {DEFAULT_DESTDIR_AWS})",
    )
    kick_parser.add_argument(
        "-v", "--verbose", dest="verbose", action="store_true", help="Display progress and status information."
    )
    kick_parser.set_defaults(func=handle_kick)


def handle_cloudtrail(args: argparse.Namespace) -> None:
    args.input = os.path.expanduser(args.input)
    if args.outdir:
        args.outdir = os.path.expanduser(args.outdir)

    # Validation
    if args.outdir and not args.outdir.startswith(DEFAULT_DESTDIR_AWS) and not args.force_outfile:
        sys.stderr.write(f'ERROR: Output location is not in {DEFAULT_DESTDIR_AWS}. Use "-f" to force.\n')
        sys.exit(2)

    if args.outdir and os.path.exists(args.outdir) and args.outdir != DEFAULT_DESTDIR_AWS and not args.append:
        sys.stderr.write(f'ERROR: Output directory {args.outdir} already exists. Use "-a" to append.\n')
        sys.exit(3)

    input_files = AWSCommon.get_input_files(args.input)
    if not input_files:
        sys.stderr.write("No input files could be processed. Exiting.\n")
        sys.exit(4)

    if args.verbose:
        print(f"Found {len(input_files)} files to parse.")

    for idx, infile in enumerate(input_files, 1):
        if args.verbose:
            print(f"- Parsing file: {infile} ({idx} of {len(input_files)})")

        records = CloudTrailProcessor.process_file(infile, reduce_noise=args.reduce_noise)
        output_file = CloudTrailProcessor.derive_output_file(infile)

        if args.outdir is None:
            output_path = os.path.join(DEFAULT_DESTDIR_AWS, output_file)
        else:
            output_path = os.path.join(args.outdir, output_file)

        output_dir = os.path.dirname(output_path)
        if not os.path.exists(output_dir):
            try:
                os.makedirs(output_dir)
            except OSError:
                pass

        with open(output_path, "a") as outfh:
            for record in records:
                outfh.write(f"{json.dumps(record)}\n")

    if args.outdir and not args.outdir.startswith(DEFAULT_DESTDIR_AWS):
        print(f"Output complete. Move to {DEFAULT_DESTDIR_AWS} for processing.")
    else:
        print("SOF-ELK should now be processing the generated file.")


def handle_vpcflow(args: argparse.Namespace) -> None:
    args.input = os.path.expanduser(args.input)
    args.outfile = os.path.expanduser(args.outfile)

    output_dir = os.path.dirname(args.outfile)
    if not output_dir.startswith(DEFAULT_DESTDIR_NFARCH):
        if not args.outfile.startswith(DEFAULT_DESTDIR_NFARCH):
            sys.stderr.write(f"WARNING: Output file location {args.outfile} is not in {DEFAULT_DESTDIR_NFARCH}.\n")

    if not os.path.exists(output_dir):
        sys.stderr.write(f"ERROR: Parent path {output_dir} does not exist. Exiting.\n")
        sys.exit(8)

    input_files = AWSCommon.get_input_files(args.input)
    if not input_files:
        sys.stderr.write("No input files could be processed. Exiting.\n")
        sys.exit(6)

    success_count = 0
    try:
        with open(args.outfile, "a") as outfh:
            for idx, infile in enumerate(input_files, 1):
                if args.verbose:
                    print(f"- Parsing file: {infile} ({idx} of {len(input_files)})")

                messages = VPCFlowProcessor.process_file(infile)
                if messages:
                    for msg in messages:
                        outfh.write(f"{msg}\n")
                    success_count += 1
                else:
                    if args.verbose:
                        print(f"  No valid messages found in {infile}")

    except Exception as e:
        sys.stderr.write(f"Error writing to {args.outfile}: {e}\n")
        sys.exit(1)

    if success_count > 0:
        print("Output complete.")
        if not args.outfile.startswith(DEFAULT_DESTDIR_NFARCH):
            print(f"You must move/copy {args.outfile} to {DEFAULT_DESTDIR_NFARCH} for processing.")
        else:
            print("SOF-ELK should now be processing the generated file.")
    else:
        print("No files were successfully converted.")


def handle_kick(args: argparse.Namespace) -> None:
    args.target = os.path.expanduser(args.target)

    if not os.path.exists(args.target):
        sys.stderr.write(f"ERROR: Target path {args.target} does not exist.\n")
        sys.exit(1)

    # Use existing get_input_files, which recurses directory
    files = AWSCommon.get_input_files(args.target)

    count = 0
    fixed = 0

    for infile in files:
        # Check extensions? Script says *.json, but find logic was broad in some contexts.
        # Original: find /logstash/aws/ -type f ...
        # But commonly we only care about json logs. Let's process everything to match original "find -type f" behavior
        # unless it is obviously binary? Original logic: "tail -c 1 ... && echo >> ..."
        # It's safer to stick to text files or just do what the script did.
        # The script does it to EVERYTHING in /logstash/aws/

        count += 1
        if AWSCommon.ensure_file_ends_with_newline(infile):
            fixed += 1
            if args.verbose:
                print(f"Fixed: {infile}")
        elif args.verbose:
            # Too noisy to print every skipped file?
            pass

    if args.verbose:
        print(f"Scanned {count} files. Appended newline to {fixed} files.")
