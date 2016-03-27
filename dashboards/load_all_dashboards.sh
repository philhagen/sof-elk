#!/bin/bash

[ -r /etc/sysconfig/for572/elk_checkout ] && . /etc/sysconfig/for572/elk_checkout

if [ $reset_dashboards -ne 1 ] ; then
    exit 2
fi

es_host=localhost
es_port=9200
kibana_index=.kibana
dashboard_list="httpd introductory netflow syslog"
dashboard_dir="/usr/local/for572logstash/dashboards/"

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