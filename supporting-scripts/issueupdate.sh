#!/bin/bash
# SOF-ELK® Supporting script
# (C)2018 Lewes Technology Consulting, LLC
#
# This script runs as a post-dhcp lease acquisition hook to change the /etc/issue file with a new IP address, then restarting any agetty processes so the new IP is shown on the prelogin authentiction screen

issueupdate_config() {
    IP=$( ip address show $( ip route|grep default | awk '{print $5}' ) | awk '/inet / {print $2}' | cut -d '/' -f 1 )
    logger "SOF-ELK post-dhcp lease: issueupdate_config() - IP=${IP}"
    cat /etc/issue.stock | sed -e "s/<%IP%>/$IP/" > /etc/issue
    TTYLIST=$( ps -h -p  $( pidof agetty) | awk '{print $2}' | sort | uniq)
    for TTY in $TTYLIST; do
    	systemctl restart getty@${TTY}
        while ( ! ps -h -p $( pidof agetty ) | grep -q $TTY ); do
            sleep 3;
            systemctl restart getty@${TTY}
        done
    done
}

issueupdate_restore() {
    IP=$( ip address show $( ip route|grep default | awk '{print $5}' ) | awk '/inet / {print $2}' | cut -d '/' -f 1 )
    logger "SOF-ELK post-dhcp lease: issueupdate_restore() - IP=${IP}"
    echo > /dev/null
}