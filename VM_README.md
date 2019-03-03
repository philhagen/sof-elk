SOF-ELK® Virtual Machine Distribution
=======
![alt tag](https://raw.githubusercontent.com/philhagen/sof-elk/master/lib/sof-elk_logo_sm.png)

**Background**

This page contains details for the SOF-ELK® (Security Operations and Forensics Elasticsearch, Logstash, Kibana) VM.
The VM is provided as a community resource but is covered at varying depths in the following SANS course(s):

* [SANS FOR572, Advanced Network Forensics and Analysis](http://for572.com/course)
* [SANS SEC555, SIEM with Tactical Analysis](http://for572.com/sec555)
* [SANS SEC501, Advanced Security Essentials - Enterprise Defender](http://for572.com/sec501)

The latest version of the VM itself is available here: <http://for572.com/sof-elk-vm>

All parsers and dashboards for this VM are now maintained in this Github repository.  You can access them directly via <http://for572.com/sof-elk-git>

**General Information**

* The VM was created with VMware Fusion v11.0.2 and ships with virtual hardware v12.
  * If you're using an older version of VMware Workstation/Fusion/Player, you will likely need to convert the VM back to a previous version of the hardware.
  * Some VMware software provides this function via the GUI, or you may find the [free "VMware vCenter Converter" tool](http://www.vmware.com/products/converter) helpful.
* The VM is deployed with the "NAT" network mode enabled
* Credentials:
  * username: ```elk_user```
    * password: ```forensics```
    * has sudo access to run ALL commands
* Logstash will ingest all files from the following filesystem locations:
  * ```/logstash/syslog/```: Syslog-formatted data
  * ```/logstash/nfarch/```: Archived NetFlow output, formatted as described below
  * ```/logstash/httpd/```: Apache logs in common, combined, or vhost-combined formats
  * ```/logstash/passivedns/```: Logs from the passivedns utility
* NOTICE: Remember that syslog DOES NOT reflect the year of a log entry!  Therefore, Logstash has been configured to look for a year value in the path to a file.  For example:  ```/logstash/syslog/2015/var/log/messages``` will assign all entries from that file to the year 2015.  If no year is present, the current year will be assumed.  This is enabled only for the `/logstash/syslog/` directory.
* Commands to be familiar with:
    * ```/usr/local/sbin/sof-elk_clear.py```: DESTROY contents of the Elasticsearch database.  Most frequently used with an index name base (e.g. ```sof-elk_clear.py -i logstash``` will delete all data from the Elasticsearch ```logstash-*``` indexes.  Other options detailed with the ```-h``` flag.
    * ```/usr/local/sbin/sof-elk_update.sh```: Update the SOF-ELK® configuration files from the Github repository.  (Requires sudo.)
* Files to be familiar with:
    * ```/etc/logstash/conf.d/*.conf```: Symlinks to github-based FOR572-specific configs that address several common log formats:
        * syslog
        * DHCPD
        * BIND querylog
        * iptables
        * Squid access_log
        * Windows messages sent by Snare
        * Passivedns (<http://for572.com/passivedns>)
        * HTTPD Common/Combined/vhost+Combined/SSL Access Logs
        * Live NetFlow v5 and archived NetFlow records
    * ```/usr/local/sof-elk/*```: Clone of Github repository (<http://for572.com/sof-elk-git> - public/v20190102 branch)

**Latest Distribution Vitals**

* Basic details on the distribution
  * VM is a CentOS 7.5 base with all OS updates as of 2019-01-02
  * Includes Elastic stack components v6.5.3
  * Configuration files are from the "public/v20190102" branch of this Github repository
* Metadata
  * Filename and size: ```Public SOF ELK v20190102.zip``` (```1,707,502,761``` bytes)
  * MD5: ```8468fdce074445e6df6c0fcae791e1de```
  * SHA256: ```b6ae8f1f5ebc4792e6ad7d5a771316d7ab4b8855cf3928c34925b2851fb3a2a7```

**How to Use**

* Restore the "Deployment" snapshot
* Boot the VM
* Log into the VM with the ```elk_user``` credentials (see above)
  * Logging in via SSH recommended, but if using the console login and a non-US keyboard, run ```sudo loadkeys uk```, replacing ```uk``` as needed for your local keyboard mapping
* cd to one of the ```/logstash/*/``` directories as appropriate
* Place files in this location (Mind the above warning about the year for syslog data.  Files must also be readable by the "logstash" user.)
* Open the main Kibana dashboard using the Kibana URL shown in the pre-authentication screen, ```http://<ip_address>:5601```
    * This dashboard gives a basic overview of what data has been loaded and how many records are present
    * There are links to several stock dashboards on the left hand side
* Wait for Logstash to parse the input files, load the appropriate dashboard URL, and start interacting with your data

**Sample Data Included**

* Syslog data in `~elk_user/lab-2.3_source_evidence/`
  * Unzip each of these files **into the `/logstash/syslog/` directory**, such as: `cd /logstash/syslog/ ; unzip ~elk_user/lab-2.3_source_evidence/<file>`
  * Use the time frame `2013-06-08 15:00:00` to `2013-06-08 23:30:00` to examine this data.
* NetFlow data in `~elk_user/lab-3.1_source_evidence/`
  * Use the `nfdump2sof-elk.sh` script and write output **to the `/logstash/nfarch/` directory**, such as: `cd /home/elk_user/lab-3.1_source_evidence/ ; nfdump2sof-elk.sh -e 10.3.58.1 -r ~elk_user/lab-3.1_source_evidence/netflow/ -w /logstash/nfarch/lab-3.1_netflow.txt`
  * Use the time frame `2012-04-02` to `2012-04-07` to examine this data.

**Ingesting Archived NetFlow**

To ingest existing NetFlow evidence, it must be parsed into a specific format.  The included ```nfdump2sof-elk.sh``` script will take care of this.
* Read from single file: ```nfdump2sof-elk.sh -r /path/to/netflow/nfcapd.201703190000 -w /logstash/nfarch/inputfile_1.txt```
* Read recursively from directory: ```nfdump2sof-elk.sh -r /path/to/netflow/ -w /logstash/nfarch/inputfile_2.txt```
* Optionally, you can specify the IP address of the exporter that created the flow data: ```nfdump2sof-elk.sh -e 10.3.58.1 -r /path/to/netflow/ -w /logstash/nfarch/inputfile_3.txt```

**Credits**
* Derek B: Cisco ASA parsing/debugging and sample data
* Barry A: Sample data and trobuleshooting
* Ryan Johnson: Testing
* Matt Bromiley: Testing
* Mike Pilkington: Testing
* Mark Hallman: Testing

**Administrative Notifications/Disclaimers/Legal/Boring Stuff**

* This virtual appliance is provided "as is" with no express or implied warranty for accuracy or accessibility.  No support for the functionality the VM provides is offered outside of this document.
* This virtual appliance includes GeoLite2 data created by MaxMind, available from <http://www.maxmind.com>
* SOF-ELK® is a registered trademark of Lewes Technology Consulting, LLC.  Content is copyrighted by its respective contributors.  SOF-ELK logo is a wholly owned property of Lewes Technology Consulting, LLC and is used by permission.
