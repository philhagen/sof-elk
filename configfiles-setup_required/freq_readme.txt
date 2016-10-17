# I use freq.py quite often to do frequency analysis on logs.  To do this you need to create a /opt/freq folder and then download freq.py to it.  Then you need # to download my frequency tables from the freq folder on this github page.

# You can generate your own frequency tables by looking at freq.py's built-in help.
# Freq.py is a standlone python script to do this found at https://github.com/MarkBaggett/MarkBaggett/blob/master/freq/freq.py

#Example:

mkdir /opt/freq
wget https://github.com/MarkBaggett/MarkBaggett/raw/master/freq/freq_server.py
chmod +x /opt/freq/freq_server.py
wget https://github.com/SMAPPER/Logstash-Configs/raw/master/configfiles-setup_required/freq/uri.freq
wget https://github.com/SMAPPER/Logstash-Configs/raw/master/configfiles-setup_required/freq/dns.freq
wget https://github.com/SMAPPER/Logstash-Configs/raw/master/configfiles-setup_required/freq/file.freq
wget https://github.com/SMAPPER/Logstash-Configs/raw/master/configfiles-setup_required/freq/pdf.freq

# To make this a service using systemd (assuming Ubuntu 16.04)

cd /etc/systemd/system
wget https://github.com/SMAPPER/Logstash-Configs/raw/master/configfiles-setup_required/freq/freq-http.service
wget https://github.com/SMAPPER/Logstash-Configs/raw/master/configfiles-setup_required/freq/freq-dns.service
systemctl daemon-reload
systemctl enable freq-http.service
systemctl enable freq-dns.service
systemctl start freq-http.service
systemctl start freq-dns.service