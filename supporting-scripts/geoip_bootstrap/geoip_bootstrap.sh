#!/bin/bash
# (C)2021 Phil Hagen <phil@lewestech.com>
#
# This script will configure a GeoIP.conf file and install the latest MaxMind GeoIP databases
# It will optionally configure a cron job to do this periodically
#
# To use a specified template or target configuration file export the
# geoip_conf_update and/or geoip_conf_target variables before running this script
# the /etc/GeoIP.conf.dist and /etc/GeoIP.conf filenames are the defaults

# requires:
# - geoipupdate utility on $PATH
# - template GeoIP.conf.dist identified in ${geoip_conf_template}

if [ -z ${geoip_conf_template} ]; then
    geoip_conf_template="/etc/GeoIP.conf.dist"
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

if ! command -v geoipupdate &> /dev/null ; then
    echo "ERROR: geoipupdate tool not available. Cannot install MaxMind databases."
    exit
else
    geoipupdateversion=$( geoipupdate -V 2>&1 | awk '{print $2}' )
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
echo "You have geoipupdate ${geoipupdateversion}, so ensure you"
echo "  create a license key for this version."
echo

read -p "Enter your MaxMind Account ID: " account_id
read -p "Enter your MaxMind License Key: " license_key

sed "s/<%ACCOUNT_ID%>/${account_id}/g;s/<%LICENSE_KEY%>/${license_key}/g" ${geoip_conf_template} > ${geoip_conf_target}

tmpfile=$( mktemp )
geoipupdate > ${tmpfile} 2>&1

if [ $? -ne 0 ]; then
    echo
    echo "ERROR: geoipupdate command failed.  Removing ${geoip_conf_target}"
    echo "       The command generated the following output (if any):"
    echo "=== Begin geoipupdate output ==="
    cat ${tmpfile}
    echo "=== End geoipupdate output ==="
    rm -f ${geoip_conf_target}
    rm -f ${tmpfile}
    exit
else
    rm -f ${tmpfile}
    echo "MaxMind GeoIP databases have been installed."
    echo "Restarting Logstash to pick up the new database files."
    systemctl restart logstash.service
    echo
fi

echo "Do you want to set a weekly cron job that will update the MaxMind GeoIP databases automatically?"
read -p "Y/N: " install_cron_job

if [ ${install_cron_job^^} == "Y" ]; then
    echo "18 4 * * 2 root /usr/local/sbin/geoip_update_logstash.sh" > /etc/cron.d/geoipupdate
fi
