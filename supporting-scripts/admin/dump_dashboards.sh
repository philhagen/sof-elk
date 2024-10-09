#!/bin/bash
# SOF-ELK® Supporting script
# (C)2023 Lewes Technology Consulting, LLC
#
# This script dumps all dashboards, visualizations, data views and associated field data into files on the filesystem

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

mkdir dashboard lens visualization map search data_views
nestedJSONKeys=".attributes.kibanaSavedObjectMeta.searchSourceJSON .attributes.optionsJSON .attributes.panelsJSON .attributes.uiStateJSON .attributes.visState"

# get list of all dashboard IDs and their content
for DASHID in $( curl -s -H 'kbn-xsrf: true' -X GET "http://${kibana_host}:${kibana_port}/api/saved_objects/_find?type=dashboard&fields=id&per_page=10000" | jq -cr '.saved_objects[].id' ); do
    dashboardJSON=$( curl -s -H 'kbn-xsrf: true' -X GET "http://${kibana_host}:${kibana_port}/api/saved_objects/dashboard/${DASHID}" | jq -cS 'del(.version,.created_at,.updated_at,.migrationVersion)' )
    dashboardName=$( echo ${dashboardJSON} | jq '.attributes.title' )
    echo "Dumping Dashboard: ${dashboardName}"

    jsonModString=$( sortNestedJSON "${nestedJSONKeys}" "${dashboardJSON}" )

    echo ${dashboardJSON} | jq -S ".references? |= unique_by(.id) | ${jsonModString}" > dashboard/${DASHID}.json
done

# get a list of all lens IDs and their content
for LENSID in $( curl -s -H 'kbn-xsrf: true' -X GET "http://${kibana_host}:${kibana_port}/api/saved_objects/_find?type=lens&fields=id&per_page=10000" | jq -cr '.saved_objects[].id' ); do
    lensJSON=$( curl -s -H 'kbn-xsrf: true' -X GET "http://${kibana_host}:${kibana_port}/api/saved_objects/lens/${LENSID}" | jq -cS "del(.version,.created_at,.updated_at,.migrationVersion)" )
    lensName=$( echo ${lensJSON} | jq '.attributes.title' )
    echo "Dumping Lens: ${lensName}"

    echo ${lensJSON} | jq -S ".references? |= unique_by(.id)" > lens/${LENSID}.json
done

# get a list of all visualization IDs and their content
for VISUALIZATIONID in $( curl -s -H 'kbn-xsrf: true' -X GET "http://${kibana_host}:${kibana_port}/api/saved_objects/_find?type=visualization&fields=id&per_page=10000" | jq -cr '.saved_objects[].id' ); do
    visualizationJSON=$( curl -s -H 'kbn-xsrf: true' -X GET "http://${kibana_host}:${kibana_port}/api/saved_objects/visualization/${VISUALIZATIONID}" | jq -cS "del(.version,.created_at,.updated_at,.migrationVersion)" )
    visualizationName=$( echo ${visualizationJSON} | jq '.attributes.title' )
    echo "Dumping Visualization: ${visualizationName}"

    jsonModString=$( sortNestedJSON "${nestedJSONKeys}" "${visualizationJSON}" )

    echo ${visualizationJSON} | jq -S ".references? |= unique_by(.id) | ${jsonModString}" > visualization/${VISUALIZATIONID}.json
done

# get a list of all map IDs and their content
for MAPID in $( curl -s -H 'kbn-xsrf: true' -X GET "http://${kibana_host}:${kibana_port}/api/saved_objects/_find?type=map&fields=id&per_page=10000" | jq -cr '.saved_objects[].id' ); do
    mapJSON=$( curl -s -H 'kbn-xsrf: true' -X GET "http://${kibana_host}:${kibana_port}/api/saved_objects/map/${MAPID}" | jq -Sc 'del(.version,.created_at,.updated_at,.migrationVersion)' )
    mapName=$( echo ${mapJSON} | jq '.attributes.title' )
    echo "Dumping Map: ${mapName}"

    jsonModString=$( sortNestedJSON "${nestedJSONKeys}" "${mapJSON}" )

    echo ${mapJSON} | jq -S ".references? |= unique_by(.id) | ${jsonModString}" > map/${MAPID}.json
done

# get a list of all search IDs and their content
for SEARCHID in $( curl -s -H 'kbn-xsrf: true' -X GET "http://${kibana_host}:${kibana_port}/api/saved_objects/_find?type=search&fields=id&per_page=10000" | jq -cr '.saved_objects[].id' ); do
    searchJSON=$( curl -s  -H 'kbn-xsrf: true' -X GET "http://${kibana_host}:${kibana_port}/api/saved_objects/search/${SEARCHID}" | jq -Sc 'del(.version,.created_at,.updated_at,.migrationVersion)' )
    searchName=$( echo ${searchJSON} | jq '.attributes.title' )
    echo "Dumping Search: ${searchName}"

    jsonModString=$( sortNestedJSON "${nestedJSONKeys}" "${searchJSON}" )

    echo ${searchJSON} | jq -S ".references? |= unique_by(.id) | ${jsonModString}" > search/${SEARCHID}.json
done

# get a list of all data_views and their content
for DATAVIEWID in $( curl -s -H 'kbn-xsrd: true' -X GET "http://${kibana_host}:${kibana_port}/api/data_views?per_page=10000" | jq -cr '.data_view[] | .id' ); do
    echo "Dumping Data View: ${DATAVIEWID}"

    curl -s -H 'kbn-xsrf: true' -X GET "http://${kibana_host}:${kibana_port}/api/data_views/data_view/${DATAVIEWID}" | jq -S 'del(.data_view.version,.data_view.fields,.data_view.fieldAttrs,.data_view.runtimeFieldMap,.data_view.namespaces,.data_view.sourceFilters,.data_view.typeMeta)' > data_views/${DATAVIEWID}.json
done
