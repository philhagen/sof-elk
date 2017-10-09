#!/bin/bash
# SOF-ELK® Supporting script
# (C)2016 Lewes Technology Consulting, LLC
#
# This script is used to update the MaxMind GeoIP databases

GEOIP_LIBDIR=/usr/local/share/GeoIP
GEOIP_CITYSOURCEURL=http://geolite.maxmind.com/download/geoip/database/GeoLiteCity.dat.gz
GEOIP_ASNSOURCEURL=http://download.maxmind.com/download/geoip/database/asnum/GeoIPASNum.dat.gz
GEOIP_CITYSOURCEFILE=GeoLiteCity.dat.gz
GEOIP_ASNSOURCEFILE=GeoIPASNum.dat.gz
RUNNOW=0

# parse any command line arguments
if [ $# -gt 0 ]; then
    while true; do
        if [ $1 ]; then
            if [ $1 == '-now' ]; then
                RUNNOW=1
            fi
            shift
        else
            break
        fi
    done
fi

if [ ! -d ${GEOIP_LIBDIR} ]; then
    mkdir -p ${GEOIP_LIBDIR}
fi

if [ $RUNNOW -eq 0 ]; then
    # wait up to 20min to start, so all these VMs don't hit the server at the same exact time
    randomNumber=$RANDOM
    let "randomNumber %= 1800"
    sleep ${randomNumber}
fi

cd ${GEOIP_LIBDIR}/
wget -N -q ${GEOIP_CITYSOURCEURL}
gunzip -f ${GEOIP_CITYSOURCEFILE}
wget -N -q ${GEOIP_ASNSOURCEURL}
gunzip -f ${GEOIP_ASNSOURCEFILE}
