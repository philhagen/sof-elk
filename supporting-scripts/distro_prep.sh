#!/bin/bash
# SOF-ELK® Supporting script
# (C)2025 Lewes Technology Consulting, LLC
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
echo "ACTION REQUIRED!  Is this the correct branch?  (Should be 'public/v*' or 'class/for123/v*' with  all others removed.)"
read

indices=$( curl -s -XGET 'http://localhost:9200/_cat/indices/' | grep -v " \.internal\| \.kibana" | sort )
if [ ! -z "${indices}" ]; then
    echo "ACTION REQUIRED!  The data above is still stored in elasticsearch.  Press return if this is correct or Ctrl-C to quit."
    echo "${indices}"
    read
fi

ingest_dir=$( find /logstash/ -mindepth 2 -print )
if [ ! -z "${ingest_dir}" ]; then
    echo "The following logs and subdirectories are still present in the ingest directory.  Press return if this is correct or Ctrl-C to quit."
    echo "${ingest_dir}"
    read
fi

echo "The following users are defined in /etc/password.  Press return if this is correct or Ctrl-C to quit."
awk -F: '$3>=1000 && $3<65000 {print "- "$1}' /etc/passwd
read

if [ -d ~elk_user/.ssh/ ]; then
    ssh_dir=$( find ~elk_user/.ssh/ -print )
    if [ ! -z "${ssh_dir}" ]; then
        echo "The following contents are in ~elk_user/.ssh/.  Press return if this is correct or Ctrl-C to quit."
        echo "${ssh_dir}"
        read
    fi
fi

echo "updating local git repo clones"
cd /usr/local/sof-elk/
SKIP_HOOK=1 git pull --all

echo "removing old kernels"
RUNNING_KERNEL=$( uname -r )
apt --yes purge $( apt list --installed | grep -Ei 'linux-image|linux-headers|linux-modules' | grep -v ${RUNNING_KERNEL} | awk -F/ '{print $1}' )

echo "removing unnecessary packages"
apt --yes autoremove

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
declare -A md5values
md5values["ASN"]="c20977100c0a6c0842583ba158e906ec"
md5values["City"]="4c60b3acf2e6782d48ce2b42979f7b98"
md5values["Country"]="849e7667913e375bb3873f8778e8fb17"
for GEOIPDB in ASN City Country; do
    file=GeoLite2-${GEOIPDB}.mmdb
    local_path=/usr/local/share/GeoIP/${file}
    md5=$( md5sum ${local_path} | awk '{print $1}' )
    if [ ${md5} != ${md5values[${GEOIPDB}]} ]; then
        echo "- ${local_path}"
        rm -f ${local_path}
        curl -s -L -o ${local_path} https://sof-elk.com/dist/${file}
        chmod 644 ${local_path}
    fi
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

read -p "Set the pre-login banner version for distribution? (Y/N)" set_distro_version
if [ ${set_distro_version} == "Y" ]; then
    echo "updating /etc/issue file for boot message"
    cat /etc/issue.prep | sed -e "s/<%REVNO%>/$revdate/" > /etc/issue
fi
