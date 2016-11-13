# In order for ALL of these configuration files to work you will need to have logstash installed
# and place these conf files into /etc/logstash/conf.d

# Also, you will need to install the logstash translate community plugin.  This can be done
# by running this command:
#
# These have been tested on Logstash 2.4.  Older versions that do not have bin/logstash-plugin and
# instead use bin/plugin have issues.

sudo /opt/logstash/bin/logstash-plugin install logstash-filter-translate
sudo /opt/logstash/bin/logstash-plugin install logstash-filter-tld
sudo /opt/logstash/bin/logstash-plugin install logstash-filter-rest
sudo /opt/logstash/bin/logstash-plugin install logstash-filter-elasticsearch

# Also follow the readmes for specific things you wish to setup such as frequency_analysis, alexa lookups,
# message queuing, etc.
