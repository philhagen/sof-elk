#!/bin/bash
# SOF-ELK® Supporting script
# (C)2026 Lewes Technology Consulting, LLC
#
# This script is read at login time (local and remote) for the elk_user user account
# it's designed to display useful stuff for the user

[ -r /etc/lsb-release ] && . /etc/lsb-release

if [ -z "${DISTRIB_DESCRIPTION}" ] && [ -x /usr/bin/lsb_release ]; then
	# Fall back to using the very slow lsb_release utility
	if ! DISTRIB_DESCRIPTION=$(lsb_release -s -d); then
		DISTRIB_DESCRIPTION="UNKNOWN DISTRIBUTION"
	fi
fi

BRANCH=$(cd /usr/local/sof-elk 2> /dev/null && git rev-parse --abbrev-ref HEAD 2> /dev/null)

PATH=$PATH:/usr/local/sof-elk/supporting-scripts
export PATH

echo
echo "Welcome to the SOF-ELK® Distribution"
printf "Built on %s (%s %s %s)\n" "${DISTRIB_DESCRIPTION}" "$(uname -o)" "$(uname -r)" "$(uname -m)"
if [ -n "${BRANCH}" ]; then
	printf "Running on the '%s' branch\n" "${BRANCH}"
else
	echo "Could not determine which branch is active - possible error condition"
fi
echo "--------------------------------------"
echo "Here are some useful commands:"
echo "  sof-elk_clear.py"
echo "    Forcibly removes all records from the Elasticsearch index."
echo "    Use '-h' for usage."
echo "  load_all_dashboards.sh"
echo "    Resets all Kibana dashboards to the versions on disk in the"
echo "    /usr/local/sof-elk/ directory."
echo

if [ -x /usr/local/sof-elk/supporting-scripts/git-check-pull-needed.sh ]; then
    /usr/local/sof-elk/supporting-scripts/git-check-pull-needed.sh
fi
