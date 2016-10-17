# In order for ALL of these configuration files to work you will need to have logstash installed
# and place these conf files into /etc/logstash/conf.d

# Also, you will need to install the logstash translate community plugin.  This can be done
# by running this command:

/opt/logstash/bin/plugin install logstash-filter-translate

# You will also need to setup the frequency analysis tools or comment out anything using them (not 
# recommended).  To do this refer to the freq_readme.txt file found at
# https://github.com/SMAPPER/Logstash-Configs/blob/master/freq_readme.txt