#!/bin/bash
# SOF-ELK® Supporting script
# (C)2019 Lewes Technology Consulting, LLC
#
# This script dumps all dashboards, visualizations, index-patterns and associated field data into files on the filesystem

export LC_ALL=C

# set defaults
kibana_host=localhost
kibana_port=5601

[ -r /etc/sysconfig/sof-elk ] && . /etc/sysconfig/sof-elk

# TODO: this may need to sort output for better revision control (http://bigdatums.net/2016/11/29/sorting-json-by-value-with-jq/)

mkdir dashboard visualization search index-pattern index-pattern/fields index-pattern/fieldformats

# get list of all dashboard IDs and their content
for DASHID in $( curl -s -H 'kbn-xsrf: true' -X GET "http://${kibana_host}:${kibana_port}/api/saved_objects/_find?type=dashboard&fields=id&per_page=10000" | jq -cr '.saved_objects[].id' ); do
    curl -s -H 'kbn-xsrf: true' -X GET "http://${kibana_host}:${kibana_port}/api/saved_objects/dashboard/${DASHID}" | jq 'del(.id,.type,.version,.updated_at,.migrationVersion)' > dashboard/${DASHID}.json
done

# get a list of all visualization IDs and their content
for VISUALIZATIONID in $( curl -s -H 'kbn-xsrf: true' -X GET "http://${kibana_host}:${kibana_port}/api/saved_objects/_find?type=visualization&fields=id&per_page=10000" | jq -cr '.saved_objects[].id' ); do
    curl -s -H 'kbn-xsrf: true' -X GET "http://${kibana_host}:${kibana_port}/api/saved_objects/visualization/${VISUALIZATIONID}" | jq 'del(.id,.type,.version,.updated_at,.migrationVersion)' > visualization/${VISUALIZATIONID}.json
done

# get a list of all search IDs and their content
for SEARCHID in $( curl -s -H 'kbn-xsrf: true' -X GET "http://${kibana_host}:${kibana_port}/api/saved_objects/_find?type=search&fields=id&per_page=10000" | jq -cr '.saved_objects[].id' ); do
    curl -s  -H 'kbn-xsrf: true' -X GET "http://${kibana_host}:${kibana_port}/api/saved_objects/search/${SEARCHID}" | jq 'del(.id,.type,.version,.updated_at,.migrationVersion)' > search/${SEARCHID}.json
done

# get a list of all index-patterns and their content, separate out the fields and fieldformatmap
for INDEXPATTERNID in $( curl -s -H 'kbn-xsrf: true' -X GET "http://${kibana_host}:${kibana_port}/api/saved_objects/_find?type=index-pattern&fields=id&per_page=10000" | jq -cr '.saved_objects[].id' ); do
    # index-pattern itself, stripping the fields and fieldFormatMap elements
    curl -s -H 'kbn-xsrf: true' -X GET "http://${kibana_host}:${kibana_port}/api/saved_objects/index-pattern/${INDEXPATTERNID}" | jq 'del(.id,.type,.version,.updated_at,.attributes.fields,.attributes.fieldFormatMap,.migrationVersion)' > index-pattern/${INDEXPATTERNID}.json

    # just the fields, sorting (per LC_ALL) for easier revision control
    curl -s -H 'kbn-xsrf: true' -X GET "http://${kibana_host}:${kibana_port}/api/saved_objects/index-pattern/${INDEXPATTERNID}" | jq -c '.attributes.fields | fromjson[]' 2> /dev/null | sort > index-pattern/fields/${INDEXPATTERNID}.json 2> /dev/null

    # just the fieldFormatMap, sorting (per LC_ALL) for easier revision control
    curl -s -H 'kbn-xsrf: true' -X GET "http://${kibana_host}:${kibana_port}/api/saved_objects/index-pattern/${INDEXPATTERNID}" | jq '.attributes.fieldFormatMap | fromjson | to_entries | sort_by(.key)' > index-pattern/fieldformats/${INDEXPATTERNID}.json 2> /dev/null

    # if any of these files are zero-length, remove them
    if [ ! -s index-pattern/fields/${INDEXPATTERNID}.json ]; then
        rm -f index-pattern/fields/${INDEXPATTERNID}.json
    fi
    if [ ! -s index-pattern/fieldformats/${INDEXPATTERNID}.json ]; then
        rm -f index-pattern/fieldformats/${INDEXPATTERNID}.json
    fi
done