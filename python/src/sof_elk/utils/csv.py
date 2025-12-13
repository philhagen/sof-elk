import argparse
import csv
import json
import re
import sys
from typing import Any


class CSVConverter:
    """
    Utilities for converting CSV to JSON.
    """

    @staticmethod
    def normalize_field_name(name: str) -> str:
        """Normalize field name by removing special characters, replacing spaces with underscores, and lowercasing."""
        fieldname = name.replace(" ", "_")
        fieldname = re.sub(r"[^a-zA-Z0-9\-_]", "", fieldname)
        return fieldname.lower()

    @staticmethod
    def convert_value(value: str | None) -> Any:
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

    @classmethod
    def remove_empty_fields(cls, obj: Any) -> Any:
        """Recursively traverse a JSON object and remove fields equal to an empty string."""
        if isinstance(obj, dict):
            return {key: cls.remove_empty_fields(value) for key, value in obj.items() if value != ""}
        elif isinstance(obj, list):
            return [cls.remove_empty_fields(item) for item in obj if item is not None and item != ""]
        else:
            return obj

    @classmethod
    def process_csv_to_json(cls, csv_filename: str, json_filename: str, tags: str | list[str] | None = None) -> bool:
        """Convert CSV file to JSON."""
        try:
            with open(csv_filename) as csvfile, open(json_filename, "w") as jsonfile:
                # field_name_translate = str.maketrans({"(": None, ")": None, " ": "_"}) # Unused in original script logic actually, though defined

                reader = csv.DictReader(csvfile)
                for row in reader:
                    newrow = {cls.normalize_field_name(k): cls.convert_value(v) for k, v in row.items()}
                    newrow = cls.remove_empty_fields(newrow)

                    if tags:
                        if "tags" in newrow:
                            # just split on spaces for now - will adjust in future if data requires it
                            newrow["tags"] = str(newrow["tags"]).split(" ")
                        else:
                            newrow["tags"] = []

                        if isinstance(tags, list):
                            for tag in tags:
                                newrow["tags"].append(tag)
                        else:
                            newrow["tags"].append(tags)

                    json.dump(newrow, jsonfile)
                    jsonfile.write("\n")
            return True

        except FileNotFoundError:
            sys.stderr.write(f"ERROR: File '{csv_filename}' not found.\n")
            return False
            # sys.exit(1) # Don't exit in library code
        except Exception as e:
            sys.stderr.write(f"ERROR: An unexpected error occurred: {e}.\n")
            return False
            # sys.exit(1)


def main(args: argparse.Namespace | None = None) -> None:
    """
    Main entry point for the CSV to JSON conversion utility.

    Args:
        args: Optional pre-parsed arguments. If None, arguments are parsed from sys.argv.
    """
    if args is None:
        parser = argparse.ArgumentParser(description="Convert CSV file to JSON.")
        parser.add_argument("-r", "--read", dest="infile", help="CSV input file to process", required=True)
        parser.add_argument(
            "-w",
            "--write",
            "--output",  # added alias
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
        parsed_args = parser.parse_args()
    else:
        parsed_args = args

    CSVConverter.process_csv_to_json(parsed_args.infile, parsed_args.outfile, parsed_args.tags)


if __name__ == "__main__":
    main()
