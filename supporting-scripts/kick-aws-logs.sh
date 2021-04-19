#!/bin/bash
# SOF-ELK® Supporting script
# (C)2021 Lewes Technology Consulting, LLC
#
# This script will add a newline to any *.json file under /logstash/aws/ if it doesn't already have one.
# This is utterly absurd but AWS CloudTrail logs place all Records on one line within in JSON array and no newline charater.
# That treachery results in filebeat's reasonable line-based logic never seeing a file as "ready to read".

find /logstash/aws/ -type f -print0 | xargs -0 -L1 bash -c 'test "$(tail -c 1 "$0")" && echo >> $0'
