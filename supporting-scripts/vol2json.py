#!/usr/bin/env python3
# SOF-ELK® Supporting script
# (C)2026 Lewes Technology Consulting, LLC
#
# Convert Volatility 3 plugin output into clean UTF-8 NDJSON ready for
# filebeat ingest — one top-level record per line, with BOMs stripped
# and encoding auto-detected.
#
# Why this script exists:
#   Volatility 3 prints JSON when invoked with `-r json`, but what lands
#   on disk depends on how the user redirected stdout:
#     * Linux/macOS (bash, zsh):                     plain UTF-8
#     * PowerShell `>` or `Out-File` (default):      UTF-16 LE with BOM
#     * PowerShell `Out-File -Encoding utf8`:        UTF-8 with BOM
#     * `vol ... | jq -c '.[]' > out.json`:           already NDJSON
#   Filebeat reads as UTF-8 by default, so PowerShell-redirected output
#   silently fails JSON parse downstream (NUL bytes between every visible
#   character confuse the parser). Pre-processing through this script
#   normalizes the bytes regardless of how the file was produced.
#
# Top-level JSON shape also varies by plugin:
#     * windows.pstree.PsTree:    JSON array of root process trees
#     * pslist / dlllist / etc.:  JSON array of records
#     * Already-NDJSON input:     one JSON per line
#   This script handles all three.
#
# Usage:
#   vol2json.py -r vol_out.json -w vol_out.jsonl
#   vol2json.py -r vol_out.json -w -                  # stdout
#   vol2json.py -r vol_out.json -w out.jsonl --encoding utf-16
#
# Output is always UTF-8 NDJSON with one record per line, suitable for
# /logstash/kape/ drop. Filebeat patterns (lib/filebeat_inputs/kape.yml)
# match *pstree*.json / *pstree*.jsonl etc.

import argparse
import json
import sys


def detect_encoding(filename):
    """Sniff the first bytes for a BOM. Returns one of:
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


def emit(obj, out, counter):
    """Serialize one record as a single line of compact UTF-8 JSON."""
    out.write(json.dumps(obj, ensure_ascii=False))
    out.write("\n")
    counter[0] += 1


def process(infile, outfile, encoding=None):
    if encoding is None:
        encoding = detect_encoding(infile)

    # errors="replace" is a safety net for the rare mangled byte — same
    # convention csv2json.py uses. Lets one bad byte spoil only the chars
    # around it, not the whole file.
    with open(infile, "r", encoding=encoding, errors="replace") as fin:
        content = fin.read()

    # Strip any stray BOM at the top of the file (utf-16 codec usually
    # consumes the BOM itself, but utf-8-sig and edge cases sometimes
    # leave a U+FEFF behind).
    content = content.lstrip("﻿").strip()

    if not content:
        sys.stderr.write(f"vol2json: empty input {infile}\n")
        return 0

    out_is_stdout = (outfile == "-")
    out = sys.stdout if out_is_stdout else open(outfile, "w", encoding="utf-8")

    counter = [0]
    skipped = 0

    try:
        # Path 1: whole file parses as one JSON value (array or single dict)
        obj = json.loads(content)
        if isinstance(obj, list):
            for item in obj:
                if isinstance(item, dict):
                    emit(item, out, counter)
                else:
                    skipped += 1
        elif isinstance(obj, dict):
            emit(obj, out, counter)
    except json.JSONDecodeError:
        # Path 2: not one big JSON — try line-by-line (NDJSON)
        for lineno, ln in enumerate(content.splitlines(), 1):
            ln = ln.strip().lstrip("﻿")
            if not ln:
                continue
            try:
                obj = json.loads(ln)
            except json.JSONDecodeError as e:
                sys.stderr.write(f"vol2json: line {lineno}: skipping bad JSON ({e})\n")
                skipped += 1
                continue
            if isinstance(obj, list):
                for item in obj:
                    if isinstance(item, dict):
                        emit(item, out, counter)
                    else:
                        skipped += 1
            elif isinstance(obj, dict):
                emit(obj, out, counter)
            else:
                skipped += 1

    if not out_is_stdout:
        out.close()

    sys.stderr.write(
        f"vol2json: {counter[0]} records  {infile} -> {outfile}  "
        f"(encoding={encoding}{', skipped=' + str(skipped) if skipped else ''})\n"
    )
    return counter[0]


def main():
    p = argparse.ArgumentParser(
        description="Normalize Volatility 3 JSON output into clean UTF-8 NDJSON.",
        epilog=(
            "Examples:\n"
            "  vol2json.py -r vol_out.json -w pstree.jsonl\n"
            "  vol2json.py -r vol_out.json -w - | head\n"
            "  vol2json.py -r vol_out.json -w out.jsonl --encoding utf-16\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument(
        "-r", "--read", dest="infile", required=True,
        help="Input Volatility JSON file (UTF-8 / UTF-8 BOM / UTF-16 LE/BE auto-detected)",
    )
    p.add_argument(
        "-w", "--write", dest="outfile", required=True,
        help='Output NDJSON file path. Use "-" for stdout.',
    )
    p.add_argument(
        "--encoding", dest="encoding", default=None,
        help="Force input encoding (e.g., utf-8, utf-16, utf-16-le, utf-8-sig). "
             "Default: auto-detect via BOM, fall back to utf-8.",
    )
    args = p.parse_args()

    sys.exit(0 if process(args.infile, args.outfile, args.encoding) > 0 else 2)


if __name__ == "__main__":
    main()
