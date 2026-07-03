#!/bin/bash
# SOF-ELK® Supporting script
# (C)2026 Lewes Technology Consulting, LLC
#
# This script displays a message to STDOUT if the origin has a newer version than the local checkout

vm_update_status_file=/var/run/sof-elk_vm_update

functions_include="/usr/local/sof-elk/supporting-scripts/functions.sh"
if [ -f "${functions_include}" ]; then
    . "${functions_include}"
else
    echo "${functions_include} not present.  Exiting " 1>&2
    exit 1
fi

cd /usr/local/sof-elk/ || exit 2

UPSTREAM=${1:-'@{u}'}
LOCAL=$(git rev-parse @{0} 2> /dev/null)
REMOTE=$(git rev-parse "$UPSTREAM" 2> /dev/null)
BASE=$(git merge-base @{0} "$UPSTREAM" 2> /dev/null)

if [ "${LOCAL}" = "${REMOTE}" ]; then
    # up to date, nothing to do (":" is the bash noop)
    :

elif [ "${LOCAL}" = "${BASE}" ]; then
    echo "Upstream Updates Available!!!!"
    echo "------------------------------"
    echo
    echo "There are upstream updates to the SOF-ELK® configuration files available"
    echo "in the Github repository. These are not required, but if desired,"
    echo "run the following command to retrieve and activate them:"
    echo
    echo "sudo sof-elk_update.sh"
    echo

elif [ "${REMOTE}" = "${BASE}" ]; then
    # this should never happen - local copies won't push to origin
    echoerr "ERROR: You have local commits that are past the Github-based origin."
    echoerr "       Automatic updates not possible."

else
    # there should be no other case - this means some weird error occurred in gathering the SHA hashes
    echoerr "ERROR: Something very unexpected occurred when determining if there are any"
    echoerr "       upstream updates. Ensure you have Internet connectivity and please"
    echoerr "       try again later."
fi

if [ -f "${vm_update_status_file}" ]; then
    echo "A new version of the SOF-ELK VM is available!!!"
    echo "-----------------------------------------------"
    echo
    echo "There is a new VM version available for download. Please see the release"
    echo "information at https://for572.com/sof-elk-readme"
    echo
fi
