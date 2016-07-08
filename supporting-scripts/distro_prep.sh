#!/bin/bash

if [[ -n $SSH_CONNECTION ]]; then
    echo "ERROR: This script must be run locally - Exiting."
    exit 2
fi

DISKSHRINK=1
# parse any command line arguments
if [ $# -gt 0 ]; then
    while true; do
        if [ "$1" ]; then
            if [ "$1" == '-nodisk' ]; then
                DISKSHRINK=0
            fi
            shift
        else
            break
        fi
    done
fi

revdate=$( date +%Y-%m-%d )

echo "looking for specific pre-distribution notes/instructions"
if [ -s ~/distro_prep.txt ]; then
    echo "~/distro_prep.txt still contains instructions - Exiting."
    echo
    cat ~/distro_prep.txt
    exit 2
fi

echo "removing old kernels"
package-cleanup -y --oldkernels --count=1
echo "cleaning yum caches"
yum clean all

echo "cleaning user histories"
rm -f ~root/.bash_history
rm -f ~elk_user/.bash_history

echo "cleaning temp directories"
rm -rf ~elk_user/tmp/*

echo "updating GeoIP database"
/usr/local/sbin/geoip_update.sh -now

echo "stopping logstash"
service logstash stop
echo "clearing elasticsearch"
curl -s -XDELETE 'http://localhost:9200/_all' > /dev/null
echo "removing elasticsearch templates"
curl -s -XDELETE 'http://localhost:9200/_template/*' > /dev/null
echo "removing elasticsearch .kibana index"
curl -s _XDELETE 'http://localhost:9200/.kibana' > /dev/null
echo "removing logstash sincedb"
rm -f /var/db/logstash/sincedb
echo "removing any input logs from prior parsing"
rm -rf /usr/local/logstash-*/*
echo "reload kibana dashboards"
/usr/local/sbin/load_all_dashboards.sh

echo "stopping network"
service network stop
#echo "clearing udev networking rules"
#echo > /etc/udev/rules.d/70-persistent-net.rules

echo "stopping syslog"
service rsyslog stop
echo "clearing existing log files"
find /var/log -type f -exec rm -f {} \;

echo "clearing SSH Host Keys"
service sshd stop
rm -f /etc/ssh/*key*

if [ $DISKSHRINK -eq 1 ]; then
    echo "ACTION REQUIRED!"
    echo "remove any snapshots that already exist and press Return"
    read

    # we don't use swap any more
    # echo "zeroize swap:"
    # swapoff -a
    # for swappart in $( fdisk -l | grep swap | awk '{print $2}' | sed -e 's/:$//' ); do
    #     echo "- zeroize $swappart (swap)"
    #     dd if=/dev/zero of=$swappart
    #     mkswap $swappart
    # done

    echo "zeroize free space and shrink:"
    for mtpt in $( mount -t xfs | awk '{print $3}' ); do
        echo "- zeroize $mtpt"
        dd if=/dev/zero of=$mtpt/ddfile
        rm -f $mtpt/ddfile
        echo "- shrink $mtpt"
        vmware-toolbox-cmd disk shrink $mtpt
    done
fi

echo "updating /etc/issue* files for boot message"
cat /etc/issue.prep | sed -e "s/<%REVNO%>/$revdate/" > /etc/issue.stock