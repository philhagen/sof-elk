#To setup alexa top 1 million checking against records you have to setup the following:
#copy all alexa files to /etc/logstash/conf.d

cd /etc/logstash/conf.d
sudo wget https://github.com/SMAPPER/Logstash-Configs/raw/master/configfiles-setup_required/0035_input_alexa.conf
sudo wget https://github.com/SMAPPER/Logstash-Configs/raw/master/configfiles-setup_required/1035_preprocess_alexa.conf
sudo wget https://github.com/SMAPPER/Logstash-Configs/raw/master/configfiles-setup_required/8007_postprocess_dns_alexa_tagging.conf
sudo wget https://github.com/SMAPPER/Logstash-Configs/raw/master/configfiles-setup_required/9901_output_alexa.conf
sudo service logstash restart

# Then schedule alexa_update.sh to run once a day

sudo mkdir /scripts
cd /scripts
sudo wget https://github.com/SMAPPER/Logstash-Configs/raw/master/scripts/alexa_update.sh

crontab <<EOF
0 0 * * * /scripts/alexa_update.sh
EOF
sudo chmod +x alexa_update.sh
sudo bash alexa_update.sh