#!/bin/bash
# SOF-ELK Supporting script
# (C)2017 Lewes Technology Consulting, LLC
#
# This script is used to prepare the VM for distribution

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

echo "checking that we're on the correct SOF-ELK branch"
cd /usr/local/sof-elk/
git branch
echo "ACTION REQUIRED!  Is this the correct branch?  (Should be 'class/v*' or 'master', with  all others removed.)"
read

echo "updating local git repo clones"
cd /usr/local/sof-elk/
git pull --all

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
systemctl stop logstash
echo "clearing elasticsearch"
curl -s -XDELETE 'http://localhost:9200/_all' > /dev/null
echo "removing elasticsearch templates"
curl -s -XDELETE 'http://localhost:9200/_template/*' > /dev/null
echo "removing elasticsearch .kibana index"
curl -s -XDELETE 'http://localhost:9200/.kibana' > /dev/null
echo "stopping filebeat service"
systemctl stop filebeat
echo "removing filebeat registry"
rm -f /var/lib/filebeat/*
echo "removing any input logs from prior parsing"
rm -rf /logstash/*/*
echo "reload kibana dashboards"
/usr/local/sbin/load_all_dashboards.sh

echo "stopping network"
systemctl stop network
#echo "clearing udev networking rules"
echo > /etc/udev/rules.d/90-eno-fix.rules

echo "clearing MAC address from interface"
grep -v HWADDR /etc/sysconfig/network-scripts/ifcfg-ens33 > /tmp/tmp_ifcfg_ens
cat /tmp/tmp_ifcfg_ens > /etc/sysconfig/network-scripts/ifcfg-ens33
rm /tmp/tmp_ifcfg_eno

echo "stopping syslog"
systemctl stop rsyslog
echo "clearing existing log files"
find /var/log -type f -exec rm -f {} \;

echo "clearing SSH Host Keys"
systemctl stop sshd
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
