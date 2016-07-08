sof-elk
=======
![alt tag](https://raw.githubusercontent.com/philhagen/sof-elk/master/lib/sof-elk_logo_sm.png)


This repository contains the configuration and support files for the SANS FOR572 Logstash VM Appliance.  More details about the pre-packaged VM are available here: <http://for572.com/logstash-readme>.

**Branches:**

* `master`: This branch is considered suitable for widespread use, but should not be used in the FOR572 class itself.  The classroom labs are version-locked, but work on this repository is ongoing.
* `develop`: This branch contains code that should be functional, but may break at times (and remain broken).  Of course, we'll try to avoid that, but it should be clear that this is NOT a branch suitable for "real world" use.
* `feature/*`:  Branches where new code functionality is tested before being merged into develop.
* `hotfix/*`: Branches where quick-term fixes are tested before being merged into develop and immediately to master.
* `release/*`: Branches where code in the develop branch is prepared for release to a VM build via a merge to master.
* Other branches may be used for major version updates, etc.  These will be merged to master when deployed for mainstream use.

**Tags:**

When a VM is prepared for distribution in the SANS FOR572 course, the revision will be tagged with a corresponding date-based version (e.g. "2014-12-18").  Users may want to consider updating to the contents of the "master" branch, but at times, this branch will expect updates to the Logstash VM itself.  Release notes on the github page (located at <http://for572.com/sof-elk-git>) will alert users when such system-level changes are required.

**Using:**

The various configuration files expect some of these files to reside at a specific path on the filesystem.  For this reason, we recommend you clone the git repository to ```/usr/local/sof-elk/```.  To use these configuration files, I recommend symlinking them into ```$LS_CONF_DIR``` as defined by your configuration file.

**Contents by directory:**

* `/dashboards/`: These files define the Kibana dashboards for individual data types.  These correspond with the parsing completed by the Logstash files in the ```/configfiles/``` directory, so they probably won't work on your own Logstash instance without some tweaking.  Note that with Kibana 4, dashboards are only kept in the Elastic database, so to load these to the interface, set ```$reset_dashboards``` to ```1``` and run the ```/dashboards/load_all_dashboards.sh``` script.
* `/configfiles/`: These files conatain parsing/tagging/formatting/etc logic for individual file types as well as output configuration.
* `/grok-patterns/`: Custom parsing patterns used by the files in the ```/configfiles/``` directory.
* `/lib/`: Supporting files, including elasticsearch mappings, YAML lookup files, and images.

**Questions/Bug Reports/etc:**

All bugs and feature requests should be logged via the github issue tracker: <https://github.com/philhagen/sof-elk/issues/>.
