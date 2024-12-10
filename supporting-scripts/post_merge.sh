#!/bin/bash
# SOF-ELK® Supporting script
# (C)2024 Lewes Technology Consulting, LLC
#
# This script is used to perform post-merge steps, eg after the git repository
#   is updated

FILEBEAT_CONF_PATH=/etc/filebeat/filebeat.yml
LOGO_PATH="/usr/share/kibana/node_modules/@kbn/core-apps-server-internal/assets/sof-elk.svg"

# if a SKIP_HOOK variable is set to 1, don't do any of this
# method from here: https://stackoverflow.com/a/33431504/1400064
case ${SKIP_HOOK:-0} in
  1) exit 0 ;;
  0) ;;
  *) ;; # this should never happen
esac

# activate all "supported" Logstash configuration files
for file in /usr/local/sof-elk/configfiles/* ; do
  if [ -h "/etc/logstash/conf.d/$( basename "${file}" )" ]; then
    rm -f "/etc/logstash/conf.d/$( basename "${file}" )"
  fi

  ln -s "${file}" "/etc/logstash/conf.d/$( basename "${file}" )"
done

# deactivate dead configuration file symlinks links
for deadlink in /etc/logstash/conf.d/* ; do
  if [ ! -e "${deadlink}" ] ; then
    rm -f "${deadlink}"
  fi
done

# reload logstash
systemctl restart logstash

# create necessary ingest directories
ingest_dirs="syslog nfarch httpd passivedns zeek kape plaso microsoft365 azure aws gcp gws kubernetes"
for ingest_dir in ${ingest_dirs}; do
  if [ ! -d "/logstash/${ingest_dir}" ]; then
    mkdir -m 1777 "/logstash/${ingest_dir}"
  fi
done

# activate all elastalert rules
#for file in /usr/local/sof-elk/lib/elastalert_rules/*.yaml ; do
#	if [ -h "/etc/elastalert_rules/$( basename "${file}" )" ]; then
#		rm -f "/etc/elastalert_rules/$( basebame "${file}" )"
#	fi
#
#	ln -s "${file}" "/etc/elastalert_rules/$( basename "${file}" )"
#done
# reload elastalert
#/usr/bin/systemctl restart elastalert

# restart filebeat to account for any new config files and/or prospectors
if [ -a  "${FILEBEAT_CONF_PATH}" ]; then
  rm -f "${FILEBEAT_CONF_PATH}"
fi
ln -fs /usr/local/sof-elk/lib/configfiles/filebeat.yml "${FILEBEAT_CONF_PATH}"
/usr/bin/systemctl restart filebeat

# other housecleaning
if [ -a "${LOGO_PATH}" ]; then
  rm -rf "${LOGO_PATH}"
fi
ln -fs /usr/local/sof-elk/lib/sof-elk.svg "${LOGO_PATH}"

# set up all cron jobs, remove old ones
for file in /usr/local/sof-elk/supporting-scripts/cronjobs/* ; do
  if [ -h "/etc/cron.d/$( basename "${file}" )" ]; then
    rm -f "/etc/cron.d/$( basename "${file}" )"
  fi

  ln -s "${file}" "/etc/cron.d/$( basename "${file}" )"
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
