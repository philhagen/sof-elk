#!/usr/bin/env python3
# SOF-ELK® Supporting script
# (C)2026 Tony Knutson, Lewes Technology Consulting, LLC
#
# Convert Volatility 3 plugin output into clean UTF-8 newline-delimited JSON
# ready for filebeat ingest: one top-level record per line, with BOMs stripped
# and encoding auto-detected.
#
# Why this script exists:
#   When run on a Microsoft Windows platform, Volatility 3 outputs UTF-16
#   newline-delimited JSON via its "-r jsonl" option.
#     * Linux/macOS (bash, zsh):                 plain UTF-8
#     * PowerShell `>` or `Out-File` (default):  UTF-16 LE with BOM
#     * PowerShell `Out-File -Encoding utf8`:    UTF-8 with BOM
#     * `vol ... | jq -c '.[]' > out.json`:      already newline-delimited JSON
#   Filebeat expects its data in UTF-8 encoding by default, so PowerShell-
#   redirected output silently fails JSON parse downstream (usually, NULL
#   bytes between each printable character), confusing the parser). Pre-
#   processing through this script normalizes the bytes regardless of how
#   the file was produced.
#   Technically, this script is only required for output created with one of
#   the BOM-prefixed forms indicated above, but if run against existing plain
#   UTF-8 data, the resulting file will be unchanged from the input.
#
#   Additionally, while the supported Volatility 3 files are limited to those
#   created with the "-r jsonl" renderer, this script will also normalize
#   multiline JSON created with the "-r json" renderer into newline-delimited
#   JSON, allowing a clean ingest.
#
# Usage:
#   volatility2sof-elk.py -r pstree-UTF16.json -w pstree_-UTF8.json
#   volatility2sof-elk.py -r pslist-UTF16.json -w -  # prints results on stdout
#   volatility2sof-elk.py -r cmdline-UTF16.json -w cmdline-UTF8.json --encoding utf-16
#
# Output is always UTF-8 newline-delimited JSON with one record per line,
# suitable for ingest via the /logstash/volatility/*/ directories.

import argparse
import json
import sys
import contextlib


def detect_encoding(filename):
    """Examine the first bytes of the input file for a BOM. Returns one of:
    'utf-16'    — UTF-16 LE or BE with BOM (PowerShell default)
    'utf-8-sig' — UTF-8 with BOM
    'utf-8'     — no BOM, assume UTF-8 (covers Linux/macOS native output)
    """
    with open(filename, "rb") as f:
        head = f.read(4)
    if head.startswith(b"\xff\xfe") or head.startswith(b"\xfe\xff"):
        return "utf-16"
    if head.startswith(b"\xef\xbb\xbf"):
        return "utf-8-sig"
    return "utf-8"


def emit(obj, out):
    """Serialize one record as a single line of compact UTF-8 JSON."""
    out.write(json.dumps(obj, ensure_ascii=False))
    out.write("\n")


def emit_object(obj, out, processed, skipped):
    if isinstance(obj, list):
        for item in obj:
            processed, skipped = emit_object(item, out, processed, skipped)
    elif isinstance(obj, dict):
        emit(obj, out)
        processed += 1
    else:
        skipped += 1
    return processed, skipped


def process(input_filename, output_filename, encoding=None):
    if encoding is None:
        encoding = detect_encoding(input_filename)

    # errors="replace" is a safety net for the rare mangled byte — same
    # convention csv2json.py uses. Lets one bad byte spoil only the chars
    # around it, not the whole file.
    with open(input_filename, "r", encoding=encoding, errors="replace") as inputfile:
        content = inputfile.read()

    # Strip any stray BOM at the top of the file (utf-16 codec usually
    # consumes the BOM itself, but utf-8-sig and edge cases sometimes
    # leave a U+FEFF behind).
    content = content.lstrip("\ufeff").strip()

    if not content:
        sys.stderr.write(f"volatility2sof-elk: empty input {input_filename}\n")
        return 0

    lines_processed = 0
    lines_skipped = 0

    if output_filename == "-":
        cm = contextlib.nullcontext(sys.stdout)
    else:
        cm = open(output_filename, "w", encoding="utf-8")

    with cm as out:
        try:
            # Path 1: whole file parses as one JSON value (array or single dict)
            obj = json.loads(content)
            lines_processed, lines_skipped = emit_object(
                obj, out, lines_processed, lines_skipped
            )
        except json.JSONDecodeError:
            # Path 2: not one big JSON — try line-by-line (newline-delimited JSON)
            for lineno, ln in enumerate(content.splitlines(), 1):
                ln = ln.strip().lstrip("\ufeff")
                if not ln:
                    continue
                try:
                    obj = json.loads(ln)
                except json.JSONDecodeError as e:
                    sys.stderr.write(
                        f"volatility2sof-elk.py: line {lineno}: skipping bad JSON ({e})\n"
                    )
                    lines_skipped += 1
                    continue
                lines_processed, lines_skipped = emit_object(
                    obj, out, lines_processed, lines_skipped
                )

    sys.stderr.write(
        f"volatility2sof-elk.py: {lines_processed} records  {input_filename} -> {output_filename}"
        f" (encoding={encoding}{', skipped=' + str(lines_skipped) if lines_skipped > 0 else ''})"
        f"\n"
    )
    return lines_processed


def main():
    parser = argparse.ArgumentParser(
        description="Normalize Volatility 3 JSON output into clean UTF-8 newline-delimited JSON.",
        epilog=(
            "Examples:\n"
            "  volatility2sof-elk.py -r pstree-UTF16.json -w pstree-UTF8.json\n"
            "  volatility2sof-elk.py -r pslist-UTF16.json -w - | head\n"
            "  volatility2sof-elk.py -r cmdline-UTF16.json -w cmdline-UTF8.json --encoding utf-16\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "-r",
        "--read",
        dest="input_filename",
        required=True,
        help="Input Volatility JSON file (UTF-8 / UTF-8 BOM / UTF-16 LE/BE auto-detected)",
    )
    parser.add_argument(
        "-w",
        "--write",
        dest="output_filename",
        required=True,
        help='Output newline-delimited JSON file path. Use "-" for stdout.',
    )
    parser.add_argument(
        "--encoding",
        dest="encoding",
        default=None,
        help="Force input encoding (e.g., utf-8, utf-16, utf-16-le, utf-8-sig). "
        "Default: auto-detect via BOM, fall back to utf-8.",
    )
    args = parser.parse_args()

    sys.exit(
        0
        if process(args.input_filename, args.output_filename, args.encoding) > 0
        else 2
    )


if __name__ == "__main__":
    main()
