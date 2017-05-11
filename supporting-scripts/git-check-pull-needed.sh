#!/bin/bash
# SOF-ELK Supporting script
# (C)2017 Lewes Technology Consulting, LLC
#
# This script displays a message to STDOUT if the origin has a newer version than the local checkout

cd /usr/local/sof-elk/

UPSTREAM=${1:-'@{u}'}
LOCAL=$(git rev-parse @{0})
REMOTE=$(git rev-parse "$UPSTREAM")
BASE=$(git merge-base @{0} "$UPSTREAM")

if [ $LOCAL = $REMOTE ]; then
    # up to date, nothing to do
    exit 0

elif [ $LOCAL = $BASE ]; then
    echo "Upstream Updates Available!!!!"
    echo "------------------------------"
    echo
    echo "There are upstream updates to the SOF-ELK configuration files available in the Github repository." 
    echo "These are not required, but if desired, run the following to retrieve:"
    echo
    echo "sudo sof-elk_update.sh"
    echo
    exit 0

elif [ $REMOTE = $BASE ]; then
    # this should never happen - local copies won't push to origin
    exit 1

else
    # there should be no other case - this means some weird error occurred in gathering the SHA hashes
    exit 1

fi
