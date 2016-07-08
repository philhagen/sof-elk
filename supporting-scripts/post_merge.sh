#!/bin/bash

# load all dashboards to the kibana ES index
/usr/local/sbin/load_all_dashboards.sh

# activate all "supported" Logstash configurations
for file in /usr/local/sof-elk/configfiles/*; do
    if [ -h /etc/logstash/conf.d/$( basename $file ) ]; then
        rm -f /etc/logstash/conf.d/$( basename $file )
    fi

    ln -s $file /etc/logstash/conf.d/$( basename $file )
done
