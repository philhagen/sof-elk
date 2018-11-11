SOF-ELK® Configuration Files
=======
![alt tag](https://raw.githubusercontent.com/philhagen/sof-elk/master/lib/sof-elk_logo_sm.png)

This repository contains the configuration and support files for the SANS FOR572 SOF-ELK® VM Appliance.

SOF-ELK® is a “big data analytics” platform focused on the typical needs of computer forensic investigators/analysts and information security operations personnel.  The platform is a customized build of the open source ELK stack, consisting of the Elasticsearch storage and search engine, Logstash ingest and enrichment system, and the Kibana dashboard frontend.  With a significant amount of customization and ongoing development, SOF-ELK® users can avoid the typically long and involved setup process the ELK stack requires.  Instead, they can simply download the pre-built and ready-to-use SOF-ELK® virtual appliance that consumes various source data types (numerous log types as well as NetFlow), parsing out the most critical data and visualizing it on several stock dashboards.  Advanced users can build visualizations the suit their own investigative or operational requirements, optionally contributing those back to the primary code repository.

The SOF-ELK® platform was initially developed for SANS FOR572, Advanced Network Forensics and Analysis, and is now used in SEC555, SIEM with Tactical Analysis, with additional course integrations being considered.  Most importantly, the platform is also distributed as a free and open source resource for the community at large, without a specific course requirement or tie-in required to use it.

More details about the pre-packaged VM are available here: <http://for572.com/sof-elk-readme>.

**Branches:**

* `master`: This branch is considered suitable for widespread use, but should not be used in the FOR572 class itself.  The classroom labs are version-locked, but work on this repository is ongoing.
* `public/*`: These branches will be tied to public releases of the VM, allowing version-locked content control after deployment.
* `class/*`: When a VM is prepared for distribution in a SANS course such as FOR572, a new sub-branch will be created under the "class" branch with a name corresponding to the VM version.  (e.g. "```class/v20170629```").
* `develop`: This branch contains code that should be functional, but may break at times (and remain broken).  Of course, we'll try to avoid that, but it should be clear that this is NOT a branch suitable for "real world" use.
* `feature/*`:  Branches where new code functionality is tested before being merged into develop.
* `hotfix/*`: Branches where quick-term fixes are tested before being merged into develop and immediately to master.
* `release/*`: Branches where code in the develop branch is prepared for release to a VM build via a merge to master.
* Other branches may be used for major version updates, etc.  These will be merged to master when deployed for mainstream use.

**Using:**

The various configuration files expect some of these files to reside at a specific path on the filesystem.  For this reason, we recommend you clone the git repository to ```/usr/local/sof-elk/```.  To use these configuration files, I recommend symlinking them into ```$LS_CONF_DIR``` as defined by your configuration file.

**Contents by directory:**

* `/dashboards/`: These files define the Kibana dashboards for individual data types.  These correspond with the parsing completed by the Logstash files in the ```/configfiles/``` directory, so they probably won't work on your own Logstash instance without some tweaking.  Note that with Kibana 4, dashboards are only kept in the Elastic database, so to load these to the interface, run the ```/dashboards/load_all_dashboards.sh``` script.
* `/configfiles/`: These files conatain parsing/tagging/formatting/etc logic for individual file types as well as output configuration.
* `/grok-patterns/`: Custom parsing patterns used by the files in the ```/configfiles/``` directory.
* `/lib/`: Supporting files, including elasticsearch mappings, YAML lookup files, and images.

**Questions/Bug Reports/etc:**

All bugs and feature requests should be logged via the github issue tracker: <https://github.com/philhagen/sof-elk/issues/>.

Please see the pull request submission guidelines before starting any development work - this is in the PULLREQUESTS.md file.

**Administrative Notifications/Disclaimers/Legal/Boring Stuff**

* Content of this repository are provided "as is" with no express or implied warranty for accuracy or accessibility.
* SOF-ELK® is a registered trademark of Lewes Technology Consulting, LLC.  Content is copyrighted by its respective contributors.  SOF-
ELK logo is a wholly owned property of Lewes Technology Consulting, LLC and is used by permission.
