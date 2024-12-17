#!/bin/bash
# SOF-ELK® Supporting script
# (C)2024 Lewes Technology Consulting, LLC
#
# This script is run after an elasticsearch update

# core concepts/syntax from: https://github.com/jjfalling/update-elasticsearch-plugins

set -e

elasticsearchPluginDir='/usr/share/elasticsearch/plugins'
elasticsearchPlugin='/usr/share/elasticsearch/bin/elasticsearch-plugin'
#elasticsearchPluginPage='https://www.elastic.co/guide/en/elasticsearch/reference/current/modules-plugins.html'

declare -A customPlugins
customPlugins=( ["head"]="mobz/elasticsearch-head" )

# Make sure only root can run our script
if [ "$(id -u)" != "0" ]; then
  printf "This script needs to run as root to run the updates!\n" 1>&2
  exit 1
fi

#ensure the elasticsearch plugin command exists
command -v "${elasticsearchPlugin}" >/dev/null 2>&1 || { printf "\nERROR: elasticsearch plugin command %s does not exist\n\n" ${elasticsearchPlugin}; exit 1; }

#ensure the es plugin dir exists
if [ ! -d "${elasticsearchPluginDir}" ]; then
  printf "\nERROR: elasticsearchPluginDir %s does not exist\n" ${elasticsearchPluginDir}
  exit 1
fi

#look at each installed plugin and try to find its repo, then offer to update
for currentInstalledPlugin in $( "${elasticsearchPlugin}" list ); do
  if [[ "${currentInstalledPlugin}" == "preupgrade"* ]]; then
    continue
  fi

  if [[ ${customPlugins["$currentInstalledPlugin"]} ]]; then
    "${elasticsearchPlugin}" remove "${currentInstalledPlugin}" > /dev/null
    "${elasticsearchPlugin}" install "${customPlugins["$currentInstalledPlugin"]}" > /dev/null

  else
    "${elasticsearchPlugin}" remove "${currentInstalledPlugin}" > /dev/null
    "${elasticsearchPlugin}" install "${currentInstalledPlugin}" > /dev/null

  fi
done
