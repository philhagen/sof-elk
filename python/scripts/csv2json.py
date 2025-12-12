#!/usr/bin/env python3
# SOF-ELK® Supporting script
# (C)2025 Lewes Technology Consulting, LLC
#
# This script will read a CSV file, use the first line as headers, then convert each row of data
#   to JSON and add the JSON object to an output file.  Field types (null, boolean, integer, float,
#   and string) are preserved, and fields consisting of empty strings will be removed from the JSON.
#   Field names will be normalized by lowercasing them, replacing spaces with underscores, and
#   removing any characters except [a-z1-9_-]

import csv
import json
import argparse
import re
import sys


def normalize_field_name(name):
    """Normalize field name by removing special characters, replacing spaces with underscores, and lowercasing."""
    fieldname = name.replace(" ", "_")
    fieldname = re.sub(r"[^a-zA-Z0-9\-_]", "", fieldname)
    return fieldname.lower()


def convert_value(value):
    """Convert string value to appropriate data type."""
    if value is None:
        return None
    elif value.lower() == "false":
        return False
    elif value.lower() == "true":
        return True
    else:
        try:
            return int(value)
        except ValueError:
            pass

        try:
            return float(value)
        except ValueError:
            pass

        return value


def remove_empty_fields(obj):
    """Recursively traverse a JSON object and remove fields equal to an empty string."""
    if isinstance(obj, dict):
        return {
            key: remove_empty_fields(value) for key, value in obj.items() if value != ""
        }
    elif isinstance(obj, list):
        return [
            remove_empty_fields(item) for item in obj if item is not None and item != ""
        ]
    else:
        return obj


def process_csv_to_json(csv_filename, json_filename, tags):
    """Convert CSV file to JSON."""
    try:
        with open(csv_filename, "r") as csvfile, open(json_filename, "w") as jsonfile:
            field_name_translate = str.maketrans({"(": None, ")": None, " ": "_"})

            reader = csv.DictReader(csvfile)
            for row in reader:
                newrow = {
                    normalize_field_name(k): convert_value(v) for k, v in row.items()
                }
                newrow = remove_empty_fields(newrow)

                if tags != None:
                    if "tags" in newrow:
                        # just split on spaces for now - will adjust in future if data requires it
                        newrow["tags"] = newrow["tags"].split(" ")
                    else:
                        newrow["tags"] = []

                    for tag in tags:
                        newrow["tags"].append(tag)

                json.dump(newrow, jsonfile)
                jsonfile.write("\n")

    except FileNotFoundError:
        sys.stderr.write(f"ERROR: File '{csv_filename}' not found.\n")
        sys.exit(1)
    except Exception as e:
        sys.stderr.write(f"ERROR: An unexpected error occurred: {e}.\n")
        sys.exit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Convert CSV file to JSON.")
    parser.add_argument(
        "-r", "--read", dest="infile", help="CSV input file to process", required=True
    )
    parser.add_argument(
        "-w",
        "--write",
        dest="outfile",
        help="JSON output file to create",
        required=True,
    )
    parser.add_argument(
        "-t",
        "--tag",
        dest="tags",
        help='Optional string to add to "tags" field - can be used multiple times',
        action="append",
    )
    args = parser.parse_args()

    process_csv_to_json(args.infile, args.outfile, args.tags)
