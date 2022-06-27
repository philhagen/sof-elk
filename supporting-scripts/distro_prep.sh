#!/bin/bash
# SOF-ELK® Supporting script
# (C)2022 Lewes Technology Consulting, LLC
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

echo "checking that we're on the correct SOF-ELK® branch"
cd /usr/local/sof-elk/
git branch
echo "ACTION REQUIRED!  Is this the correct branch?  (Should be 'public/v*' or 'class/v*', with  all others removed.)"
read

curl -s -XGET 'http://localhost:9200/_cat/indices/'|sort
echo "ACTION REQUIRED!  The data above is still stored in elasticsearch.  Press return if this is correct or Ctrl-C to quit."
read

echo "the following logs and subdirectories are still present in the ingest directory.  Press return if this is correct or Ctrl-C to quit."
find /logstash/ -type f -print
find /logstash/ -mindepth 2 -type d
read

echo "updating local git repo clones"
cd /usr/local/sof-elk/
git pull --all

echo "removing old kernels"
package-cleanup -y --oldkernels --count=1
echo "cleaning yum caches"
yum clean all --enablerepo=elk-*
rm -rf /var/cache/yum

echo "cleaning user home directories"
rm -f ~root/.bash_history
rm -f ~elk_user/.bash_history
rm -f ~root/.python_hisory
rm -f ~elk_user/.python_history
rm -f ~root/.lesshst
rm -f ~elk_user/.lesshst
rm -rf ~root/.local
rm -rf ~elk_user/.local
rm -rf ~root/.cache
rm -rf ~elk_user/.cache
rm -rf ~root/.config/htop
rm -rf ~elk_user/.config/htop
rm -rf ~root/.config/gcloud/logs
rm -rf ~elk_user/.config/gcloud/logs
rm -rf ~root/.vim
rm -rf ~elk_user/.vim
#cat /dev/null > ~/.bash_history; history -c ; history -w; exit

echo "cleaning temp directories"
rm -rf ~elk_user/tmp/*

echo "Resetting GeoIP databases to empty."
for GEOIPDB in ASN City Country; do
    rm -f /usr/local/share/GeoIP/GeoLite-${GEOIPDB}.mmdb
    cp -a /usr/local/sof-elk/supporting-scripts/geoip_bootstrap/empty-GeoLite2-${GEOIPDB}.mmdb /usr/local/share/GeoIP/GeoLite2-${GEOIPDB}.mmdb
done
rm -f /etc/GeoIP.conf
rm -f /etc/cron.d/geoipupdate

echo "stopping elastalert"
systemctl stop elastalert
echo "clearing elastalert"
curl -s -XDELETE 'http://127.0.0.1:9200/elastalert_status' > /dev/null
curl -s -XDELETE 'http://127.0.0.1:9200/elastalert_status_error' > /dev/null
curl -s -XDELETE 'http://127.0.0.1:9200/elastalert_status_past' > /dev/null
curl -s -XDELETE 'http://127.0.0.1:9200/elastalert_status_silence' > /dev/null
curl -s -XDELETE 'http://127.0.0.1:9200/elastalert_status_status' > /dev/null
elastalert-create-index --host 127.0.0.1 --port 9200 --no-ssl --no-auth --url-prefix "" --index "elastalert_status" --old-index "" --config /etc/sysconfig/elastalert_config.yml

echo "reload kibana dashboards"
/usr/local/sbin/load_all_dashboards.sh

echo "stopping kibana"
systemctl stop kibana

echo "stopping filebeat service"
systemctl stop filebeat
echo "clearing filebeat data"
rm -rf /var/lib/filebeat

echo "removing elasticsearch .tasks index"
curl -s -XDELETE 'http://localhost:9200/.tasks' > /dev/null

echo "stopping network"
systemctl stop network

echo "stopping elasticsearch"
systemctl stop elasticsearch

echo "stopping logstash"
systemctl stop logstash

echo "stopping syslog"
systemctl stop rsyslog
echo "clearing existing log files"
find /var/log -type f -exec rm -f {} \;

echo "clearing SSH Host Keys"
systemctl stop sshd
rm -f /etc/ssh/*key*

echo "clearing cron/at content"
systemctl stop atd
systemctl stop crond
rm -f /var/spool/at/.SEQ
rm -f /var/spool/at/*

echo "clearing mail spools"
systemctl stop postfix
rm -f /var/spool/mail/root
rm -f /var/spool/mail/elk_user

echo "clearing /tmp/"
rm -rf /tmp/*

if [ $DISKSHRINK -eq 1 ]; then
    echo "ACTION REQUIRED!"
    echo "remove any snapshots that already exist and press Return"
    read

    # we don't use swap any more
    echo "zeroize swap:"
    swapoff -a
    for swappart in $( fdisk -l | grep swap | awk '{print $2}' | sed -e 's/:$//' ); do
        echo "- zeroize $swappart (swap)"
        dd if=/dev/zero of=$swappart
        mkswap $swappart
    done

    echo "shrink all drives:"
    for shrinkpart in $( vmware-toolbox-cmd disk list ); do
        vmware-toolbox-cmd disk shrink ${shrinkpart}
    done
fi

echo "updating /etc/issue file for boot message"
cat /etc/issue.prep | sed -e "s/<%REVNO%>/$revdate/" > /etc/issue
rm -f /etc/issue.stock
