# If you have sflow and want to collect the data to logstash I recommend downloading and installing
#  sflowtool on one or more systems. Then download my sflowtool_init_script.txt and rename it and 
# put it in /etc/init.d/.  I recommend just naming it sflowtool.  Then set it to auto start and point
# all your syslog devices at it using port 6343.  This will convert the sflow into netflow v5 data
# and logstash can parse it.

# Installing sflowtool
# May need to change autoreconf-2.13 to whatever your distro has for autoreconf
apt-get install build-essential make autoreconf-2.13 git
git clone https://github.com/sflow/sflowtool.git
cd sflowtool
./boot.sh
./configure
make
make install

# In the current incarnation of the sflowtool_init_script I'm assuming you put sflowtool 
# on the logstash hosts so it sends the converted netflow v5 data to 127.0.0.1 on the port
# logstash is expecting it (based on my netflow.conf file).

# Example of setup (assumes you've installed sflowtool first):

wget https://github.com/SMAPPER/Logstash-Configs/raw/master/misc/sflowtool_init_script.txt
mv sflowtool_init_script.txt /etc/init.d/sflowtool
update-rc.d sflowtool defaults
chmod +x /etc/init.d/sflowtool
service sflowtool start