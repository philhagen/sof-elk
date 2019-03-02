#!/bin/bash
# SOF-ELK® Supporting script
# (C)2019 Lewes Technology Consulting, LLC
#
# This script simply dumps all dashboards to files on the filesystem

LC_ALL=C

# get list of all dashboard IDs to use for export and filenames
for DASHID in $( curl -s -XGET --compressed -H "Accept-Encoding: gzip, deflate, br" "http://localhost:9200/.kibana/_search?q=type:dashboard&size=10000" | jq -r '.hits.hits[]._id[10:]' ); do

    # get the dashboard content, filter to remove unnecessary fields
    curl -s -XGET --compressed -H "Accept-Encoding: gzip, deflate, br" http://localhost:5601/api/kibana/dashboards/export?dashboard=${DASHID} > ${DASHID}_raw.json 2> /dev/null
    cat ${DASHID}_raw.json | jq '.|del(.objects[].version)|del(.objects[].attributes.version)|del(.objects[].updated_at)|del(.objects[].migrationVersion)' > ${DASHID}.json 2> /dev/null
    RES=$?
    if [ $RES -eq 0 ]; then
        rm -f ${DASHID}_raw.json
    else
        rm -f ${DASHID}.json
        echo "WARNING!! ${DASHID} pare-down failed.  This must be manually performed - the source data likely is missing some closure brackets."
        continue
    fi

    # remove the index-patterns on the intro dashboard file
    DASHTITLE=$( cat ${DASHID}.json | jq -r ".objects[] | select(.id == \"${DASHID}\") | .attributes.title" )
    if [ "${DASHTITLE}" == "SOF-ELK® VM Introduction Dashboard" ]; then
        cat ${DASHID}.json | jq ". | del(.objects[] | select(.type == \"index-pattern\"))" > ${DASHID}_temp.json
        rm ${DASHID}.json
        mv ${DASHID}_temp.json ${DASHID}.json
    fi

    # pull out fields and fieldFormats to their own files
    cat ${DASHID}.json | jq -r '.objects[] | select(.type=="index-pattern") | .attributes.fields' | jq -c '.[]' | sort | uniq > ${DASHID}_fields.txt 2> /dev/null
    if [ ! -s ${DASHID}_fields.txt ]; then
        echo "NOTE: ${DASHID} did not have any index-pattern fields"
        rm ${DASHID}_fields.txt
    else
        # replace the fields in the original file with a stub
### TODO: THIS NEEDS TO BE MORE RESILIENT - WE'RE LUCKY THERE ARE NO 'fields' ITEMS IN NON-INDEX-PATTERN TYPES
        cat ${DASHID}.json | jq 'del(.objects[].attributes.fields)' > ${DASHID}_temp.json
        rm ${DASHID}.json
        mv ${DASHID}_temp.json ${DASHID}.json
    fi
    cat ${DASHID}.json | jq -r '.objects[] | select(.type=="index-pattern") | .attributes.fieldFormatMap' | jq '.' > ${DASHID}_fieldFormatMap.txt 2> /dev/null
    if [ ! -s ${DASHID}_fieldFormatMap.txt ]; then
        echo "NOTE: ${DASHID} did not have any index-pattern fieldFormats"
        rm ${DASHID}_fieldFormatMap.txt
    else
        # replace the fieldFormats in the original file with a stub
### TODO: THIS NEEDS TO BE MORE RESILIENT - WE'RE LUCKY THERE ARE NO 'fieldFormatMap' ITEMS IN NON-INDEX-PATTERN TYPES
        cat ${DASHID}.json | jq 'del(.objects[].attributes.fieldFormatMap)' > ${DASHID}_temp.json
        rm ${DASHID}.json
        mv ${DASHID}_temp.json ${DASHID}.json
    fi

done
