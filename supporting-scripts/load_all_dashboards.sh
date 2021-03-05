#!/bin/bash
# SOF-ELK® Supporting script
# (C)2021 Lewes Technology Consulting, LLC
#
# This script is used to load all dashboards, visualizations, saved searches, and index patterns to Kibana

# set defaults
es_host=localhost
es_port=9200
kibana_host=localhost
kibana_port=5601
kibana_index=.kibana
kibana_file_dir="/usr/local/sof-elk/kibana/"

[ -r /etc/sysconfig/sof-elk ] && . /etc/sysconfig/sof-elk

kibana_version=$( jq -r '.version' < /usr/share/kibana/package.json )
kibana_build=$(jq -r '.build.number' < /usr/share/kibana/package.json )

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

# re-insert all ES templates in case anything has changed
# this will not change existing mappings, just new indexes as they are created
# (And why-oh-why isn't this handled by "template_overwrite = true" in the logstash output section?!?!?!?!)
for es_template_file in $( ls -1 /usr/local/sof-elk/lib/elasticsearch-*-template.json ); do
    es_template=$( echo $es_template_file | sed 's/.*elasticsearch-\(.*\)-template.json/\1/' )
    curl -s -H 'kbn-xsrf: true' -H 'Content-Type: application/json' -X PUT http://${es_host}:${es_port}/_template/${es_template} -d @${es_template_file} > /dev/null
done

# set the default index pattern, time zone, and add TZ offset to the default date format, and other custom Kibana settings
curl -s -H 'kbn-xsrf: true' -H 'Content-Type: application/json' -X POST http://${es_host}:${es_port}/${kibana_index}/_doc/config:${kibana_version} -d @${kibana_file_dir}/sof-elk_config.json > /dev/null

# increase the recovery priority for the kibana index so we don't have to wait to use it upon recovery
curl -s -H 'kbn-xsrf: true' -H 'Content-Type: application/json' -X PUT http://${es_host}:${es_port}/${kibana_index}/_settings -d "{ \"settings\": {\"index\": {\"priority\": 100 }}}" > /dev/null

# replace index patterns
# these must be inserted FIRST becuase they are the basis for the other stored objects' references
for indexpatternfile in ${kibana_file_dir}/index-pattern/*.json; do
    INDEXPATTERNID=$( basename ${indexpatternfile} | sed -e 's/\.json$//' )

    # reconstruct the new index-pattern with the proper fields and fieldFormatMap values
    if [ -f ${kibana_file_dir}/index-pattern/fields/${INDEXPATTERNID}.json ]; then
        fields=1
    else
        fields=0
    fi
    if [ -f ${kibana_file_dir}/index-pattern/fieldformats/${INDEXPATTERNID}.json ]; then
        fieldformatmap=1
    else
        fieldformatmap=0
    fi

    # create temp files to hold the reconstructed index-pattern
    TMPFILE=$( mktemp )
    TMPNDJSONFILE=$( mktemp --suffix=.ndjson )

    cat ${indexpatternfile} | jq -c '.' > ${TMPNDJSONFILE}

    if [ ${fields} == 1 ]; then
        cat ${TMPNDJSONFILE} | jq -c --arg fields "$( cat ${kibana_file_dir}/index-pattern/fields/${INDEXPATTERNID}.json | jq -c '.' )" '.attributes += { fields: $fields }' > ${TMPFILE}
        cat ${TMPFILE} > ${TMPNDJSONFILE}
    fi
    if [ ${fieldformatmap} == 1 ]; then
        cat ${TMPNDJSONFILE} | jq -c --arg fieldformatmap "$( cat ${kibana_file_dir}/index-pattern/fieldformats/${INDEXPATTERNID}.json | jq -c '.' )" '.attributes += { fieldFormatMap: $fieldformatmap }' > ${TMPFILE}
        cat ${TMPFILE} > ${TMPNDJSONFILE}
    fi

    # update the index-mapping object
    curl -s -H 'kbn-xsrf: true' --form file=@${TMPNDJSONFILE} -X POST "http://${kibana_host}:${kibana_port}/api/saved_objects/_import?overwrite=true" > /dev/null

    # remove the temp files
    rm -f ${TMPFILE}
    rm -f ${TMPNDJSONFILE}
done

# insert/update dashboards, visualizations, maps, and searches
# ORDER MATTERS!!! dependencies in the "references" field will cause failure to insert if the references are not already present
TMPNDJSONFILE=$( mktemp --suffix=.ndjson )
for objecttype in visualization map search dashboard; do
    cat ${kibana_file_dir}/${objecttype}/*.json | jq -c '.' >> ${TMPNDJSONFILE}
done
curl -s -H 'kbn-xsrf: true' --form file=@${TMPNDJSONFILE} -X POST "http://${kibana_host}:${kibana_port}/api/saved_objects/_import?overwrite=true" > /dev/null
rm -f ${TMPNDJSONFILE}
