#!/bin/bash
SLEEP=$((RANDOM % 3600))
sleep $SLEEP
cd /usr/local/sof-elk
git remote update
