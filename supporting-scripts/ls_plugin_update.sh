#!/bin/bash
# SOF-ELK® Supporting script
# (C)2024 Lewes Technology Consulting, LLC
#
# This script is run after logstash installs or updates

# core concepts/syntax from: https://github.com/jjfalling/update-elasticsearch-plugins
set -e

PLUGINBIN=/usr/share/logstash/bin/logstash-plugin

lsplugins="logstash-input-relp logstash-input-google_pubsub logstash-filter-tld logstash-filter-json_encode logstash-filter-cidr"

for lsplugin in ${lsplugins}; do
	$PLUGINBIN install ${lsplugin}
done
