#!/bin/bash
# SOF-ELK® Supporting script
# (C)2025 Lewes Technology Consulting, LLC
#
# This script is used to update the repository from its git origin
# It will not overwrite any local changes unless -f (force) is specified

# include common functions
functions_include="/usr/local/sof-elk/supporting-scripts/functions.sh"
if [ -f ${functions_include} ]; then
    . ${functions_include}
else
    echo "${functions_include} not present.  Exiting " 1>&2
    exit 1
fi

# set default values
FORCE=0

# parse options
while getopts ":f" opt; do
    case "${opt}" in
        f) FORCE=1 ;;
        \?)
            echoerr "ERROR: Invalid option: -${OPTARG}."
            exit 2
            ;;
    esac
done

# quit if not running with admin privs
require_root

cd /usr/local/sof-elk/ || exit 3
if [[ $( git status --porcelain ) && $FORCE -eq 0 ]]; then
    echoerr "ERROR: You have local changes to this repository - will not overwrite without '-f' to force."
    echoerr "       Run 'git status' from the /usr/local/sof-elk/ directory to identify the local changes."
    echoerr "       Note that using '-f' will delete any modifications that have been made in this directory."
    exit 2
fi

/usr/local/sof-elk/supporting-scripts/git-remote-update.sh -now
# This method adapted from https://stackoverflow.com/a/3278427
LOCAL=$(git rev-parse "@{0}")
REMOTE=$(git rev-parse "@{u}")
BASE=$(git merge-base "@{0}" "@{u}")

if [[ "${LOCAL}" == "${REMOTE}" ]]; then
    echo "Up-to-date"

elif [[ "${LOCAL}" == "${BASE}" ]]; then
    # Need to pull
    git reset --hard > /dev/null
    git clean -fdx > /dev/null
    git pull origin

    /usr/local/sof-elk/supporting-scripts/git-remote-update.sh -now
    for lspid in $( pgrep -u logstash java ); do
        kill -s HUP "${lspid}"
    done

elif [[ "${REMOTE}" == "${BASE}" ]]; then
    echo "Need to push - this should never happen"

else
    echo "Diverged - this should never happen"
fi
