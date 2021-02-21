#!/bin/bash
# SOF-ELK® Supporting script
# (C)2021 Lewes Technology Consulting, LLC
#
# This script dumps all dashboards, visualizations, index-patterns and associated field data into files on the filesystem

export LC_ALL=C

# set defaults
kibana_host=localhost
kibana_port=5601

[ -r /etc/sysconfig/sof-elk ] && . /etc/sysconfig/sof-elk

# this function returns a jq modification string that will replace json strings at the indicated keys with sorted values of their original content
sortNestedJSON () {
    JSONKeys="$1"
    sourceJSON="$2"

    jsonMod=""
    for nestedJSONKey in ${JSONKeys}; do
        nestedJSONValue=$( echo ${sourceJSON} | jq -Sc "if ${nestedJSONKey}? then ${nestedJSONKey} | fromjson else null end" )
        if [ "${nestedJSONValue}" != "null" ]; then
            if [ "${jsonMod}" ]; then
                jsonMod="${jsonMod} |"
            fi
            sortedJSONValue=$( echo ${nestedJSONValue} | jq -Sc 'tojson' )
            jsonMod="${jsonMod} ${nestedJSONKey}=${sortedJSONValue}"
        fi
    done
    echo ${jsonMod}
}

mkdir dashboard visualization search index-pattern index-pattern/fields index-pattern/fieldformats

# get list of all dashboard IDs and their content
for DASHID in $( curl -s -H 'kbn-xsrf: true' -X GET "http://${kibana_host}:${kibana_port}/api/saved_objects/_find?type=dashboard&fields=id&per_page=10000" | jq -cr '.saved_objects[].id' ); do
    dashboardJSON=$( curl -s -H 'kbn-xsrf: true' -X GET "http://${kibana_host}:${kibana_port}/api/saved_objects/dashboard/${DASHID}" | jq -cS 'del(.id,.type,.version,.updated_at,.migrationVersion)' )
    dashboardName=$( echo ${dashboardJSON} | jq '.attributes.title' )
    echo "Dumping Dashboard: ${dashboardName}"

    nestedJSONKeys=".attributes.kibanaSavedObjectMeta.searchSourceJSON .attributes.uiStateJSON .attributes.visState"
    jsonModString=$( sortNestedJSON "${nestedJSONKeys}" "${dashboardJSON}" )

    echo ${dashboardJSON} | jq -S "${jsonModString}"  > dashboard/${DASHID}.json
done

# get a list of all visualization IDs and their content
for VISUALIZATIONID in $( curl -s -H 'kbn-xsrf: true' -X GET "http://${kibana_host}:${kibana_port}/api/saved_objects/_find?type=visualization&fields=id&per_page=10000" | jq -cr '.saved_objects[].id' ); do
    visualizationJSON=$( curl -s -H 'kbn-xsrf: true' -X GET "http://${kibana_host}:${kibana_port}/api/saved_objects/visualization/${VISUALIZATIONID}" | jq -cS "del(.id,.type,.version,.updated_at,.migrationVersion)" )
    visualizationName=$( echo ${visualizationJSON} | jq '.attributes.title' )
    echo "Dumping Visualization: ${visualizationName}"

    nestedJSONKeys=".attributes.kibanaSavedObjectMeta.searchSourceJSON .attributes.uiStateJSON .attributes.visState"
    jsonModString=$( sortNestedJSON "${nestedJSONKeys}" "${visualizationJSON}" )

    echo ${visualizationJSON} | jq -S "${jsonModString}" > visualization/${VISUALIZATIONID}.json
done

# get a list of all search IDs and their content
for SEARCHID in $( curl -s -H 'kbn-xsrf: true' -X GET "http://${kibana_host}:${kibana_port}/api/saved_objects/_find?type=search&fields=id&per_page=10000" | jq -cr '.saved_objects[].id' ); do
    searchJSON=$( curl -s  -H 'kbn-xsrf: true' -X GET "http://${kibana_host}:${kibana_port}/api/saved_objects/search/${SEARCHID}" | jq -Sc 'del(.id,.type,.version,.updated_at,.migrationVersion)' )
    searchName=$( echo ${searchJSON} | jq '.attributes.title' )
    echo "Dumping Search: ${searchName}"

    nestedJSONKeys=".attributes.kibanaSavedObjectMeta.searchSourceJSON"
    jsonModString=$( sortNestedJSON "${nestedJSONKeys}" "${searchJSON}" )

    echo ${searchJSON} | jq -S "${jsonModString}" > search/${SEARCHID}.json
done

echo "Dumping Index Patterns"
# get a list of all index-patterns and their content, separate out the fields and fieldformatmap
for INDEXPATTERNID in $( curl -s -H 'kbn-xsrf: true' -X GET "http://${kibana_host}:${kibana_port}/api/saved_objects/_find?type=index-pattern&fields=id&per_page=10000" | jq -cr '.saved_objects[].id' ); do
    # index-pattern itself, stripping the fields and fieldFormatMap elements
    curl -s -H 'kbn-xsrf: true' -X GET "http://${kibana_host}:${kibana_port}/api/saved_objects/index-pattern/${INDEXPATTERNID}" | jq -S 'del(.id,.type,.version,.updated_at,.attributes.fields,.attributes.fieldFormatMap,.migrationVersion)' > index-pattern/${INDEXPATTERNID}.json

    # just the fields, sorting (per LC_ALL) for easier revision control
    curl -s -H 'kbn-xsrf: true' -X GET "http://${kibana_host}:${kibana_port}/api/saved_objects/index-pattern/${INDEXPATTERNID}" | jq -c '.attributes.fields | fromjson[]' 2> /dev/null | sort > index-pattern/fields/${INDEXPATTERNID}.json 2> /dev/null

    # just the fieldFormatMap, sorting (per LC_ALL) for easier revision control
    curl -s -H 'kbn-xsrf: true' -X GET "http://${kibana_host}:${kibana_port}/api/saved_objects/index-pattern/${INDEXPATTERNID}" | jq -S '.attributes.fieldFormatMap | fromjson | to_entries | sort_by(.key)' > index-pattern/fieldformats/${INDEXPATTERNID}.json 2> /dev/null

    # if any of these files are zero-length, remove them
    if [ ! -s index-pattern/fields/${INDEXPATTERNID}.json ]; then
        rm -f index-pattern/fields/${INDEXPATTERNID}.json
    fi
    if [ ! -s index-pattern/fieldformats/${INDEXPATTERNID}.json ]; then
        rm -f index-pattern/fieldformats/${INDEXPATTERNID}.json
    fi
done