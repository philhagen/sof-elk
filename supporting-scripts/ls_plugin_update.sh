#!/bin/bash
# SOF-ELK® Supporting script
# (C)2026 Lewes Technology Consulting, LLC
#
# This script is run after logstash installs or updates

# core concepts/syntax from: https://github.com/jjfalling/update-elasticsearch-plugins
set -e

PLUGINBIN=/usr/share/logstash/bin/logstash-plugin
lsplugins="logstash-input-relp logstash-input-google_pubsub logstash-filter-tld logstash-filter-json_encode logstash-filter-cidr"

failed_plugins=""
for lsplugin in ${lsplugins}; do
    if ! "${PLUGINBIN}" install "${lsplugin}"; then
        echo "WARNING: failed to install plugin: ${lsplugin}" >&2
        failed_plugins="${failed_plugins} ${lsplugin}"
    fi
done

if [ -n "${failed_plugins}" ]; then
    echo "WARNING: one or more plugins failed to install:${failed_plugins}" >&2
    exit 1
fi