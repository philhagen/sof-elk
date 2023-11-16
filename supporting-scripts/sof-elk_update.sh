#!/bin/bash
# SOF-ELK® Supporting script
# (C)2019 Lewes Technology Consulting, LLC
#
# This script is used to update the repository from its git origin
# It will not overwrite any local changes unless -force is specified

FORCE=0

if [[ $EUID -ne 0 ]]; then
    echo "This script must be run as root.  Exiting."
    exit 1
fi

# parse any command line arguments
if [ $# -gt 0 ]; then
    while true; do
        if [ $1 ]; then
            if [ $1 == '-force' ]; then
                FORCE=1
            fi
            shift
        else
            break
        fi
    done
fi

cd /usr/local/sof-elk/
if [[ $( git status --porcelain ) && $FORCE -eq 0 ]]; then
    echo "ERROR: You have local changes to this repository - will not overwrite without '-force'."
    echo "       Run 'git status' from the /usr/local/sof-elk/ directory to identify the local changes."
    echo "       Note that using '-force' will delete any modifications that have been made in this directory."
    exit 2
fi

/usr/local/sof-elk/supporting-scripts/git-remote-update.sh -now
# This method adapted from method here: https://stackoverflow.com/a/3278427
LOCAL=$(git rev-parse @{0})
REMOTE=$(git rev-parse @{u})
BASE=$(git merge-base @{0} @{u})

if [[ $LOCAL = $REMOTE ]]; then
    echo "Up-to-date"

elif [[ $LOCAL = $BASE ]]; then
    # Need to pull
    git reset --hard > /dev/null
    git clean -fdx > /dev/null
    git pull origin

    /usr/local/sof-elk/supporting-scripts/git-remote-update.sh -now
    for lspid in $( ps -u logstash | grep java | awk '{print $1}' ); do
        kill -s HUP $lspid
    done

elif [[ $REMOTE = $BASE ]]; then
    echo "Need to push - this should never happen"

else
    echo "Diverged - this should never happen"
fi