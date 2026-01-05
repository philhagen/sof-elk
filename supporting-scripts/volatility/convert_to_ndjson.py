#!/usr/bin/env python3
"""
Convert Volatility JSON array to NDJSON (newline-delimited JSON)
================================================================
Logstash's json_lines codec expects one JSON object per line.
This script converts Volatility's JSON array format to NDJSON.

Usage:
    python convert_to_ndjson.py input.json output.ndjson
"""

import json
import sys
from pathlib import Path


def convert_to_ndjson(input_file: Path, output_file: Path):
    """Convert JSON array to NDJSON format"""

    print(f"Reading: {input_file}")
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Handle both array and object inputs
    if isinstance(data, list):
        records = data
    elif isinstance(data, dict):
        # If it's a single object, wrap it in a list
        records = [data]
    else:
        print(f"Error: Unexpected data type: {type(data)}")
        sys.exit(1)

    print(f"Converting {len(records)} records to NDJSON...")
    with open(output_file, 'w', encoding='utf-8') as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False) + '\n')

    print(f"Written to: {output_file}")
    print(f"Total records: {len(records)}")


def main():
    if len(sys.argv) != 3:
        print("Usage: python convert_to_ndjson.py <input.json> <output.ndjson>")
        sys.exit(1)

    input_file = Path(sys.argv[1])
    output_file = Path(sys.argv[2])

    if not input_file.exists():
        print(f"Error: Input file not found: {input_file}")
        sys.exit(1)

    convert_to_ndjson(input_file, output_file)


if __name__ == '__main__':
    main()
