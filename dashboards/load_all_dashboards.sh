#!/bin/bash

[ -r /etc/sysconfig/for572/elk_checkout ] && . /etc/sysconfig/for572/elk_checkout

if [ $reset_dashboards -ne 1 ] ; then
    exit 2
fi

es_host=localhost
es_port=9200
kibana_index=.kibana

index_patterns="httpdlog netflow syslog"

kibana_version=$( jq -r '.version' < /opt/kibana/package.json )
kibana_build=$(jq -r '.build.number' < /opt/kibana/package.json )

dashboard_list="httpd introductory netflow syslog"
dashboard_dir="/usr/local/for572logstash/dashboards/"

# create the index patterns from files
for indexid in ${index_patterns}; do
    curl -s XDELETE http://${es_host}:${es_port}/${kibana_index}/index_pattern/${indexid}-* > /dev/null
    curl -s XPUT http://${es_host}:${es_port}/${kibana_index}/index_pattern/${indexid}-* -T ${dashboard_dir}/index-patterns/${indexid} > /dev/null
done

# set the default index pattern
curl -XPOST http://${es_host}:${es_port}/${kibana_index}/config/${kibana_version} -d "{\"buildNum\": ${kibana_build}, \"defaultIndex\": \"syslog-*\"}"
# create the dashboards, searches, and visualizations from files
for dashboard in ${dashboard_list}; do
    for type in ${dashboard_dir}${dashboard}/*; do
        type=$( basename $type )
        for object in ${dashboard_dir}${dashboard}/${type}/*; do
            object=$( basename ${object} )
            curl -s -XDELETE http://${es_host}:${es_port}/${kibana_index}/${type}/${object} > /dev/null
            curl -s -XPUT http://${es_host}:${es_port}/${kibana_index}/${type}/${object} -T ${dashboard_dir}${dashboard}/${type}/${object} > /dev/null
        done
    done
done