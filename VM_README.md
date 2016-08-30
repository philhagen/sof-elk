# SOF-ELK VM Distribution #
![alt tag](https://raw.githubusercontent.com/philhagen/sof-elk/master/lib/sof-elk_logo_sm.png)

## Background ##
This page contains details for the SOF-ELK (Security Operations and Forensics Elasticsearch, Logstash, Kibana) VM.
The VM is provided as a community resource but is covered in depth in the following course(s):

* [SANS FOR572, Advanced Network Forensics and Analysis](http://for572.com/course)

The latest version of the VM itself is available here: <http://for572.com/sof-elk-vm>

All parsers and dashboards for this VM are now maintained in this Github repository.  You can access them directly via <http://for572.com/sof-elk-git>

## General Information ##
* The VM was created with VMware Fusion v8.1.1 and ships with virtual hardware v10.
  * If you're using an older version of VMware Workstation/Fusion/Player, you will likely need to convert the VM back to a previous version of the hardware.
  * Some VMware software provides this function via the GUI, or you may find the [free "VMware vCenter Converter" tool](http://www.vmware.com/products/converter) helpful.
* The "Deployment" snapshot is a "known-good" state, which is used as a basis for use in the FOR572 classroom materials
* The VM is deployed with the "NAT" network mode enabled
* Credentials:
  * username: ```elk_user```
    * password: ```forensics```
    * has sudo access to run ALL commands
* Logstash will ingest all files from the following filesystem locations:
  * ```/usr/local/logstash-syslog/```: Syslog-formatted data
  * ```/usr/local/logstash-nfarch/```: Archived NetFlow output, formatted as described below
  * ```/usr/local/logstash-httpd/```: Apache logs in common, combined, or vhost-combined formats
  * ```/usr/local/logstash-passivedns/```: Logs from the passivedns utility
* NOTICE: Remember that syslog DOES NOT reflect the year of a log entry!  Therefore, Logstash has been configured to look for a year value in the path to a file.  For example:  ```/usr/local/logstash-syslog/2015/var/log/messages``` will assign all entries from that file to the year 2015.  If no year is present, the current year will be assumed.  This is enabled only for the "logstash-syslog" directory.
* Commands to be familiar with:
    * ```/usr/local/sbin/es_nuke.sh```: DESTROY contents of the Elasticsearch database.  Requires an index name base (e.g. ```es_nuke.sh syslog``` will delete all data from the Elasticsearch ```syslog-*``` indexes.
    * ```/usr/local/sbin/ls_restart.sh```: Restarts Logstash daemon, activating any changes to the configuration files.  Include the ```-reparse``` option to re-read all files still on the filesystem.  The ```-reparse``` option will result in duplicate entries unless you've used ```es_nuke.sh``` as needed.  (Requires sudo.)
    * ```/usr/local/sbin/sof-elk-update.sh```: Update the SOF-ELK configuration files from the Github repository.  (Requires sudo.)
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
    * ```/usr/local/sof-elk/*```: Clone of Github repository (<http://for572.com/sof-elk-git> - master branch)

## Latest Distribution Vitals ##
* Basic details on the distribution
  * VM is a CentOS 7.2 base with all updates as of 2016-07-08
  * Includes Elasticsearch 2.3.4, Logstash 2.2.4, and Kibana 4.5.2
  * Configuration files are from the "classroom" branch of this Github repository (tag 2016-07-08)
* Metadata
  * Filename and size: ```FOR572 SOF-ELK 2016-08-17.zip``` (830019192 bytes)
  * MD5: ```c2eebe809e953a8b580d859525592236```
  * SHA256: ```6019b849b367633a5dbac1f9ec27c7b1ecabbac1e107bbb6d73d2194a44cfbc2```

## How to Use ##
* Restore the "Deployment" snapshot
* Boot the VM
* Log into the VM with the ```elk_user``` credentials (see above)
* cd to one of the ```/usr/local/logstash-*/``` directories as appropriate
* Place files in this location (Mind the above warning about the year for syslog data.  Files must also be readable by the "logstash" user.)
* Open the main Kibana dashboard using the Kibana URL shown in the pre-authentication screen, ```http://<ip_address>:5601```
    * This dashboard gives a basic overview of what data has been loaded and how many records are present
    * There are links to several stock dashboards on the left hand side
* Wait for Logstash to parse the input files, load the appropriate dashboard URL, and start interacting with your data

## Changelog ##
* Update: future-pending
  * Dynamically calculate ES_HEAP_SIZE
  * Add HTML Visualization type
* Update: 2016-07-08: This is a MAJOR update!
  * Complete overhaul of the VM
  * Re-branded to SOF-ELK, with awesome logo to boot
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
    * ```firewall-cmd --zone=public --add-port=9995/udp --permanent```
    * ```firewall-cmd --reload```
  * Archived NetFlow (e.g. ASCII output from nfdump) is ingested just as live NetFlow, so you can load historical evidence alongside live data, and use the same dashboard to examine both simultaneously.  See the "Ingesting Archived NetFlow" section for details on this process.
  * Cisco ASA events sent via syslog are fully parsed
  * Much, much more!

## Ingesting Archived NetFlow ##
To ingest existing NetFlow evidence, it must be parsed into a specific format.  The nfdump command line needed to parse existing data is below.  Be sure you review the top of the output file to ensure there are no warning/error messages present.

```export EXP_IP=1.1.1.1``` (Replace ```1.1.1.1``` with the exporter source for the data, if available.  This field is required and must be a valid IPv4 address, but use a placeholder if needed.)

```nfdump (-r <input file> | -R <input dir>) -q -N -O tstart -o "fmt:$EXP_IP %das %dmk %eng %ts %fl 0 %byt %pkt %in %da %nh %sa %dp %sp %te %out %pr 0 0 %sas %smk %stos %flg 0" > /path/to/some_file.txt```  (Then place ```some_file.txt``` in ```/usr/local/logstash-nfarch```.)

## Sample Data ##
Some sample data is available in the ```~ls_user/exercise_source_logs/``` directory.  Unzip this to the ```/usr/local/logstash-syslog/``` directory and check out the syslog dashboard to get a quick feel for the overall process.

## Credits ##
* Derek B: Cisco ASA parsing/debugging and sample data
* Barry A: Sample data and trobuleshooting
* Ryan Johnson: Testing
* Matt Bromiley: Testing

## Administrative Notifications/Disclaimers/Legal/Boring Stuff ##
* This virtual appliance is provided "as is" with no express or implied warranty for accuracy or accessibility.  No support for the functionality the VM provides is offered outside of this document.
* This virtual appliance includes GeoLite2 data created by MaxMind, available from <http://www.maxmind.com>
