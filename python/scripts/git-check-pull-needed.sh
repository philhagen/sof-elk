#!/bin/bash
# SOF-ELK® Supporting script Wrapper
# (C)2025 Lewes Technology Consulting, LLC

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PYTHONPATH="${DIR}/../sofelk/source"

export PYTHONPATH
# $1 in original was upstream (optional). The python module accepts 'upstream' positional arg.
# If $1 is set, pass it. If not, python defaults to @{u}.
if [ -n "$1" ]; then
    python3 -m sof_elk.cli management check_pull "$1"
else
    python3 -m sof_elk.cli management check_pull
fi
