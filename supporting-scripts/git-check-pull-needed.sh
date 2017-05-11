#!/bin/bash

UPSTREAM=${1:-'@{u}'}
LOCAL=$(git rev-parse @{0})
REMOTE=$(git rev-parse "$UPSTREAM")
BASE=$(git merge-base @{0} "$UPSTREAM")

if [ $LOCAL = $REMOTE ]; then
    # up to date, nothing to do
    exit 0

elif [ $LOCAL = $BASE ]; then
    echo "Updates to the SOF-ELK configuration files are available!"
    echo "These are not required, but if desired, run the following to retrieve:"
    echo
    echo "sudo sof-elk_update.sh"
    exit 0

elif [ $REMOTE = $BASE ]; then
    # this should never happen - local copies won't push to origin
    exit 1

else
    # there should be no other case - this means some weird error occurred in gathering the SHA hashes
    exit 1

fi
