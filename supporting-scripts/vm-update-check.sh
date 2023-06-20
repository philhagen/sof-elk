#!/bin/bash
# SOF-ELK® Supporting script
# (C)2023 Lewes Technology Consulting, LLC
#
# This script creates a file if a new version of the SOF-ELK VM is available
# This is ONLY run for public/community versions

vm_update_status_file=/var/run/sof-elk_vm_update

cd /usr/local/sof-elk/

current_branch=$( git branch )

if ! echo "${current_branch}" | grep -q "^\* public\/v[0-9]\{8\}$" ; then
    # not on a public/community edition branch
    exit
fi

if [ -f ${vm_update_status_file} ]; then
    # already checked since boot, no need to do it again
    exit
fi

current_release=$( echo "${current_branch}" | sed -e 's/^\* public\/v\([0-9]\{8\}\).*/\1/' )
latest_release=$( curl -s --head https://for572.com/sof-elk-versioncheck | grep "^Location: " | sed -e 's/^Location: .*v\([0-9]\{8\}\).*/\1/' )

if [[ ${current_release} < ${latest_release} ]]; then
    # there is a new public version available
    touch ${vm_update_status_file}
fi
