#!/usr/bin/env python3
# SOF-ELK® Supporting script Wrapper
# (C)2025 Lewes Technology Consulting, LLC

import sys
import os
import argparse

# Ensure we can import the sof_elk package
current_dir = os.path.dirname(os.path.abspath(__file__))
source_dir = os.path.join(current_dir, "..", "sofelk", "source")
if source_dir not in sys.path:
    sys.path.insert(0, source_dir)

from sof_elk.management.elasticsearch import run_freeze

def main():
    parser = argparse.ArgumentParser(
        description="Disable or re-enable Elasticsearch indices (Wrapper)."
    )
    parser.add_argument("-a", "--action", dest="action", choices=["freeze", "thaw", "list"], required=True, help="Action to take.")
    parser.add_argument("-e", "--host", dest="host", default="127.0.0.1", help="Elasticsearch IP address")
    parser.add_argument("-p", "--port", dest="port", default=9200, type=int, help="Elasticsearch port")
    parser.add_argument("-i", "--index", dest="index", help="Index to act on.")
    parser.add_argument("-t", "--tag", dest="tag", default=False, help="Tag for frozen index.")
    parser.add_argument("-n", "--newindex", dest="newindex", default=False, help="Name for new index.")
    parser.add_argument("-d", "--delete", dest="delete", action="store_true", help="Delete source index.")
    
    args = parser.parse_args()
    
    run_freeze(args)

if __name__ == "__main__":
    main()
