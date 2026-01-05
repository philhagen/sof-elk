# Volatility to SOF-ELK Parsers

Memory forensics parsers for ingesting Volatility3 output into SOF-ELK using the **Filebeat → Logstash → Elasticsearch** architecture.

## Overview

This toolkit provides Filebeat configuration, Logstash filters, and Python preprocessing scripts to parse and index Volatility3 memory forensics output into Elasticsearch via SOF-ELK.

### Supported Volatility3 Plugins (6 Total)

**Tier 1: Process Enumeration (3 plugins)**
- **windows.pslist** - Lists active processes by walking the process list
- **windows.pstree** - Shows process hierarchy in a tree structure
- **windows.psscan** - Scans physical memory for process structures (detects hidden processes)

**Tier 2: Network & Execution Analysis (3 plugins)**
- **windows.netscan** - Network connections (IPv4/IPv6) with GeoIP enrichment
- **windows.cmdline** - Command line arguments with attack pattern detection
- **windows.netstat** - Network statistics (netstat-style enumeration)
