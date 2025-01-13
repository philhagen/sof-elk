#!/usr/bin/env python3
# SOF-ELK® Supporting script
# (C)2024 Lewes Technology Consulting, LLC
#
# This script will recursively read a file or directory tree of JSON AWS Cloudtrail logs and output in a format that SOF-ELK® can read.  Both gzipped and native JSON is supported.

import argparse
import gzip
import json
import os
import sys


from datetime import datetime
from collections import defaultdict


default_destdir = "/logstash/aws/"


def extract_date_from_filename(filepath):
    """
    Extract the date portion (YYYY-MM-DDT) from the full file path.
    Assumes the filename contains a date in the format YYYYMMDD, such as
    123456789012_CloudTrail_us-east-1_20250110T0805Z_Ba3uiALBNRSB1c4v.json.gz.
    """
    base_name = os.path.basename(filepath)
    try:
        # Look for the YYYYMMDD pattern in the filename
        for part in base_name.split("_"):
            if "T" in part and part[:8].isdigit():
                date_part = part[:8]  # Extract YYYYMMDD
                date_object = datetime.strptime(date_part, "%Y%m%d")
                return date_object.strftime("%Y-%m-%dT")
    except ValueError:
        sys.stderr.write(
            f"- ERROR: Could not extract date from filename {filepath}. Skipping file.\n"
        )
    return None


def process_cloudtrail_file(infile):
    """
    Process a CloudTrail log file and return its records.
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


def derive_output_dir(input_dir, infile):
    """
    Derive the output directory path based on the input directory structure.
    """
    daily_path = os.path.dirname(infile)
    relative_path = os.path.relpath(os.path.dirname(daily_path), input_dir)
    return os.path.join("processed-logs-json", relative_path)


parser = argparse.ArgumentParser(
    description="Process AWS CloudTrail logs into daily-based output files."
)
parser.add_argument(
    "-r",
    "--read",
    dest="infile",
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
    "-v",
    "--verbose",
    dest="verbose",
    action="store_true",
    help="Display progress and status information.",
)
args = parser.parse_args()


input_files = []
if os.path.isfile(args.infile):
    input_files.append(args.infile)
elif os.path.isdir(args.infile):
    for root, _, files in os.walk(args.infile):
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

    date_key = extract_date_from_filename(infile)
    if not date_key:
        continue

    records = process_cloudtrail_file(infile)

    output_dir = derive_output_dir(args.infile, infile)

    if args.outdir == None:
        output_dir = os.path.join(default_destdir, output_dir)
    else:
        output_dir = os.path.join(args.outdir, output_dir)

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    output_file = os.path.join(output_dir, f"cloudtrail_{date_key}.json")
    with open(output_file, "w") as outfh:
        for record in records:
            outfh.write(f"{json.dumps(record)}\n")

if args.verbose:
    print("Output complete. Daily JSON files have been created in the specified directory.")
