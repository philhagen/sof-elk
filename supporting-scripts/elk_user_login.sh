#!/bin/bash
# SOF-ELK Supporting script
# (C)2016 Lewes Technology Consulting, LLC
#
# This script is read at login time (local and remote) for the elk_user user account
# it's designed to display useful stuff for the user/student

echo
echo "Welcome to the SOF-ELK VM Distribution"
echo "--------------------------------------"
echo "Here are some useful commands:"
echo "  sof-elk_clear.py"
echo "    Forcibly removes all records from the Elasticsearch index.  Use '-h' for usage."
echo "  load_all_dashboards.sh"
echo "    Resets all Kibana dashboards to the versions on disk in /usr/local/sof-elk/"

echo

/usr/local/sof-elk/supporting_scripts/git-check-pull-needed.sh
