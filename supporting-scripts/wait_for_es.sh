#!/bin/bash
# SOF-ELK® Supporting script
# (C)2026 Lewes Technology Consulting, LLC
#
# This script will wait for elasticsearch to be available, preventing silly kibana errors in the browser

eshost=127.0.0.1
esport=9200
maxwait=60
waited=0

status=""
while [[ "${status}" != "green" ]]; do
	status=$( curl --silent --fail "http://${eshost}:${esport}/_cluster/health" | jq -r '.status' )
    if [[ "${status}" == "green" ]]; then
        break
    fi
	sleep 1
	echo -n '.'

	waited=$(( waited + 1 ))
    if [[ "${waited}" -ge "${maxwait}" ]]; then
        echo
        echo "ERROR: elasticsearch did not reach green status after ${maxwait} seconds." >&2
        exit 1
    fi
done
echo
