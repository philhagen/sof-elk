#!/bin/bash
# SOF-ELK® Supporting script
# (C)2018 Lewes Technology Consulting, LLC
#
# This script is used to load all dashboards, visualizations, saved searches, and index patterns to Elasticsearch

[ -r /etc/sysconfig/sof-elk ] && . /etc/sysconfig/sof-elk

ARGC=$#

es_host=localhost
es_port=9200
kibana_host=localhost
kibana_port=5601
kibana_index=.kibana

kibana_version=$( jq -r '.version' < /usr/share/kibana/package.json )
kibana_build=$(jq -r '.build.number' < /usr/share/kibana/package.json )

dashboard_dir="/usr/local/sof-elk/dashboards/"

# enter a holding pattern until the elasticsearch server is available, but don't wait too long
max_wait=60
wait_step=0
interval=5
until curl -s -XGET http://${es_host}:${es_port}/_cluster/health > /dev/null ; do
    wait_step=$(( ${wait_step} + ${interval} ))
    if [ ${wait_step} -gt ${max_wait} ]; then
        echo "ERROR: elasticsearch server not available for more than ${max_wait} seconds."
        exit 5
    fi
    sleep ${interval};
done

# re-insert all ES templates in case anything has changed
# this will not change existing mappings, just new indexes as they are created
# (And why-oh-why isn't this handled by "template_overwrite = true" in the logstash output section?!?!?!?!)
for es_template in $( ls -1 /usr/local/sof-elk/lib/elasticsearch-*-template.json | sed 's/.*elasticsearch-\(.*\)-template.json/\1/' ); do
    curl -s -XPUT -H 'Content-Type: application/json' http://${es_host}:${es_port}/_template/${es_template} -d @/usr/local/sof-elk/lib/elasticsearch-${es_template}-template.json > /dev/null
done

# set the default index pattern, time zone, and add TZ offset to the default date format 
curl -s -XPOST -H 'Content-Type: application/json' http://${es_host}:${es_port}/${kibana_index}/doc/config:${kibana_version} -d "{\"config\": {\"buildNum\": ${kibana_build}, \"telemetry:optIn\": false, \"defaultIndex\": \"logstash\", \"dateFormat\": \"YYYY-MM-DD HH:mm:ss.SSS Z\", \"dateFormat:tz\": \"Etc/UTC\"}}" > /dev/null

# increase the recovery priority for the kibana index so we don't have to wait to use it upon recovery
curl -s -XPUT -H 'Content-Type: application/json' http://${es_host}:${es_port}/${kibana_index}/_settings -d "{ \"settings\": {\"index\": {\"priority\": 100 }}}" > /dev/null

# create the dashboards, searches, and visualizations from files
# TODO: This will not handle if there are more than one index-pattern per dashboard.  I dont *think* this should ever happen, but may need more fine-grained control in the export/import process
for dashboardfile in ${dashboard_dir}/*.json; do
    DASHID=$( basename ${dashboardfile} | cut -d \. -f 1 )
    FIELDFILE=${dashboard_dir}/${DASHID}_fields.txt
    FIELDFORMATFILE=${dashboard_dir}/${DASHID}_fieldFormatMap.txt

    if [ -f ${FIELDFILE} ]; then
        TMPDASH=$( mktemp )
        NEWFIELDS=$( cat ${FIELDFILE} |sed '1s/^/[/; $!s/$/,/; $s/$/]/' | jq -scR '.' )

        if [ -f ${FIELDFORMATFILE} ]; then
            NEWFIELDFORMATMAP=$( cat ${FIELDFORMATFILE} | jq -c '.' )
            cat ${dashboardfile} | jq --argjson newfields "$NEWFIELDS" --arg newfieldformatmap "$NEWFIELDFORMATMAP" '(.objects[] | select(.type == "index-pattern").attributes.fields) |= $newfields | (.objects[] | select(.type == "index-pattern").attributes.fieldFormatMap) |= $newfieldformatmap' > ${TMPDASH}
        else
            cat ${dashboardfile} | jq --argjson newfields "$NEWFIELDS"  '(.objects[] | select(.type == "index-pattern").attributes.fields) |= $newfields' > ${TMPDASH} > /dev/null
        fi

        curl -s -XPOST "http://${kibana_host}:${kibana_port}/api/kibana/dashboards/import?force=true" -H "kbn-xsrf:true" -H "Content-type:application/json" -d @${TMPDASH} > /dev/null
        rm -f ${TMPDASH}

    else
        curl -s -XPOST "http://${kibana_host}:${kibana_port}/api/kibana/dashboards/import?force=true" -H "kbn-xsrf:true" -H "Content-type:application/json" -d @${dashboardfile} > /dev/null
    fi

# NEWFIELDS=$( cat 99d1b510-72b3-11e8-9159-894bd7d62352_fields.txt |sed '1s/^/[/; $!s/$/,/; $s/$/]/' | jq -scR '.' )
# NEWFIELDFORMATMAP=': FF=$( cat 99d1b510-72b3-11e8-9159-894bd7d62352_fieldFormatMap.txt|jq -c '.' )
# old way: cat 99d1b510-72b3-11e8-9159-894bd7d62352.json |jq --argjson newfields "$NEWFIELDS"  '(.objects) |= (map((if .type == "index-pattern" then .attributes.fields=$newfields else . end)))'|less
# jq 1.5+ way: cat 99d1b510-72b3-11e8-9159-894bd7d62352.json |jq --argjson newfields "$NEWFIELDS"  '(.objects[] | select(.type == "index-pattern").attributes.fields) |= $newfields' | less
#              cat 99d1b510-72b3-11e8-9159-894bd7d62352.json | jq --arg newfieldformatmap "$NEWFIELDFORMATMAP" '(.objects[] | select(.type == "index-pattern").attributes.fieldFormatMap) |= $newfieldformatmap'
# for both:
# cat 99d1b510-72b3-11e8-9159-894bd7d62352.json |jq --argjson newfields "$NEWFIELDS" --arg newfieldformatmap "$NEWFIELDFORMATMAP" '(.objects[] | select(.type == "index-pattern").attributes.fields) |= $newfields | (.objects[] | select(.type == "index-pattern").attributes.fieldFormatMap) |= $newfieldformatmap' | less


    #curl -s -XPOST "http://${kibana_host}:${kibana_port}/api/kibana/dashboards/import?force=true" -H "kbn-xsrf:true" -H "Content-type:application/json" -d @${dashboardfile} > /dev/null
done

# # prevent this script from automatically running again on next boot
# # ignore this if being forced
# if [ ${FORCE} != "force" ]; then
#     TMPFILE=$( mktemp )
#     grep -v ^reset_dashboards /etc/sysconfig/sof-elk > ${TMPFILE}
#     echo "reset_dashboards=0" >> ${TMPFILE}
#     cat ${TMPFILE} > /etc/sysconfig/sof-elk
#     rm -f ${TMPFILE}
# fi
