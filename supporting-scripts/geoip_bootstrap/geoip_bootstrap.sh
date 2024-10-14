#!/bin/bash
# (C)2023 Phil Hagen <phil@lewestech.com>
#
# This script will configure a GeoIP.conf file and install the latest MaxMind GeoIP databases
# It will optionally configure a cron job to do this periodically
#
# To use a specified template or target configuration file export the
# geoip_conf_update and/or geoip_conf_target variables before running this script
# the /etc/GeoIP.conf.default and /etc/GeoIP.conf filenames are the defaults

# requires:
# - geoipupdate utility on $PATH
# - template GeoIP.conf.default identified in ${geoip_conf_template}

if [ -z ${geoip_conf_template} ]; then
    geoip_conf_template="/etc/GeoIP.conf.default"
fi
if [ -z ${geoip_conf_target} ]; then
    geoip_conf_target="/etc/GeoIP.conf"
fi

if [[ $EUID -ne 0 ]]; then
    echo "This script must be run as root.  Exiting."
    exit 1
fi

if [ -f ${geoip_conf_target} ]; then
    # not clobbering existing file
    echo "ERROR: ${geoip_conf_target} already exists - not overwriting."
    echo "       If you wish to replace this file, remove it and re-run this script."
    exit
fi

if [ ! -f ${geoip_conf_template} ]; then
    # no template, so exit
    echo "ERROR: ${geoip_conf_template} does not exist - exiting."
    exit
fi

if ! command -v geoipupdate &> /dev/null ; then
    echo "ERROR: geoipupdate tool not available. Cannot install MaxMind databases."
    exit
else
    geoipupdateversion=$( geoipupdate -V 2>&1 | awk '{print $2}' )
fi

if [ $( echo ${geoipupdateversion:0:1} ) -lt 4 ]; then
    echo "ERROR: Your version of the geoipupdate tool is too old.  Update to at least version 4.x and re-run the bootstrap script"
    exit
fi

target_dir=$( dirname ${geoip_conf_target} )
realpath=$( realpath $0 )
if [ ! -w ${target_dir} ]; then
    echo "ERROR: ${target_dir} not writable, so cannot create ${geoip_conf_target}."
    echo "       You may need to run 'sudo ${realpath}'. Exiting."
    exit
fi

echo "Do you want to download the MaxMind GeoIP databases?"
echo "(This requires free MaxMind account and internet access.)"
echo "This prompt will time out in 30 seconds."
read -t 30 -p "Y/N: " installmmdb
echo

if [ -z ${installmmdb} ] || [ ${installmmdb^^} != "Y" ]; then
    exit
fi

echo "If you do not already have a MaxMind account, sign up here:"
echo "  https://www.maxmind.com/en/geolite2/signup"
echo "Once signed in, generate a license key here:"
echo "  https://www.maxmind.com/en/accounts/current/license-key"
echo

read -p "Enter your MaxMind Account ID: " account_id
read -p "Enter your MaxMind License Key: " license_key

# The MaxMind updater is finicky... Script will try this many times to update before exiting with a failure
RETRIES=3
SUCCESS=0
while [ ${SUCCESS} -eq 0 ]; do
    # do this every loop because it'll prevent having a leftover "bad" file stuck in the root
    sed "s/<%ACCOUNT_ID%>/${account_id}/g;s/<%LICENSE_KEY%>/${license_key}/g" ${geoip_conf_template} > ${geoip_conf_target}

    tmpfile=$( mktemp )
    geoipupdate > ${tmpfile} 2>&1

    if [ $? -eq 0 ]; then
        SUCCESS=1

    else
        RETRIES="$((${RETRIES}-1))"

        rm -f ${geoip_conf_target}

        if [ ${RETRIES} -gt 0 ]; then
            echo
            echo "Temporary failure of geoipupdate command.  Waiting 5 seconds to try again."
            echo "=== Begin geoipupdate output ==="
            cat ${tmpfile}
            echo "=== End geoipupdate output ==="
            sleep 5
        else
            echo
            echo "ERROR: geoipupdate command failed.  Removing ${geoip_conf_target}"
            echo "       You may have provided an invalid Account ID and/or License Key."
            echo "       If these were confirmed correct, wait a few minutes and run this"
            echo "       command again."
            rm -f ${geoip_conf_target}
            exit
        fi
    fi
 
    rm -f ${tmpfile}
done

echo "MaxMind GeoIP databases have been installed."
echo
echo "Restarting Logstash to pick up the new database files."
systemctl restart logstash.service

echo "Do you want to set a weekly cron job that will update the MaxMind GeoIP databases automatically?"
read -p "Y/N: " install_cron_job

if [ ${install_cron_job^^} == "Y" ]; then
    echo "18 4 * * 2 root /usr/local/sbin/geoip_update_logstash.sh" > /etc/cron.d/geoipupdate
fi
