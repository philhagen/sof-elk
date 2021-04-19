#!/bin/bash
# SOF-ELK® Supporting script
# (C)2019 Lewes Technology Consulting, LLC
#
# This script is run after the logstash updates via yum

# core concepts/syntax from: https://github.com/jjfalling/update-elasticsearch-plugins

PLUGINBIN=/usr/share/logstash/bin/logstash-plugin

lsplugins="logstash-input-relp logstash-filter-tld logstash-filter-rest logstash-filter-json_encode logstash-filter-cidr"

for lsplugin in ${lsplugins}; do
	$PLUGINBIN install ${lsplugin}
done