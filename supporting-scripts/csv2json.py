#!/usr/bin/env python3
# SOF-ELK® Supporting script
# (C)2026 Lewes Technology Consulting, LLC
#
# This script reads a CSV file, uses the first line as headers, then converts
# each row of data to JSON and writes one JSON object per line to an output
# file. Field types (null, boolean, integer, float, and string) are preserved;
# fields with empty strings are removed; field names are normalized by
# lowercasing them, replacing spaces with underscores, and removing any
# characters except [a-z0-9_-].
#
# Eric Zimmerman ("EZ") forensic tools support (Kape modules + standalone):
#   - UTF-8 with BOM (RECmd batch output, RegistryExplorer exports)
#   - UTF-16 LE/BE (PowerShell-redirected output: "RECmd ... > out.csv")
#   - Plain UTF-8 (most tools: PECmd, SBECmd, LECmd, MFTECmd, EvtxECmd,
#     JLECmd, AmcacheParser, AppCompatCacheParser, ...)
#   - Embedded NUL bytes from RegBinary values, $FILE_NAME bytes, and other
#     binary-derived fields (these break Python's stdlib csv reader otherwise)
#   - Very large single fields (PECmd FilesLoaded, RECmd ValueData on big
#     registry values) — csv.field_size_limit is raised to 10 MB.
#
# Usage:
#   csv2json.py -r INPUT.csv -w OUTPUT.json [-t TAG ...] [-e ENCODING]

import csv
import json
import argparse
import re
import sys

# EZ Tools sometimes pack 50+ KB into a single CSV field (PECmd FilesLoaded,
# RECmd ValueData on large registry values). Python's default field_size_limit
# is 128 KB on some platforms — raise to 10 MB for headroom.
csv.field_size_limit(10 * 1024 * 1024)


def detect_encoding(filename):
    """Sniff the first bytes of the file to determine encoding.

    Returns one of: 'utf-8-sig', 'utf-16', 'utf-8', or 'cp1252'. The 'utf-16'
    codec handles both BE (FE FF) and LE (FF FE) BOMs.

    cp1252 fallback: NirSoft tools (BrowsingHistoryView, etc.) and many other
    Windows utilities default to writing CSV in the system ANSI code page,
    which is cp1252 on en-US Windows installs. Without this fallback we'd
    read those files as utf-8 + errors='replace' and silently replace bytes
    like 0xA0 (non-breaking space in cp1252) with U+FFFD.
    """
    with open(filename, "rb") as f:
        head = f.read(4096)
    if head.startswith(b"\xef\xbb\xbf"):
        return "utf-8-sig"
    if head.startswith(b"\xff\xfe") or head.startswith(b"\xfe\xff"):
        return "utf-16"
    try:
        head.decode("utf-8")
        return "utf-8"
    except UnicodeDecodeError:
        # First chunk has bytes that aren't valid utf-8. cp1252 maps every
        # byte to *something*, so it always decodes — accept that as the
        # best guess for Windows-origin CSV.
        return "cp1252"


def strip_nuls(line_iterator):
    """Strip NUL bytes from each line.

    Embedded NUL bytes occur in RECmd RegBinary value content, MFTECmd
    $FILE_NAME raw bytes, and other binary-derived columns. Python's csv
    reader raises `_csv.Error: line contains NUL` on the first one.
    """
    for line in line_iterator:
        # Fast path: no NUL → yield as-is. Most lines won't have any.
        yield line.replace("\x00", "") if "\x00" in line else line


def normalize_field_name(name, preserve_case=False):
    """Normalize field name: spaces -> underscores, drop non-[a-zA-Z0-9_-]; lowercase by default.

    When preserve_case=True, keep the original casing. This is the right mode
    for feeding the existing SOF-ELK KAPE parsers (6501/6503/6504) which were
    built around EZ Tools' native PascalCase JSON output (BagPath, FileName,
    TimeCreated, etc.) — csv2json'd output needs to match that schema or the
    upstream rename blocks won't fire.
    """
    if not name:
        return ""
    fieldname = name.replace(" ", "_")
    fieldname = re.sub(r"[^a-zA-Z0-9\-_]", "", fieldname)
    return fieldname if preserve_case else fieldname.lower()


def convert_value(value):
    """Convert string value to appropriate data type (null, bool, int, float, str)."""
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


def process_csv_to_json(csv_filename, json_filename, tags, encoding=None, preserve_case=False):
    """Convert CSV file to JSON."""
    if encoding is None:
        encoding = detect_encoding(csv_filename)

    try:
        # errors="replace" is a safety net so a single mangled byte in a
        # 100 MB forensic CSV doesn't abort the whole conversion. The bad
        # bytes become U+FFFD and the rest of the row still ingests.
        with open(csv_filename, "r", encoding=encoding, errors="replace") as csvfile, \
             open(json_filename, "w") as jsonfile:

            cleaned = strip_nuls(csvfile)
            reader = csv.DictReader(cleaned)
            row_count = 0

            for row in reader:
                # Guard against None keys (which can happen when EZ Tools
                # writes a trailing comma producing an extra unnamed column)
                newrow = {
                    normalize_field_name(k, preserve_case): convert_value(v)
                    for k, v in row.items() if k
                }
                newrow = remove_empty_fields(newrow)

                if tags is not None:
                    if "tags" in newrow:
                        # just split on spaces for now - will adjust in future if data requires it
                        newrow["tags"] = newrow["tags"].split(" ") if isinstance(newrow["tags"], str) else list(newrow["tags"])
                    else:
                        newrow["tags"] = []

                    for tag in tags:
                        newrow["tags"].append(tag)

                json.dump(newrow, jsonfile)
                jsonfile.write("\n")
                row_count += 1

            # Brief stderr summary so batch-conversion scripts can log progress
            sys.stderr.write(
                f"csv2json: {row_count} rows  {csv_filename} -> {json_filename}  (encoding={encoding})\n"
            )

    except FileNotFoundError:
        sys.stderr.write(f"ERROR: File '{csv_filename}' not found.\n")
        sys.exit(1)
    except Exception as e:
        sys.stderr.write(f"ERROR: An unexpected error occurred: {e}.\n")
        sys.exit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Convert a CSV file (Eric Zimmerman forensic tools, etc.) to one-JSON-per-line."
    )
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
    parser.add_argument(
        "-e",
        "--encoding",
        dest="encoding",
        help="Force input encoding (e.g., utf-8, utf-8-sig, utf-16, latin-1). "
             "Auto-detected from BOM by default; specify only if auto-detection fails.",
    )
    parser.add_argument(
        "-p",
        "--preserve-case",
        dest="preserve_case",
        action="store_true",
        help="Keep original field-name casing instead of lowercasing. "
             "Use this when feeding the upstream SOF-ELK KAPE parsers "
             "(6501-kape_mftecmd, 6503-kape_lecmd, 6504-kape_evtxecmd) which "
             "expect EZ Tools' native PascalCase keys (BagPath, FileName, "
             "TimeCreated, etc.). Default is lowercase for the newer "
             "shellbags/prefetch/registry/browser parsers.",
    )
    args = parser.parse_args()

    process_csv_to_json(args.infile, args.outfile, args.tags, args.encoding, args.preserve_case)
