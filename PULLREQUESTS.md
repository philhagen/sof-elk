Submitting Pull Requests
========================

The code in this repository is used in a number of different environments, so these pull request guidelines are designed to allow the various moving parts to continue working.  Please take a moment to read them before submitting a pull request - in fact, before doing any customization.

*PLEASE NOTE*: These guidelines are rudimentary and will certainly be changed in the future.  We still would greatly appreciate your help, but please contact a developer (@PhilHagen) for help before proceeding if you plan to submit a complex PR.  We just want to prevent you from undergoing our own headaches down the road.

1. All development must be done from the "develop" branch.  PRs against master will not be accepted.
2. Do not modify the included stock dashboards, except for bug-level edits.  New dashboards will be considered, but as the codebase is designed to address a broad community, highly customized dashboards may not be accepted into master.
3. Any custom parsers must be created in the `/configfiles-UNSUPPORTED/` subdirectory.  Any that are suitable for universal deployment will be moved to the `/configfiles/` subdirectory by the SOF-ELK® team.
4. All IP addresses pulled via grok must be in a field with a name formatted as such: `<directionality>_ip` or `<use_case>_ip`
    * Examples: `source_ip`, `destination_ip`, `relay_ip`, `answer_ip`
5. All IP addresses must be enriched with the GeoIP location and ASN filters (see existing files for examples)
6. All IP addresses must be added to the "ips" array field (see existing files for examples)

Consult the [sample Filebeat prospector](lib/filebeat_inputs/filebeat_template.yml.sample) for information on how to create a new Filebeat log source.  If extending an existing log type (e.g. syslog), this is not needed.

Consult the [sample parsing configuration file](configfiles/6xxx-parsing_template.conf.sample) for information on how to build a filter configuration file.

Consult the [sample output configuration file](confgfiles/configfiles/9xxx-output-template.conf.sample) for information on how to build an output configuration file.  If extending an existing log type (e.g. syslog), this is not needed.

Consult the [sample template file](lib/elasticsearch-example-template.json.sample) for a basic Elasticsearch template for your index, unless using an existing index.  If inserting to an existing index, you would instead modify that index template rather than creating a new one.
