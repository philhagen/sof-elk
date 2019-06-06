#!/bin/bash
# SOF-ELK® Supporting script
# (C)2019 Lewes Technology Consulting, LLC
#
# This script will apply settings to elasticsearch indices when run

es_host=localhost
es_port=9200
NUMBER_OF_REPLICAS=0
INDEX_LIST="filefolderaccess filesystem httpdlog lnkfiles logstash netflow"

[ -r /etc/sysconfig/sof-elk ] && . /etc/sysconfig/sof-elk

# set replica count
for index in $INDEX_LIST; do
	curl -s -H 'kbn-xsrf: true' -H 'Content-Type: application/json' -X PUT "http://${es_host}:${es_port}/${index}-*/_settings" -d"{ \"index\": { \"number_of_replicas\": ${NUMBER_OF_REPLICAS} } }" > /dev/null 2>&1
done