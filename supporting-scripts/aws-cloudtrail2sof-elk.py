#!/usr/bin/env python3
# SOF-ELK® Supporting script
# (C)2025 Lewes Technology Consulting, LLC
# Updated Jan 2025 by GH user @za to refactor into a date-hashed directory tree
#
# This script will recursively read a file or directory tree of JSON AWS
# Cloudtrail logs and output in a format that SOF-ELK® can read.  Both gzipped
# and native JSON is supported.
# Assumes the filename contains a date in the format YYYYMMDD, such as:
#  123456789012_CloudTrail_us-east-1_20250110T0805Z_Ba3uiALBNRSB1c4v.json.gz

import argparse
import gzip
import json
import os
import re
import sys


from datetime import datetime
from collections import defaultdict


default_destdir = os.path.join(os.sep, "logstash", "aws")

filename_regex_string = "(?P<account_id>\d{12})_CloudTrail_(?P<region_name>[A-Za-z0-9-]+)_(?P<year>\d{4})(?P<month>\d{2})(?P<day>\d{2})T(?P<time>\d{4})Z_.*"
filename_regex = re.compile(filename_regex_string)


def process_cloudtrail_file(infile):
    """
    Process a single CloudTrail log file and return its records.
    """
    records = []

    # Determine if this is a gzip file
    try:
        with gzip.open(infile, "rt") as input_file:
            rawjson = json.load(input_file)
    except OSError:
        with open(infile, "r") as input_file:
            rawjson = json.load(input_file)
    except json.decoder.JSONDecodeError:
        sys.stderr.write(
            f"- ERROR: Could not process JSON from {infile}. Skipping file.\n"
        )
        return records

    if "Records" not in rawjson:
        sys.stderr.write(
            f"- ERROR: Input file {infile} does not appear to contain AWS CloudTrail records. Skipping file.\n"
        )
        return records

    return rawjson["Records"]


def derive_output_file(infile):
    """
    Derive the output directory path based on the input directory structure.
    """

    filename = os.path.basename(infile)
    filename_match = filename_regex.match(filename)

    if filename_match:
        filename_parts = filename_match.groupdict()

        output_file = os.path.join(
            "processed-logs-json",
            filename_parts["account_id"],
            filename_parts["region_name"],
            filename_parts["year"],
            filename_parts["month"],
            f"cloudtrail_{filename_parts['year']}-{filename_parts['month']}-{filename_parts['day']}.json",
        )

    else:
        sys.stderr.write(
            f"WARNING: {infile} does not have a standard file naming structure. Placing records into undated output file.\n"
        )
        output_file = os.path.join("processed-logs-json", "cloudtrail_undated.json")

    return output_file


parser = argparse.ArgumentParser(
    description="Process AWS CloudTrail logs into daily-based output files."
)
parser.add_argument(
    "-r",
    "--read",
    dest="input",
    required=True,
    help="AWS CloudTrail log file or directory to read.",
)
parser.add_argument(
    "-o",
    "--output",
    dest="outdir",
    help='Base directory to store processed daily output files (default: "processed-logs-json").',
)
parser.add_argument(
    "-f",
    "--force",
    dest="force_outfile",
    help=f"Force creating an output file in a location other than the default SOF-ELK ingest location, {default_destdir}",
    default=False,
    action="store_true",
)
parser.add_argument(
    "-a",
    "--append",
    dest="append",
    help="Append to the output file if it exists.",
    default=False,
    action="store_true",
)
parser.add_argument(
    "-v",
    "--verbose",
    dest="verbose",
    action="store_true",
    help="Display progress and status information.",
)
args = parser.parse_args()
args.input = os.path.expanduser(args.input)
args.outdir = os.path.expanduser(args.outdir)

if not args.outdir.startswith(default_destdir) and not args.force_outfile:
    sys.stderr.write(
        f'ERROR: Output location is not in {default_destdir}, which is the SOF-ELK ingest location. Use "-f" to force creating a file in this location.\n'
    )
    sys.exit(2)

if (
    os.path.exists(args.outdir)
    and not (args.outdir == default_destdir)
    and not args.append
):
    sys.stderr.write(
        f'ERROR: Output directory {args.outdir} already exists.  Use "-a" to append to any existing output in this location.\n'
    )
    sys.exit(3)

input_files = []
if os.path.isfile(args.input):
    input_files.append(args.input)
elif os.path.isdir(args.input):
    for root, _, files in os.walk(args.input):
        for name in files:
            input_files.append(os.path.join(root, name))
else:
    sys.stderr.write("No input files could be processed. Exiting.\n")
    sys.exit(4)

if args.verbose:
    print(f"Found {len(input_files)} files to parse.")

for idx, infile in enumerate(input_files, 1):
    if args.verbose:
        print(f"- Parsing file: {infile} ({idx} of {len(input_files)})")

    records = process_cloudtrail_file(infile)

    output_file = derive_output_file(infile)

    if args.outdir == None:
        output_path = os.path.join(default_destdir, output_file)
    else:
        output_path = os.path.join(args.outdir, output_file)

    output_dir = os.path.dirname(output_path)

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    with open(output_path, "a") as outfh:
        for record in records:
            outfh.write(f"{json.dumps(record)}\n")

if not args.outdir.startswith(default_destdir):
    print(
        f"Output complete.  You must move/copy the generated file to the {default_destdir} directory before SOF-ELK can process it."
    )
else:
    print(
        "SOF-ELK should now be processing the generated file - check system load and the Kibana interface to confirm."
    )
