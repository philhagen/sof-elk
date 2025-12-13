#!/usr/bin/env python3
# SOF-ELK® Supporting script Wrapper
# (C)2025 Lewes Technology Consulting, LLC

import sys
import os

# Ensure we can import the sof_elk package
# Assuming this script is in supporting-scripts/, and sof_elk is in sofelk/source/
current_dir = os.path.dirname(os.path.abspath(__file__))
source_dir = os.path.join(current_dir, "..", "sofelk", "source")
if source_dir not in sys.path:
    sys.path.insert(0, source_dir)

from sof_elk.management.elasticsearch import run_clear, ElasticsearchManager

def main():
    # Parse arguments using the existing CLI logic or bridge it manually
    # The original script used argparse directly. 
    # The new modules use argparse via subcommands.
    # To maintain EXACT backward compatibility with flags like -i, -f, -a, -r
    # we can construct a namespace or similar.
    # But run_clear expects 'args' object with index, filepath, nukeitall, reload attributes.
    
    import argparse
    parser = argparse.ArgumentParser(
        description="Clear the SOF-ELK(R) Elasticsearch database (Wrapper)."
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("-i", "--index", dest="index", help="Index to clear or 'list'")
    group.add_argument("-f", "--filepath", dest="filepath", help="Local directory root or single local file to clear.")
    group.add_argument("-a", "--all", dest="nukeitall", action="store_true", default=False, help="Remove all documents.")
    parser.add_argument("-r", "--reload", dest="reload", action="store_true", default=False, help="Reload source files.")
    
    args = parser.parse_args()
    
    run_clear(args)

if __name__ == "__main__":
    main()
