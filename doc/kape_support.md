SOF-ELK® KAPE Support
=======

[KAPE (The Kroll Artifact Parser and Extractor)](https://learn.duffandphelps.com/kape) is an efficient and highly configurable triage program that will target essentially any device or storage location, find forensically useful artifacts, and parse them within a few minutes.  It's able to pull countless critical artifacts from a source system within minutes.  It consists of various modules that allow extraction and parsing of useful forensic artifacts.

SOF-ELK will parse a number of the growing set of reports that KAPE generates.  Since KAPE modules evolve quickly, this document indicates the tool version for each supported data set.  New data types are added often, so check back as the data SOF-ELK can parse is added to and updated.

**Supported KAPE Tools:**

- [LECmd](https://github.com/EricZimmerman/LECmd): Parses Microsoft Windows LNK shortcut files
  - Version supported: v1.3.2.0
  - Required filename: `*_LECmd_Output.json`
- [MFTECmd](https://github.com/EricZimmerman/MFTECmd): Parses $MFT from NTFS file systems
  - Version supported: v0.4.4.2
  - Required filename: `*_MFTECmd*_Output.json`
- [EvtxECmd](https://github.com/EricZimmerman/EvtxECmd): Parses Microsoft Windows Event Log files
  - Version supported: v0.4.5.2
  - Required filename: `*_EvtxECmd_Output.json`

**Credits:**

First and foremost, many thanks to Eric Zimmerman for creating KAPE and for all the hard work he puts in making and keeping the toolset awesome.