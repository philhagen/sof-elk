#!/bin/bash
# (C)2021 Phil Hagen <phil@lewestech.com>
#
# This script will configure a GeoIP.conf file and install the latest MaxMind GeoIP databases
# It will optionally configure a cron job to do this periodically

# requires:
# - geoipupdate utility on $PATH
# - template GeoIP.conf.dist identified in ${geoip_conf_template}

geoip_conf_template="/etc//GeoIP.conf.default"
geoip_conf_target="/etc/GeoIP.conf"

if [[ $EUID -ne 0 ]]; then
    echo "This script must be run as root.  Exiting."
    exit 1
fi

if [ -f ${geoip_conf_target} ]; then
    # not clobbering existing file
    exit
fi

if ! command -v geoipupdate &> /dev/null ; then
    echo "ERROR: geoipupdate tool not available. Cannot install MaxMind databases."
    exit
else
    geoipupdateversion=$( geoipupdate -V 2>&1 | awk '{print $2}' )
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
echo "  https://www.maxmind.com/en/accounts/155942/license-key"
echo "You have geoipupdate ${geoipupdateversion}, so ensure you"
echo "  create a license key for this version."
echo

read -p "Enter your MaxMind Account ID: " account_id
read -p "Enter your MaxMind License Key: " license_key

sed "s/<%ACCOUNT_ID%>/${account_id}/g;s/<%LICENSE_KEY%>/${license_key}/g" ${geoip_conf_template} > ${geoip_conf_target}

geoipupdate > /dev/null 2>&1

if [ $? -ne 0 ]; then
    echo
    echo "ERROR: geoipupdate command failed.  Removing ${geoip_conf_target}"
    rm -f ${geoip_conf_target}
    exit
else
    echo "MaxMind GeoIP databases have been installed."
    echo "Restarting Logstash to pick up the new database files."
    systemctl restart logstash.service
    echo
fi

echo "Do you want to set a weekly cron job that will update the MaxMind GeoIP databases automatically?"
read -p "Y/N: " install_cron_job

if [ ${install_cron_job^^} == "Y" ]; then
    echo "18 4 * * 2 root /usr/local/sbin/geoip_update_logstash" > /etc/cron.d/geoipupdate
fi
