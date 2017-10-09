#!/bin/bash
# SOF-ELK® Supporting script
# (C)2017 Lewes Technology Consulting, LLC
#
# This script is used to update the origin for the SOF-ELK® repository files
RUNNOW=0

# parse any command line arguments
if [ $# -gt 0 ]; then
    while true; do
        if [ $1 ]; then
            if [ $1 == '-now' ]; then
                RUNNOW=1
            fi
            shift
        else
            break
        fi
    done
fi

if [[ $EUID -ne 0 ]]; then
    echo "This script must be run as root.  Exiting."
    exit 1
fi

if [ $RUNNOW -eq 0 ]; then
    # wait up to 20min to start, so all these VMs don't hit the server at the same exact time
    randomNumber=$RANDOM
    let "randomNumber %= 1800"
    sleep ${randomNumber}
fi

cd /usr/local/sof-elk/
git remote update > /dev/null 2>&1
