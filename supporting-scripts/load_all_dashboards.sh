#!/bin/bash
# SOF-ELK® Supporting script
# (C)2016 Lewes Technology Consulting, LLC
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

# set the default index pattern, time zone, and add TZ offset to the default date format 
curl -s -XPOST -H 'Content-Type: application/json' http://${es_host}:${es_port}/${kibana_index}/doc/config:${kibana_version} -d "{\"config\": {\"buildNum\": ${kibana_build}, \"defaultIndex\": \"logstash\", \"dateFormat:tz\": \"Etc/UTC\", \"dateFormat\": \"MMMM Do YYYY, HH:mm:ss.SSS Z\"}}" > /dev/null

# increase the recovery priority for the kibana index so we don't have to wait to use it upon recovery
curl -s -XPUT -H 'Content-Type: application/json' http://${es_host}:${es_port}/${kibana_index}/_settings -d "{ \"settings\": {\"index\": {\"priority\": 100 }}}" > /dev/null

# re-insert all ES templates in case anything has changed
# this will not change existing mappings, just new indexes as they are created
# (And why-oh-why isn't this handled by "template_overwrite = true" in the logstash output section?!?!?!?!)
for es_template in $( ls -1 /usr/local/sof-elk/lib/elasticsearch-*-template.json | sed 's/.*elasticsearch-\(.*\)-template.json/\1/' ); do
    curl -s -XPUT -H 'Content-Type: application/json' http://${es_host}:${es_port}/_template/${es_template} -d @/usr/local/sof-elk/lib/elasticsearch-${es_template}-template.json > /dev/null
done

# create the dashboards, searches, and visualizations from files
for dashboardfile in ${dashboard_dir}/*.json; do
    curl -s -XPOST 'http://${kibana_host}:${kibana_port}/api/kibana/dashboards/import?force=true' -H 'kbn-xsrf:true' -H 'Content-type:application/json' -d @$dashboardfile > /dev/null
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
