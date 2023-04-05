#!/bin/bash
# SOF-ELK® Supporting script
# (C)2023 Lewes Technology Consulting, LLC
#
# This script is used to perform an in-place update of the geoipupdate utility.
# The new version is needed for new-format hashed API keys

# perform version check and quit if not the specific old version

if [ $(rpm -q geoipupdate --queryformat %{VERSION}) != "2.5.0" ]; then
    # already updated - exit cleanly
    exit
fi

if [[ $EUID -ne 0 ]]; then
    echo "This script must be run as root.  Exiting."
    exit 1
fi

yum -q -y install https://github.com/maxmind/geoipupdate/releases/download/v4.10.0/geoipupdate_4.10.0_linux_386.rpm > /dev/null

rm -f /etc/GeoIP.conf

if [ -f /etc/GeoIP.conf.rpmsave ]; then
    mv /etc/GeoIP.conf.rpmsave /etc/GeoIP.conf.old_version
    echo "Your exisitng GeoIP update configuration has been renamed"
    echo "  \"/etc/GeoIP.conf.old_version\".  It will no longer work and you must"
    echo "  generate a NEW version of a GeoIP key, then run"
    echo "  \"sudo /usr/local/sbin/geoip_bootstrap.sh\" again, supplying the new key."
fi

cat /usr/local/sof-elk/ansible/roles/sof-elk_base/files/GeoIP.conf.default > /etc/GeoIP.conf.default

### this is needed if we DON'T do the sof-elk_update.sh path!!
#curl -L -o /etc/GeoIP.conf.default https://raw.githubusercontent.com/philhagen/sof-elk/main/ansible/roles/sof-elk_base/files/GeoIP.conf.default