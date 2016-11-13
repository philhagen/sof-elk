# I use freq.py quite often to do frequency analysis on logs.  To do this you need to create a /opt/freq folder and then download freq.py to it.  Then you need # to download my frequency tables from the freq folder on this github page.

# You can generate your own frequency tables by looking at freq.py's built-in help.
# Freq.py is a standlone python script to do this found at https://github.com/MarkBaggett/MarkBaggett/blob/master/freq/freq.py

#Example:

sudo mkdir /opt/freq
cd /opt/freq
sudo wget https://github.com/MarkBaggett/MarkBaggett/raw/master/freq/freq.py
sudo wget https://github.com/MarkBaggett/MarkBaggett/raw/master/freq/freq_server.py
sudo chmod +x /opt/freq/freq_server.py
sudo wget https://github.com/SMAPPER/Logstash-Configs/raw/master/configfiles-setup_required/freq/uri.freq
sudo wget https://github.com/SMAPPER/Logstash-Configs/raw/master/configfiles-setup_required/freq/dns.freq
sudo wget https://github.com/SMAPPER/Logstash-Configs/raw/master/configfiles-setup_required/freq/file.freq
sudo wget https://github.com/SMAPPER/Logstash-Configs/raw/master/configfiles-setup_required/freq/pdf.freq
sudo wget https://github.com/SMAPPER/Logstash-Configs/raw/master/configfiles-setup_required/freq/freq.sh
sudo chmod +x freq.sh

# To make this a service using systemd (assuming Ubuntu 16.04)

cd /etc/systemd/system
sudo wget https://github.com/SMAPPER/Logstash-Configs/raw/master/configfiles-setup_required/freq/freq-http.service
sudo wget https://github.com/SMAPPER/Logstash-Configs/raw/master/configfiles-setup_required/freq/freq-dns.service
sudo systemctl daemon-reload
sudo systemctl enable freq-http.service
sudo systemctl enable freq-dns.service
sudo systemctl start freq-http.service
sudo systemctl start freq-dns.service

# To make this a service using init.d (older OSes)

cd /etc/init.d/
sudo wget https://github.com/SMAPPER/Logstash-Configs/raw/master/configfiles-setup_required/freq/freq
sudo chmod +x freq
sudo service freq start

