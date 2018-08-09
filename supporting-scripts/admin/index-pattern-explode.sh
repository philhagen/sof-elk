#!/bin/bash
# SOF-ELK® Supporting script
# (C)2018 Lewes Technology Consulting, LLC
#
# this script will break out the index-pattern entries from a dashboard file

if [ -z $1 ]; then
    echo "ERROR - no input filename supplied.  Exiting."
    exit 1
fi

DASHID=$( echo $1 | cut -d\. -f 1 )

cat ${DASHID}.json | jq -r '.objects[] | select(.type=="index-pattern") | .attributes.fields' | jq -c '.[]' > ${DASHID}_fields.txt
if [ ! -s ${DASHID}_fields.txt ]; then
    echo "NOTE: ${DASHID} did not have any index-pattern fields"
    rm ${DASHID}_fields.txt
fi
cat ${DASHID}.json | jq -r '.objects[] | select(.type=="index-pattern") | .attributes.fieldFormatMap' | jq '.' > ${DASHID}_fieldFormatMap.txt
if [ ! -s ${DASHID}_fieldFormatMap.txt ]; then
    echo "NOTE: ${DASHID} did not have any index-pattern fieldFormats"
    rm ${DASHID}_fieldFormatMap.txt
fi
