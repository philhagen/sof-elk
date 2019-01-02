SOF-ELK® VM Distribution
=======
![alt tag](https://raw.githubusercontent.com/philhagen/sof-elk/master/lib/sof-elk_logo_sm.png)

**Background**

This page contains details for the SOF-ELK® (Security Operations and Forensics Elasticsearch, Logstash, Kibana) VM.
The VM is provided as a community resource but is covered in depth in the following course(s):

* [SANS FOR572, Advanced Network Forensics and Analysis](http://for572.com/course)
* [SANS SEC555, SIEM with Tactical Analysis](http://for572.com/sec555)

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

**Changelog**

* Update: 2019-01-02: Updated to ES 6.5.3 components
  * Updated system components to latest CentOS 7.6
  * Updated all Elastic Stack components to 6.5.3
  * Numerous other config file, parser, and dashboard updates as documented in the Git history
* Update: 2018-09-18: All-new with 6.4.1
  * VM was rebuilt entirely from scratch with all Elastic stack components at v6.4.0
  * Updated system components to match latest CentOS 7.5
  * Rebuilt and revalidated all Logstash parsers against latest syntax
  * Total overhaul of most supporting_scripts files to address latest Elasticsearch and Kibana APIs
  * Latest versions of domain_stats and freq_server
  * Better handling of dynamic (boot-time) memory allocation for Elasticsearch
  * Moved to MaxMind GeoIP2 format (required by this version of Logstash)
  * Updated several Logstash parsers to handle new fields, correct field types, etc.
  * Rebuilt all Kibana dashboards to handle updated index mappings and field names
  * IPv6 addresses can now be handled as IPs instead of strings
* Update: 2017-05-18: Another MAJOR update!
  * Daily checks for upstream updates in the Github repository, with advisement on login if updates are available
  * Added dozens of parser configurations from Justin Henderson, supporting the SANS SEC555 class
  * Added experimental Plaso data ingest features, contributed by Mark McCurdy
  * Added freq_server and domain_stats as localhost-bound services
  * Added HTML visualization type to Kibana
  * Dynamically calculate ES_HEAP_SIZE
  * Uses a locally-running filebeat process for file ingest instead of logstash's file inputs
  * Replaced es_nuke.sh with sof-elk_clear.py, adding by-file/by-directory clear and optional reload from disk
  * Overall file cleanup
  * Enforce field naming consistency
  * Various updates to dashboards and parsers
  * Ingest locations changed to ```/logstash/*/```
  * Increased VM's default RAM to 4GB
* Update: 2016-07-08: This is a MAJOR update!
  * Complete overhaul of the VM
  * Re-branded to SOF-ELK®, with awesome logo to boot
  * Now uses CentOS 7.x as a base OS
  * Latest releases of the ELK stack components
  * All dashboards re-created to work in Kibana 4
  * Optimized Logstash parsing
  * Better post-deployment upgradability path
  * Far more than can be adequately documented here - see the git logs for all the details
  * No longer includes the Xplico application
* Update: 2015-09-18
  * Adjusted sample source evidence to correspond to the UTC change
  * Re-configured Xplico to start on boot (not Logstash-related)
* Update: 2015-07-16
  * Force permanence for UTC (seriously, why doesn't replacing /etc/localtime last an update to the tzdata package?!)
  * Updated all packages
* Update: 2015-05-05
  * Uses separate ElasticSearch instance instead of Logstash's embedded version (also disabled Groovy scripting engine to address CVE-2015-1427)
  * Uses github-based configuration files, grok patterns, and dashboards (tag 2015-05-05)
  * Updated all packages
* Update: 2015-03-21
  * Corrects that somehow the time zone was set to US Eastern instead of UTC, which is unforgivable
* Update: 2015-03-20
  * Modified the embedded ElasticSearch server configuration to mitigate CVE-2015-1427 by disabling the Groovy scripting engine.
* Update: 2015-01-01
  * Modified the Kibana configuration so the for572.json dashboard is REALLY loaded as the default.
  * Updated all packages
* Update: 2014-12-18
  * Corrected a Squid log parsing error
  * corrected the Kibana "Home" dashboard to be the FOR572 summary/instruction dashboard
  * Updated all packages
* Update: 2014-12-03: This is a MAJOR update!
  * Parsing has been updated and is far more robust.  The VM cleanly ingests all known data, but let me know if there is any standard data that's not parsed correctly.
  * The VM can ingest live NetFlow v5 by opening UDP port 9995 in the firewall with the following commands using sudo:
    * ```fw_modify.sh -a open -p 9995 -r udp```
  * Archived NetFlow (e.g. ASCII output from nfdump) is ingested just as live NetFlow, so you can load historical evidence alongside live data, and use the same dashboard to examine both simultaneously.  See the "Ingesting Archived NetFlow" section for details on this process.
  * Cisco ASA events sent via syslog are fully parsed
  * Much, much more!

**Ingesting Archived NetFlow**

To ingest existing NetFlow evidence, it must be parsed into a specific format.  The included ```nfdump2sof-elk.sh``` script will take care of this.
* Read from single file: ```nfdump2sof-elk.sh -r /path/to/netflow/nfcapd.201703190000 -w /logstash/nfarch/inputfile_1.txt```
* Read recursively from directory: ```nfdump2sof-elk.sh -r /path/to/netflow/ -w /logstash/nfarch/inputfile_2.txt```
* Optionally, you can specify the IP address of the exporter that created the flow data: ```nfdump2sof-elk.sh -e 10.3.58.1 -r /path/to/netflow/ -w /logstash/nfarch/inputfile_3.txt```

**Sample Data**

Some sample data is available in the ```~elk_user/exercise_source_logs/``` directory.  Unzip this to the ```/logstash/syslog/``` directory and check out the syslog dashboard to get a quick feel for the overall process.

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
