#!/bin/bash
# SOF-ELK® Supporting script
# (C)2026 Lewes Technology Consulting, LLC
#
# This script is used to load all dashboards, visualizations, saved searches, and data views to Kibana

# set defaults
es_host=localhost
es_port=9200
kibana_host=localhost
kibana_port=5601
kibana_alias=.kibana
sofelk_root_dir="/usr/local/sof-elk/"
kibana_file_dir="${sofelk_root_dir}kibana/"

[ -r /etc/sysconfig/sof-elk ] && . /etc/sysconfig/sof-elk

kibana_version=$( jq -r '.version' < /usr/share/kibana/package.json )
kibana_build=$(jq -r '.build.number' < /usr/share/kibana/package.json )

# gracefully handle null-glob matches
shopt -s nullglob

# small helper: run curl, capture HTTP status, warn (don't abort) on failure
do_curl() {
    local desc="$1"; shift
    local http_code
    local tmpfile
    tmpfile=$( mktemp )

    http_code=$( curl -s -o "${tmpfile}" -w '%{http_code}' "$@" )
    if [[ ! "${http_code}" =~ ^2 ]]; then
        echo "WARNING: ${desc} failed (HTTP ${http_code})" >&2
        cat "${tmpfile}" >&2
    fi
    rm -f "${tmpfile}"
}

# enter a holding pattern until the elasticsearch server is available, but don't wait too long
max_wait=60
wait_step=0
interval=5
until curl -s -X GET http://${es_host}:${es_port}/_cluster/health > /dev/null ; do
    wait_step=$(( ${wait_step} + ${interval} ))
    if [ ${wait_step} -gt ${max_wait} ]; then
        echo "ERROR: elasticsearch server not available for more than ${max_wait} seconds."
        exit 5
    fi
    sleep ${interval}
done

kibana_index=$( curl -s "http://${es_host}:${es_port}/_alias/${kibana_alias}" | jq -r 'keys[0] // empty' )

# re-insert all ES templates in case anything has changed
# this will not change existing mappings, just new indexes as they are created
for es_component_template_file in ${sofelk_root_dir}lib/elasticsearch_templates/component_templates/*.json; do
    es_component_template=$( echo $es_component_template_file | sed -e s'/.*\/component-\(.*\)\.json$/\1/' )
    echo "Loading ES Component Template: ${es_component_template}"

    do_curl "component template ${es_component_template}" \
        -H 'kbn-xsrf: true' -H 'Content-Type: application/json' \
        -X PUT "http://${es_host}:${es_port}/_component_template/${es_component_template}" \
        -d @"${es_component_template_file}"
done
for es_index_template_file in ${sofelk_root_dir}lib/elasticsearch_templates/index_templates/*.json; do
    es_index_template=$( echo $es_index_template_file | sed 's/.*\/index-\(.*\)\.json/\1/' )
    echo "Loading ES Index Template: ${es_index_template}"

    do_curl "index template ${es_index_template}" \
        -H 'kbn-xsrf: true' -H 'Content-Type: application/json' \
        -X PUT "http://${es_host}:${es_port}/_index_template/${es_index_template}" \
        -d @"${es_index_template_file}"
done

# set the default data view, time zone, and add TZ offset to the default date format, and other custom Kibana settings
echo "Setting Kibana Defaults"
do_curl "Kibana defaults" \
    -H 'kbn-xsrf: true' -H 'Content-Type: application/json' \
    -X POST "http://${kibana_host}:${kibana_port}/api/saved_objects/config/${kibana_version}?overwrite=true" \
    -d@"${kibana_file_dir}/sof-elk_config.json"

# increase the recovery priority for the kibana index so we don't have to wait to use it upon recovery
if [ -z "${kibana_index}" ] || [ "${kibana_index}" = "error" ]; then
    echo "WARNING: could not resolve concrete ${kibana_alias} index name; skipping recovery priority bump" >&2
else
    echo "Increasing Kibana index recovery priority (${kibana_index})"
    do_curl "Kibana index priority" \
        -H 'kbn-xsrf: true' -H 'Content-Type: application/json' \
        -X PUT "http://${es_host}:${es_port}/${kibana_index}/_settings" \
        -d '{ "settings": {"index": {"priority": 100 }}}'
fi

# replace data_views
# these must be inserted FIRST becuase they are the basis for the other stored objects' references
for dataviewfile in ${kibana_file_dir}/data_views/*.json ; do
    DATAVIEWID=$( basename ${dataviewfile} .json )
    echo "Loading Data View: ${DATAVIEWID}"

    # replace the data_view object
    # delete is expected to 404 on first run, so don't warn on that one
    curl -s -H 'kbn-xsrf: true' -H 'Content-Type: application/json' \
        -X DELETE "http://${kibana_host}:${kibana_port}/api/data_views/data_view/${DATAVIEWID}" > /dev/null
    do_curl "data view ${DATAVIEWID}" \
        -H 'kbn-xsrf: true' -H 'Content-Type: application/json' \
        -X POST "http://${kibana_host}:${kibana_port}/api/data_views/data_view" \
        -d@"${dataviewfile}"
done

# insert/update dashboards, visualizations, maps, and searches
# ORDER MATTERS!!! dependencies in the "references" field will cause failure to insert if the references are not already present
TMPNDJSONFILE=$( mktemp --suffix=.ndjson )
trap 'rm -f "${TMPNDJSONFILE}"' EXIT

for objecttype in visualization lens map search dashboard; do
    echo "Preparing objects: ${objecttype}"
    for objectfile in ${kibana_file_dir}/${objecttype}/*.json; do
        jq -c '.' "${objectfile}" >> ${TMPNDJSONFILE} || echo "WARNING: failed to parse ${objectfile}" >&2
    done
done

echo "Loading objects in bulk"
do_curl "bulk saved-object import" \
    -H 'kbn-xsrf: true' \
    --form file=@"${TMPNDJSONFILE}" \
    -X POST "http://${kibana_host}:${kibana_port}/api/saved_objects/_import?overwrite=true"
