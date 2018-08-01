#!/bin/bash
# SOF-ELK® Supporting script
# (C)2016 Lewes Technology Consulting, LLC
#
# This script is used to perform post-merge steps, eg after the git repository is updated

# reload all dashboards
/usr/local/sbin/load_all_dashboards.sh

# activate all "supported" Logstash configuration files
for file in /usr/local/sof-elk/configfiles/*; do
    if [ -h /etc/logstash/conf.d/$( basename $file ) ]; then
        rm -f /etc/logstash/conf.d/$( basename $file )
    fi

    ln -s $file /etc/logstash/conf.d/$( basename $file )
done

# other housecleaning
LOGO_PATH="/usr/share/kibana/src/core_plugins/kibana/public/assets/sof-elk.svg"
if [ -a $LOGO_PATH ]; then
    rm -rf $LOGO_PATH
fi
ln -fs /usr/local/sof-elk/lib/sof-elk.svg $LOGO_PATH

# restart filebeat
/usr/bin/systemctl restart filebeat

# reload logstash
for lspid in $( ps -u logstash | grep java | awk '{print $1}' ); do
    kill -s HUP $lspid
done
