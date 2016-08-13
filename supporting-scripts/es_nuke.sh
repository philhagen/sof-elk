#!/bin/sh
# NUKE ALL data in elasticsearch.  This is incredibly destructive!

# source function library
. /etc/rc.d/init.d/functions

sourceloc=/usr/local/logstash-*

ARGC=$#

if [ ${ARGC} -ne 1 ]; then
    echo "ERROR: This script takes exactly one argument - the basename of the index to delete."
    echo "       Basename of index is something like 'syslog', 'netflow', or 'httpdlog'"
    echo "Exiting."
    exit 2
fi

BASEINDEX=$1
# If you provided the index including the value after the dash, don't append a -*
if [ "`echo $BASEINDEX | grep -v '\-'`" ]; then
  BASEINDEX="$BASEINDEX-*"
fi
DOCCOUNT=$(curl -s http://localhost:9200/${BASEINDEX}/_count | jq -e '.count')
if [ $? == 1 ]; then
  DOCCOUNT=0
fi

if [ ${DOCCOUNT} -eq 0 ]; then
    echo -e "There are no documents in the '\e[1m${BASEINDEX}\e[0m' indices."
    echo "Exiting."
    exit
fi

echo "WARNING!!  THIS COMMAND CAN DESTROY DATA!  READ CAREFULY!"
echo "---------------------------------------------------------"
echo "This script will permanently delete data from the elasticsearch server."
echo
echo -e "There are currently \e[1m${DOCCOUNT}\e[0m documents in the '\e[1m${BASEINDEX}\e[0m' indices."

echo
echo -e "To delete the '\e[1m${BASEINDEX}\e[0m' indices from the server, type \"\e[1mYES\e[0m\" below and press return."
read RESPONSE

if [ ${RESPONSE} != "YES" ]; then
    echo "Not deleting anything without explicit confirmation."
    exit
else
    echo -n "Deleting all data from the '${BASEINDEX} indices: "
    curl -s -XDELETE "http://localhost:9200/${BASEINDEX}" > /dev/null && success || failure
    echo

    echo
    echo "NOTE: This script does not delete the 'sincedb' file, which tracks progress through existing"
    echo "  log files. If you want to re-parse existing files, you'll need to run the following command:"
    echo "sudo ls_restart.sh -reparse"
    echo
fi
