import gzip
import json
import os
import sys
from typing import Any, TextIO


class AWSCommon:
    """
    Common utilities for AWS log processing.
    """

    @staticmethod
    def get_input_files(input_path: str) -> list[str]:
        """
        recursively find files in a directory or return the file itself.
        """
        input_files: list[str] = []
        if os.path.isfile(input_path):
            input_files.append(input_path)
        elif os.path.isdir(input_path):
            for root, _, files in os.walk(input_path):
                for name in files:
                    input_files.append(os.path.join(root, name))
        return input_files

    @staticmethod
    def open_file_handle(infile: str) -> TextIO | None:
        """
        Open a file handle for reading, handling gzip if necessary.
        """
        try:
            if infile.endswith(".gz"):
                return gzip.open(infile, "rt")
            else:
                return open(infile)
        except OSError as e:
            sys.stderr.write(f"Error opening {infile}: {e}\n")
            return None

    @staticmethod
    def smart_open_json(infile: str) -> Any | None:
        """
        Open a file and return the JSON content.
        """
        try:
            handle = AWSCommon.open_file_handle(infile)
            if handle:
                with handle as f:
                    return json.load(f)
        except json.JSONDecodeError as e:
            sys.stderr.write(f"Error decoding JSON from {infile}: {e}\n")
        except Exception as e:
            sys.stderr.write(f"Error reading {infile}: {e}\n")
        return None

    @staticmethod
    def ensure_file_ends_with_newline(filepath: str) -> bool:
        """
        Check if the file ends with a newline character, and append one if not.
        Returns True if a newline was appended, False otherwise.
        """
        try:
            with open(filepath, "rb+") as f:
                try:
                    f.seek(-1, os.SEEK_END)
                except OSError:
                    # Empty file
                    return False

                last_char = f.read(1)
                if last_char != b"\n":
                    f.seek(0, os.SEEK_END)
                    f.write(b"\n")
                    return True
        except OSError as e:
            sys.stderr.write(f"Error checking/updating {filepath}: {e}\n")

        return False
