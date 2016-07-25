#!/bin/bash
# SOF-ELK Supporting script
# (C)2016 Lewes Technology Consulting, LLC
#
# This script is used to restart the logstash service, clearing the sincedb if -reparse is specified

REPARSE=0

# parse any command line arguments
if [ $# -gt 0 ]; then
    while true; do
        if [ $1 ]; then
            if [ $1 == '-reparse' ]; then
                REPARSE=1
            fi
            shift
        else
            break
        fi
    done
fi

/usr/bin/systemctl stop logstash.service
if [ $REPARSE -eq 1 ]; then
    rm -f /var/db/logstash/sincedb
fi
/usr/bin/systemctl start logstash.service