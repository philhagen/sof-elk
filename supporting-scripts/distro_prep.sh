#!/bin/bash
# SOF-ELK® Supporting script
# (C)2024 Lewes Technology Consulting, LLC
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

echo "Checking that we're on the correct SOF-ELK® branch"
cd /usr/local/sof-elk/
git branch
echo "ACTION REQUIRED!  Is this the correct branch?  (Should be 'public/v*', 'class/v*', or e.g. 'for123/v*' with  all others removed.)"
read

indices=$( curl -s -XGET 'http://localhost:9200/_cat/indices/' | grep -v " \.internal\| \.kibana" | sort )
if [ ! -z "${indices}" ]; then
    echo "ACTION REQUIRED!  The data above is still stored in elasticsearch.  Press return if this is correct or Ctrl-C to quit."
    read
fi

ingest_dir=$( find /logstash/ -mindepth 2 -print )
if [ ! -z ${ingest_dir} ]; then
    echo "The following logs and subdirectories are still present in the ingest directory.  Press return if this is correct or Ctrl-C to quit."
    read
fi

echo "The following users are defined in /etc/password.  Press return if this is correct or Ctrl-C to quit."
awk -F: '$3>=1000 && $3<65000 {print "- "$1}'
read

if [ -d ~elk_user/.ssh/ ]; then
    ssh_dir=$( find ~elk_user/.ssh/ -print )
    if [ ! -z ${ssh_dir} ]; then
        echo "The following contents are in ~elk_user/.ssh/.  Press return if this is correct or Ctrl-C to quit."
        read
    fi
fi

echo "updating local git repo clones"
cd /usr/local/sof-elk/
SKIP_HOOK=1 git pull --all

echo "removing old kernels"
RUNNING_KERNEL=$( uname -r )
apt --yes purge $( apt list --installed | grep -Ei 'linux-image|linux-headers|linux-modules' | grep -v ${RUNNING_KERNEL} | awk -F/ '{print $1}' )
echo "cleaning apt caches"
apt-get clean

echo "cleaning user home directories"
for userclean in root elk_user; do
    rm -f ~${userclean}/.bash_history
    rm -f ~${userclean}/.python_history
    rm -f ~${userclean}/.lesshst
    rm -rf ~${userclean}/.local
    rm -rf ~${userclean}/.cache
    rm -rf ~${userclean}/.vim
    rm -rf ~${userclean}/.viminfo
    rm -rf ~${userclean}/.bundle
    rm -rf ~${userclean}/.ansible
    rm -rf ~${userclean}/.config
    rm -rf ~${userclean}/.vscode-server
done
#cat /dev/null > ~/.bash_history; history -c ; history -w; exit

echo "cleaning temp directories"
rm -rf ~elk_user/tmp/*

echo "Resetting GeoIP databases to distributed versions."
for GEOIPDB in ASN City Country; do
    rm -f /usr/local/share/GeoIP/GeoLite2-${GEOIPDB}.mmdb
    curl -s -L -o /usr/local/share/GeoIP/GeoLite2-${GEOIPDB}.mmdb https://lewestech.com/dist/GeoLite2-${GEOIPDB}.mmdb
    chmod 644 /usr/local/share/GeoIP/GeoLite2-${GEOIPDB}.mmdb
done
rm -f /etc/GeoIP.conf
rm -f /etc/cron.d/geoipupdate

# echo "stopping domain-stats"
# systemctl stop domain-stats
# echo "clearing domain-stats data"
# rm -rf /usr/local/share/domain-stats/[0-9][0-9][0-9]/
# rm -f /usr/local/share/domain-stats/domain-stats.log
# rm -rf /usr/local/share/domain-stats/memocache/
# rm -rf /usr/local/share/domain-stats/__pycache__/
# echo "reloading top 1m for domain-stats from scratch"
# domain-stats-utils -i /usr/local/lib/python3.6/site-packages/domain_stats/data/top1m.import -nx /usr/local/share/domain-stats/

# echo "stopping elastalert"
# systemctl stop elastalert
# echo "clearing elastalert"
# curl -s -XDELETE 'http://127.0.0.1:9200/elastalert_status' > /dev/null
# curl -s -XDELETE 'http://127.0.0.1:9200/elastalert_status_error' > /dev/null
# curl -s -XDELETE 'http://127.0.0.1:9200/elastalert_status_past' > /dev/null
# curl -s -XDELETE 'http://127.0.0.1:9200/elastalert_status_silence' > /dev/null
# curl -s -XDELETE 'http://127.0.0.1:9200/elastalert_status_status' > /dev/null
# elastalert-create-index --host 127.0.0.1 --port 9200 --no-ssl --no-auth --url-prefix "" --index "elastalert_status" --old-index "" --config /etc/sysconfig/elastalert_config.yml

echo "reloading kibana dashboards"
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
ifconfig ens33 down

echo "stopping elasticsearch"
systemctl stop elasticsearch

echo "stopping logstash"
systemctl stop logstash

echo "clearing SSH Host Keys"
systemctl stop ssh.socket
rm -f /etc/ssh/*key*

echo "clearing cron/at content"
systemctl stop atd
systemctl stop cron
rm -f /var/spool/cron/atjobs/.SEQ
rm -rf /var/spool/cron/atjobs/*

echo "clearing mail spools"
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
