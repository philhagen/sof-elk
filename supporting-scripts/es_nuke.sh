#!/bin/sh
# stop logstash, NUKE ALL data in elasticsearch, remove the sincedb, restart logstash
# this is incredibly destructive!

# source function library
. /etc/rc.d/init.d/functions

sourceloc=/usr/local/logstash-*
sincedb=/var/db/logstash/sincedb

ARGC=$#

if [ ${ARGC} -ne 1 ]; then
    echo "ERROR: This script takes exactly one argument - the basename of the index to delete."
    echo "       Basename of index is something like 'syslog', 'netflow', or 'httpdlog'"
    echo "Exiting."
    exit 2
fi

BASEINDEX=$1

echo "WARNING!!  THIS COMMAND CAN DESTROY DATA!  READ CAREFULY!"
echo "---------------------------------------------------------"
echo "This script will permanently delete data from the elasticsearch server."
echo
echo "To delete all of the '${BASEINDEX}' indices from the server, type \"YES\" below and press return."
read RESPONSE

if [ ${RESPONSE} != "YES" ]; then
    echo "Not deleting anything without explicit confirmation."
    exit
else
    echo -n "Deleting all data from the ${BASEINDEX}-* indices: "
    curl -s -XDELETE "http://localhost:9200/${BASEINDEX}-*" > /dev/null && success || failure
fi