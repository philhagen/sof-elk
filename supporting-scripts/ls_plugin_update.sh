#!/bin/bash
# SOF-ELK® Supporting script
# (C)2026 Lewes Technology Consulting, LLC
#
# This script is run after logstash installs or updates

# core concepts/syntax from: https://github.com/jjfalling/update-elasticsearch-plugins
set -e

functions_include="/usr/local/sof-elk/supporting-scripts/functions.sh"
if [ -f "${functions_include}" ]; then
    . "${functions_include}"
else
    echo "${functions_include} not present.  Exiting " 1>&2
    exit 1
fi

logstashPluginBin=/usr/share/logstash/bin/logstash-plugin
lsplugins="logstash-input-relp logstash-input-google_pubsub logstash-filter-tld logstash-filter-json_encode logstash-filter-cidr"

# Make sure only root can run our script
require_root

#ensure the logstash plugin command exists
command -v "${logstashPluginBin}" >/dev/null 2>&1 || { echoerr "ERROR: logstash plugin command ${logstashPluginBin} does not exist"; exit 1; }


failed_plugins=""
for lsplugin in ${lsplugins}; do
    if ! "${logstashPluginBin}" install "${lsplugin}"; then
        echo "WARNING: failed to install plugin: ${lsplugin}" >&2
        if [ -z "${failed_plugins}" ]; then
            failed_plugins="${lsplugin}"
        else
            failed_plugins="${failed_plugins} ${lsplugin}"
        fi
    fi
done

if [ -n "${failed_plugins}" ]; then
    echo "WARNING: one or more plugins failed to install:${failed_plugins}" >&2
    exit 1
fi