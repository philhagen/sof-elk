#!/bin/bash
# SOF-ELK® Supporting script
# (C)2026 Lewes Technology Consulting, LLC
#
# This script is run after an elasticsearch update

# core concepts/syntax from: https://github.com/jjfalling/update-elasticsearch-plugins
set -e

functions_include="/usr/local/sof-elk/supporting-scripts/functions.sh"
if [ -f "${functions_include}" ]; then
    . "${functions_include}"
else
    echo "${functions_include} not present.  Exiting " 1>&2
    exit 1
fi

elasticsearchPluginDir='/usr/share/elasticsearch/plugins'
elasticsearchPluginBin='/usr/share/elasticsearch/bin/elasticsearch-plugin'
#elasticsearchPluginPage='https://www.elastic.co/guide/en/elasticsearch/reference/current/modules-plugins.html'

declare -A customPlugins
customPlugins=( ["head"]="mobz/elasticsearch-head" )

# Make sure only root can run our script
require_root

#ensure the elasticsearch plugin command exists
command -v "${elasticsearchPluginBin}" >/dev/null 2>&1 || { echoerr "ERROR: elasticsearch plugin command ${elasticsearchPluginBin} does not exist"; exit 1; }

#ensure the es plugin dir exists
if [ ! -d "${elasticsearchPluginDir}" ]; then
    echoerr "ERROR: elasticsearchPluginDir ${elasticsearchPluginDir} does not exist"
    exit 1
fi

#look at each installed plugin and try to find its repo, then offer to update
if ! installedPluginList=$( "${elasticsearchPluginBin}" list ); then
    echoerr "ERROR: Could not list installed plugins"
    exit 2
fi
for currentInstalledPlugin in ${installedPluginList}; do
    if [[ "${currentInstalledPlugin}" == "preupgrade"* ]]; then
        continue
    fi

    if [[ ${customPlugins["${currentInstalledPlugin}"]} ]]; then
        installTarget="${customPlugins["${currentInstalledPlugin}"]}"
    else
        installTarget="${currentInstalledPlugin}"
    fi

    if ! "${elasticsearchPluginBin}" remove "${currentInstalledPlugin}" > /dev/null; then
        echoerr "ERROR: failed to remove plugin: ${currentInstalledPlugin} - skipping reinstall attempt"
    elif ! "${elasticsearchPluginBin}" install "${installTarget}" > /dev/null; then
        echoerr "ERROR: failed to install plugin: ${installTarget}"
    fi
done
