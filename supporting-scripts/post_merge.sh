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

/usr/bin/systemctl restart filebeat
/usr/bin/systemctl reload logstash