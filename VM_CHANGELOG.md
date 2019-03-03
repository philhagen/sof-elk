SOF-ELK® Virutal Machine Changelog
=======

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