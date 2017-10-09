#!/bin/bash
# SOF-ELK® Supporting script
# (C)2017 Lewes Technology Consulting, LLC
#
# This script simply prints all loaded Elasticsearch indices to STDOUT

curl -s -XGET "http://localhost:9200/_cat/indices?v"
