#!/bin/bash
# SOF-ELK® Supporting script
# (C)2020 Lewes Technology Consulting, LLC
#
# This script will first determine if the GeoIP.conf file has been updated with a User ID and License Key.
# If so, it will run the update.  If the file is still the default, it will output a message indicating the user needs to register an account and update the file.

GEOIP_CONFIG=/etc/GeoIP.conf

if [ ! -f ${GEOIP_CONFIG} ]; then
    echo "The GeoIP configuration file has not been created - exiting."
    echo
    echo "No updates can be downloaded without this file.  Using the"
    echo "/etc/GeoIP.conf.default file as a template, create ${GEOIP_CONFIG}."
    echo "Replace the AccountID and LicenseKey values with your own."
    exit
fi

geoipupdate -f ${GEOIP_CONFIG}