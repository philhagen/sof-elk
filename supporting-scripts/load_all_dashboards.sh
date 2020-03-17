#!/bin/bash
# SOF-ELK® Supporting script
# (C)2020 Lewes Technology Consulting, LLC
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

# set the default index pattern, time zone, and add TZ offset to the default date format 
curl -s -H 'kbn-xsrf: true' -H 'Content-Type: application/json' -X POST http://${es_host}:${es_port}/${kibana_index}/_doc/config:${kibana_version} -d "{\"config\": {\"buildNum\": ${kibana_build}, \"telemetry:optIn\": false, \"defaultIndex\": \"logstash\", \"dateFormat\": \"YYYY-MM-DD HH:mm:ss.SSS Z\", \"dateFormat:tz\": \"UTC\"}}" > /dev/null

# increase the recovery priority for the kibana index so we don't have to wait to use it upon recovery
curl -s -H 'kbn-xsrf: true' -H 'Content-Type: application/json' -X PUT http://${es_host}:${es_port}/${kibana_index}/_settings -d "{ \"settings\": {\"index\": {\"priority\": 100 }}}" > /dev/null

# insert/update dashboard definitions
for dashboardfile in ${kibana_file_dir}/dashboard/*.json; do
    DASHID=$( basename ${dashboardfile} | sed -e 's/\.json$//' )

    curl -s -H 'kbn-xsrf: true' -H 'Content-Type: application/json' -X POST "http://${kibana_host}:${kibana_port}/api/saved_objects/dashboard/${DASHID}?overwrite=true" -d @${dashboardfile} > /dev/null
done

# insert/update visualization definitions
for visualizationfile in ${kibana_file_dir}/visualization/*.json; do
    VISUALIZATIONID=$( basename ${visualizationfile} | sed -e 's/\.json$//' )

    curl -s -H 'kbn-xsrf: true' -H 'Content-Type: application/json' -X POST "http://${kibana_host}:${kibana_port}/api/saved_objects/visualization/${VISUALIZATIONID}?overwrite=true" -d @${visualizationfile} > /dev/null
done

# insert/update search definitions
for searchfile in ${kibana_file_dir}/search/*.json; do
    SEARCHID=$( basename ${searchfile} | sed -e 's/\.json$//' )

    curl -s -H 'kbn-xsrf: true' -H 'Content-Type: application/json' -X POST "http://${kibana_host}:${kibana_port}/api/saved_objects/search/${SEARCHID}?overwrite=true" -d @${searchfile} > /dev/null
done

for indexpatternfile in ${kibana_file_dir}/index-pattern/*.json; do
    INDEXPATTERNID=$( basename ${indexpatternfile} | sed -e 's/\.json$//' )

    # create a temp file to hold the reconstructed index-pattern
    TMPFILE=$( mktemp )

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

    if [ ${fieldformatmap} == 1 ]; then
       cat ${indexpatternfile} | jq --arg fields "$( cat ${kibana_file_dir}/index-pattern/fields/${INDEXPATTERNID}.json | jq -sc '.' )" --arg fieldformatmap "$( cat ${kibana_file_dir}/index-pattern/fieldformats/${INDEXPATTERNID}.json | jq -c 'from_entries' )" '.attributes += { fields: $fields, fieldFormatMap: $fieldformatmap }' > ${TMPFILE}

    else
        # TODO: there should always be fields - assuming that is the case here
        cat ${indexpatternfile} | jq --arg fields "$( cat ${kibana_file_dir}/index-pattern/fields/${INDEXPATTERNID}.json | jq -sc '.' )" '.attributes += { fields: $fields }' > ${TMPFILE}
    fi

    # if for some strange reason the index-mapping object does not yet exist, create it
    if [ $( curl -s -H 'kbn-xsrf: true' -w '%{http_code}' -o /dev/null -X GET "http://${kibana_host}:${kibana_port}/api/saved_objects/index-pattern/${INDEXPATTERNID}" ) == 404 ]; then
        curl -s -H 'kbn-xsrf: true' -H 'Content-Type: application/json' -X POST "http://${kibana_host}:${kibana_port}/api/saved_objects/index-pattern/${INDEXPATTERNID}" -d @${kibana_file_dir}/index-pattern/${INDEXPATTERNID}.json > /dev/null
    fi

    # update the index-mapping object
    # NOTE! This will change with Elastic 7 TODO: Fix this when that upgrade occurs.... will need to revalidate all the APIs of course
    curl -s -H 'kbn-xsrf: true' -H 'Content-Type: application/json' -X PUT "http://${kibana_host}:${kibana_port}/api/saved_objects/index-pattern/${INDEXPATTERNID}?overwrite=true" -d @${TMPFILE} > /dev/null

    # remove the temp file
    rm -f ${TMPFILE}
done