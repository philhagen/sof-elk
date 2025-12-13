#!/bin/bash
# SOF-ELK® Supporting script Wrapper
# (C)2025 Lewes Technology Consulting, LLC

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PYTHONPATH="${DIR}/../sofelk/source"

export PYTHONPATH
# Pass args? The original script didn't take args for host/port, it hardcoded them mostly or relied on defaults.
# It used wait_for_es.sh which is also wrapped.
python3 -m sof_elk.cli management load_dashboards "$@"
