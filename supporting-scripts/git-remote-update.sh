#!/bin/bash

if [[ $EUID -ne 0 ]]; then
    echo "This script must be run as root.  Exiting."
    exit 1
fi

SLEEP=$((RANDOM % 3600))
sleep $SLEEP
cd /usr/local/sof-elk
git remote update
