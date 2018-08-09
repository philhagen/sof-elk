#!/bin/bash
# SOF-ELK® Supporting script
# (C)2018 Lewes Technology Consulting, LLC
#
# This script simply dumps all dashboards to files on the filesystem

# get list of all dashboard IDs to use for export and filenames
for DASHID in $( curl -s "http://localhost:9200/.kibana/_search?q=type:dashboard&size=10000" | jq -r '.hits.hits[]._id[10:]' ); do

    # get the dashboard content, filter to remove unnecessary fields
    curl -s -XGET http://localhost:5601/api/kibana/dashboards/export?dashboard=${DASHID} > ${DASHID}_raw.json 2> /dev/null
    cat ${DASHID}_raw.json | jq '.|del(.objects[].version)|del(.objects[].attributes.version)|del(.objects[].updated_at)' > ${DASHID}.json 2> /dev/null
    RES=$?
    if [ $RES -eq 0 ]; then
        rm -f ${DASHID}_raw.json
    else
        rm -f ${DASHID}.json
        echo "WARNING!! ${DASHID} paring-down failed.  This must be manually performed - the source data likely is missing some closure brackets."
        continue
    fi

    # remove the index-patterns on the intro dashboard
    DASHTITLE=$( cat ${DASHID}.json | jq -r ".objects[] | select(.id == \"${DASHID}\") | .attributes.title" )
    if [ "${DASHTITLE}" == "SOF-ELK® VM Introduction Dashboard" ]; then
        cat ${DASHID}.json | jq ". | del(.objects[] | select(.type==\"index-pattern\"))" > ${DASHID}_temp.json
        rm ${DASHID}.json
        mv ${DASHID}_temp.json ${DASHID}.json
    fi
done
