#!/bin/bash
# SOF-ELK® Supporting script
# (C)2026 Lewes Technology Consulting, LLC
#
# This script will update GeoIP databases using an existing GeoIP.conf file
# If any of the databases have changed, it will restart the Logstash service

GEOIP_CONFIG=/etc/GeoIP.conf

functions_include="/usr/local/sof-elk/supporting-scripts/functions.sh"
if [ -f "${functions_include}" ]; then
    . "${functions_include}"
else
    echo "${functions_include} not present.  Exiting " 1>&2
    exit 1
fi

if [ ! -f "${GEOIP_CONFIG}" ]; then
  echo "The GeoIP configuration file has not been created - exiting."
  echo
  echo "No updates can be downloaded without this file."
  echo "Run 'geoip_bootstrap.sh' as root to configure this system for"
  echo "automatic updates."
  echo
  echo "You will need an Account ID and License Key from a free MaxMind"
  echo "account to enable them."
  exit 2
fi

# identify the database directory or use the standard default if not set
DBDIR=$( grep ^DatabaseDirectory "${GEOIP_CONFIG}" | awk '{$1=""; print}' |  sed -e 's/^[[:space:]]*//' )
if [ -z "${DBDIR}" ]; then
    DBDIR=/usr/local/share/GeoIP/
fi

# identify the configured databases
DATABASES=$( grep ^EditionIDs "${GEOIP_CONFIG}" | awk '{$1=""; print}' | sed -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//' )

# if there are no databases, there's no need to update anything!
if [ -n "${DATABASES}" ]; then
    # default/empty variables
    UPDATES=0
    declare -A md5=()
    declare -A md5_check=()

    for DATABASE in ${DATABASES}; do
        if [ -f "${DBDIR}/${DATABASE}.mmdb" ]; then
            md5["${DATABASE}"]=$( md5sum -b "${DBDIR}"/"${DATABASE}".mmdb | awk '{print $1}' )
        else
            md5["${DATABASE}"]=""
        fi
    done

    # run the updater
    if ! geoipupdate -f "${GEOIP_CONFIG}"; then
        echoerr "ERROR: geoipupdate failed - database files were not refreshed."
    fi

    # compare md5s of what was there before the update to what is there now
    for DATABASE in ${DATABASES}; do
        md5_check[${DATABASE}]=$( md5sum -b "${DBDIR}"/"${DATABASE}".mmdb | awk '{print $1}' )
        if [ "${md5["${DATABASE}"]}" != "${md5_check["${DATABASE}"]}" ]; then
            UPDATES=1
        fi
    done

    # if there were any updates, run the expensive Logstash restart
    if [ "${UPDATES}" -eq 1 ]; then
        systemctl restart logstash.service
    fi
fi
