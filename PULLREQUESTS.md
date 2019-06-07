Submitting Pull Requests
========================

The code in this repository is used in a number of different environments, so these pull request guidelines are designed to allow the various moving parts to
 continue working.  Please take a moment to read them before submitting a pull request - in fact, before doing any customization.

 *PLEASE NOTE*: These guidelines are currently under heavy revision and will be changed in the near future.  We still would greatly appreciate your help, but please contact a developer (@PhilHagen) for help before proceeding if you plan to submit a PR.  We just want to prevent you from undergoing our own headaches down the road.

1. All development must be done from the "develop" branch.  PRs against master will not be accepted.
1. Do not modify the included stock dashboards, except for bug-level edits.  New dashboards will be considered, but as the codebase is designed to address a broad community, highly customized dashboards may not be accepted into master.
1. Any custom parsers must be created in the /configfiles-UNSUPPORTED/ subdirectory.  Any that are suitable for universal deployment will be moved to the /configfiles/ subdirectory by the SOF-ELK® team.
1. All IP addresses pulled via grok must be in a field with a name formatted as such: <directionality>_ip or <use_case>_ip
  * Examples: `source_ip`, `destination_ip`, `relay_ip`, `answer_ip`
1. All IP addresses must be enriched with the GeoIP location and ASN filters (see existing files for examples)
1. All IP addresses must be added to the "ips" array field (see existing files for examples)
