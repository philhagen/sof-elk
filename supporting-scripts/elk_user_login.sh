#!/bin/bash
# this script is read at login time (local and remote) for the elk_user user account
# it's designed to display useful stuff for the user/student

echo
echo "Welcome to the SOF-ELK VM Distribution"
echo "--------------------------------------"
echo "Here are some useful commands:"
echo "  es_nuke.sh <indexname>"
echo "    Forcibly removes all records from the <indexname> Elasticsearch index"
echo "  sudo ls_restart.sh"
echo "    Restart the logstash parser service, re"
echo "  load_all_dashboards.sh"
echo "    Resets all Kibana dashboards to the versions on disk in /usr/local/sof-elk/"