#!/bin/bash
# SOF-ELK® Supporting script Wrapper
# (C)2025 Lewes Technology Consulting, LLC

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PYTHONPATH="${DIR}/../sofelk/source"

export PYTHONPATH
# python3 -m sof_elk.cli management vm_update_check
# This script is often run via cron or login, so suppress output if needed?
# Original script didn't suppress, but it only printed if errors (curl silent).
# The python module mimics silent operation unless file is updated.
python3 -m sof_elk.cli management vm_update_check "$@"
