#!/bin/bash
python /opt/freq/freq_server.py 10001 /opt/freq/dns.freq &
python /opt/freq/freq_server.py 10002 /opt/freq/dns.freq &
python /opt/freq/freq_server.py 10003 /opt/freq/english_lowercase.freq &
python /opt/freq/freq_server.py 10004 /opt/freq/dns.freq &
