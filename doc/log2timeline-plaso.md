SOF-ELK® log2timeline/Plaso Support
=======

[log2timeline](https://github.com/log2timeline) is a framework for extensive and flexible timeline creation.  The [Plaso](https://github.com/log2timeline/plaso) tool, part of the framework, creates what are known as "supertimelines", containing aggregated and normalized forensic artifacts, based primarily on observed time stamps.  This gives a forensicator the ability to review a wide range of artifacts in a standardized fashion.

SOF-ELK will parse the CSV format of the Plaso tool's output.  The commands below serve as a general guideline on creating a compatible output file that SOF-ELK can handle.  These commands are not a substitute for log2timeline and/or Plaso documentation.

**Generating a compatible Plaso Output File**

- Generate the Plaso dumpfile
  - `log2timeline.py -z UTC --parsers "win7,-filestat" /cases/capstone/base-rd01-triage-plaso.dump /mnt/windows_mount/base-rd01/`
- Use `psort.py` to generate CSV
  - `psort.py -z "UTC" -o L2tcsv base-rd01-triage-plaso.dump "date > '2018-08-23 00:00:00' AND date < '2018-09-07 00:00:00'" -w base-rd01-triage-plaso.csv`

**Credits:**

Mark Hallman and Mike Pilkington did a lot of the groundwork on a standalone ELK VM used in FOR508. Without their work and help integrating the configuration to SOF-ELK, this would have been a much more difficult task.