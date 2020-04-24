#!/bin/bash
# SOF-ELK® Supporting script
# (C)2018 Lewes Technology Consulting, LLC
#
# This script will wait for elasticsearch to be available, preventing silly kibana errors in the browser

eshost=127.0.0.1
esport=9200

while ! curl --output /dev/null --silent --head --fail http://${eshost}:${esport}; do
	sleep 1 && echo -n '.'
done
