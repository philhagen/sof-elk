#!/bin/bash
# SOF-ELK® Supporting script
# (C)2018 Lewes Technology Consulting, LLC
#
# This script is used to update the MaxMind GeoIP databases

GEOIP_LIBDIR=/usr/local/share/GeoIP
GEOIP_BASEURL=http://geolite.maxmind.com/download/geoip/database/
GEOIP_CITYSOURCEARCH=GeoLite2-City.tar.gz
GEOIP_ASNSOURCEARCH=GeoLite2-ASN.tar.gz
GEOIP_CITYSOURCEFILE=GeoLite2-City.mmdb
GEOIP_ASNSOURCEFILE=GeoLite2-ASN.mmdb
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
    # wait up to 60min to start, so all these VMs don't hit the server at the same exact time
    randomNumber=$RANDOM
    let "randomNumber %= 3600"
    sleep ${randomNumber}
fi

cd ${GEOIP_LIBDIR}/
wget -N -q ${GEOIP_BASEURL}${GEOIP_CITYSOURCEARCH}
tar xzf ${GEOIP_CITYSOURCEARCH}
mv GeoLite2-City_*/${GEOIP_CITYSOURCEFILE} ${GEOIP_LIBDIR}/
rm -rf ${GEOIP_CITYSOURCEARCH} GeoLite2-City_*/

wget -N -q ${GEOIP_BASEURL}${GEOIP_ASNSOURCEARCH}
tar xzf ${GEOIP_ASNSOURCEARCH}
mv GeoLite2-ASN_*/${GEOIP_ASNSOURCEFILE} ${GEOIP_LIBDIR}/
rm -rf ${GEOIP_ASNSOURCEARCH} GeoLite2-ASN_*/

chown -R root:root ${GEOIP_LIBDIR}
