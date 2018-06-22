#!/bin/bash
# SOF-ELK® Supporting script
# (C)2018 Lewes Technology Consulting, LLC
#
# This script simply dumps all dashboards to files on the filesystem

# get list of all dashboard IDs to use for export and filenames
for DASHID in $( curl -s "http://localhost:9200/.kibana/_search?q=type:dashboard&size=10000" | jq -r '.hits.hits[]._id[10:]' ); do
    curl -s -XGET http://localhost:5601/api/kibana/dashboards/export?dashboard=${DASHID} | jq '.|del(.objects[].version)|del(.objects[].attributes.version)' > ${DASHID}.json
done
