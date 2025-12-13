#!/bin/bash
# SOF-ELK® Supporting script Wrapper
# (C)2025 Lewes Technology Consulting, LLC

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PYTHONPATH="${DIR}/../sofelk/source"

export PYTHONPATH
# Pass args directly. Python module handles -r, -w, -e logic.
python3 -m sof_elk.cli utils nfdump "$@"
