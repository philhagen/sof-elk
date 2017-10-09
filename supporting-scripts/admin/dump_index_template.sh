#!/bin/bash
# SOF-ELK® Supporting script
# (C)2017 Lewes Technology Consulting, LLC
#
# This script prints the template requested on the commandline on STDOUT

curl -s -XGET "http://localhost:9200/_template/$1"
