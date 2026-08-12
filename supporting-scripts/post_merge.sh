#!/bin/bash
# SOF-ELK® Supporting script
# (C)2026 Lewes Technology Consulting, LLC
#
# This script is used to perform post-merge steps, eg after the git repository
#   is updated

LOGO_PATH="/usr/share/kibana/node_modules/@kbn/core-apps-server-internal/assets/sof-elk.svg"
INGEST_DIRS="syslog nfarch httpd passivedns zeek kape plaso microsoft365 azure aws gcp gws kubernetes hayabusa appleul volatility/pslist volatility/pstree volatility/psscan volatility/netscan volatility/cmdline volatility/netstat"
RELOAD_LOGSTASH=0
RESTART_FILEBEAT=0
RESTART_KIBANA=0

# if a SKIP_HOOK variable is set to 1, don't do any of this
# method from here: https://stackoverflow.com/a/33431504/1400064
case ${SKIP_HOOK:-0} in
    1) exit 0 ;;
    0) ;;
    *) ;; # this should never happen
esac

# if a previous commit ID has been set in a shell variable, determine what paths have changed for conditional restarts below
if [ -n "${PREV_COMMIT}" ]; then
    mapfile -t files_changed < <( git diff --name-only "$(git merge-base "${PREV_COMMIT}" HEAD)" )

    for file in "${files_changed[@]}"; do
        if [[ "${file}" == configfiles/* ]]; then
            RELOAD_LOGSTASH=1
        fi
        if [[ "${file}" == lib/filebeat_inputs/* ]]; then
            RESTART_FILEBEAT=1
        fi
    done

else
    RELOAD_LOGSTASH=1
    RESTART_FILEBEAT=1
    RESTART_KIBANA=1
fi

if [[ "${RELOAD_LOGSTASH}" -eq 1 ]]; then
    # activate all "supported" Logstash configuration files
    for file in /usr/local/sof-elk/configfiles/* ; do
        ln -fs "${file}" "/etc/logstash/conf.d/$( basename "${file}" )"
    done

    # deactivate dead configuration file symlinks links
    for deadlink in /etc/logstash/conf.d/* ; do
        if [ ! -e "${deadlink}" ] ; then
            rm -f "${deadlink}"
        fi
    done

    # reload logstash configurations
    for lspid in $( pgrep -u logstash java ); do
        kill -s HUP "${lspid}"
    done
fi

# create necessary ingest directories (don't forget to add new ones to ansible's filebeat role)
for ingest_dir in ${INGEST_DIRS}; do
    if [ ! -d "/logstash/${ingest_dir}" ]; then
        mkdir -m 1777 -p "/logstash/${ingest_dir}"
    fi
done

# activate all elastalert rules
#for file in /usr/local/sof-elk/lib/elastalert_rules/*.yaml ; do
#	ln -fs "${file}" "/etc/elastalert_rules/$( basename "${file}" )"
#done
# reload elastalert
#/usr/bin/systemctl restart elastalert

if [[ "${RESTART_FILEBEAT}" -eq 1 ]]; then
    # restart filebeat to account for any new config files and/or prospectors
    /usr/bin/systemctl restart filebeat
fi

# other housecleaning
ln -fs /usr/local/sof-elk/lib/sof-elk.svg "${LOGO_PATH}"

# link supporting scripts
for file in csv2json.py fw_modify.sh geoip_bootstrap.sh geoip_update_logstash.sh kick-aws-logs.sh load_all_dashboards.sh nfdump2sof-elk.sh post_merge.sh sof-elk_clear.py sof-elk_update.sh sof-elk_branch.sh volatility2sof-elk.py ; do
    filepath=/usr/local/sof-elk/supporting-scripts/${file}

    ln -fs "${filepath}" "/usr/local/sbin/${file}"
done
for deadlink in /usr/local/sbin/* ; do
    if [ ! -e "${deadlink}" ] ; then
        rm -f "${deadlink}"
    fi
done

# set up all cron jobs, remove old ones
for file in /usr/local/sof-elk/supporting-scripts/cronjobs/* ; do
    ln -fs "${file}" "/etc/cron.d/$( basename "${file}" )"
done
for deadlink in /etc/cron.d/* ; do
    if [ ! -e "${deadlink}" ] ; then
        rm -f "${deadlink}"
    fi
done

# create the atd sequence file, if not already there
if [ ! -f /var/spool/cron/atjobs/.SEQ ]; then
    touch /var/spool/cron/atjobs/.SEQ
fi

# reload all dashboards
/usr/local/sbin/load_all_dashboards.sh
