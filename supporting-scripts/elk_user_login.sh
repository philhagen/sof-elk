#!/bin/bash
# SOF-ELK® Supporting script
# (C)20124 Lewes Technology Consulting, LLC
#
# This script is read at login time (local and remote) for the elk_user user account
# it's designed to display useful stuff for the user/student

[ -r /etc/lsb-release ] && . /etc/lsb-release

if [ -z "$DISTRIB_DESCRIPTION" ] && [ -x /usr/bin/lsb_release ]; then
	# Fall back to using the very slow lsb_release utility
	DISTRIB_DESCRIPTION=$(lsb_release -s -d)
fi

echo
echo "Welcome to the SOF-ELK® VM Distribution"
printf "Built on %s (%s %s %s)\n" "$DISTRIB_DESCRIPTION" "$(uname -o)" "$(uname -r)" "$(uname -m)"
echo "--------------------------------------"
echo "Here are some useful commands:"
echo "  sof-elk_clear.py"
echo "    Forcibly removes all records from the Elasticsearch index."
echo "    Use '-h' for usage."
echo "  load_all_dashboards.sh"
echo "    Resets all Kibana dashboards to the versions on disk in the"
echo "    /usr/local/sof-elk/ directory."
echo

/usr/local/sof-elk/supporting-scripts/git-check-pull-needed.sh

PATH=$PATH:/usr/local/sof-elk/supporting-scripts
export PATH