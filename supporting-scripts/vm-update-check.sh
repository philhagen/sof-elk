#!/bin/bash
# SOF-ELK® Supporting script
# (C)2024 Lewes Technology Consulting, LLC
#
# This script creates a file if a new version of the SOF-ELK VM is available
# This is ONLY run for public/community versions

VM_UPDATE_STATUS_FILE="/var/run/sof-elk_vm_update"

cd /usr/local/sof-elk/ || exit 1

current_branch=$( git branch | grep ^\* | awk '{print $2}' )

if ! echo "${current_branch}" | grep -q "^public\/v[0-9]\{8\}$" ; then
  # not on a public/community edition branch
  exit
fi

if [ -f "${VM_UPDATE_STATUS_FILE}" ]; then
  # already checked since boot, no need to do it again
  exit
fi

current_release=$( echo "${current_branch}" | sed -e 's/^public\/v\([0-9]\{8\}\).*/\1/' )
latest_release=$( curl -s --head --referer "${current_release}" https://for572.com/sof-elk-versioncheck | grep "^Location: " | sed -e 's/^Location: .*v\([0-9]\{8\}\).*/\1/' )

if [[ ${current_release} < ${latest_release} ]]; then
  # there is a new public version available
  touch "${VM_UPDATE_STATUS_FILE}"
fi
