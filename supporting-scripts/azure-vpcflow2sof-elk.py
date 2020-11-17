#!/usr/bin/env python3
# SOF-ELK® Supporting script
# (C)2020 Lewes Technology Consulting, LLC
#
# This script will read a file or directory tree of JSON VPC Flow logs and output in a format that SOF-ELK® can read with its NetFlow ingest feature

# See https://docs.microsoft.com/en-us/azure/network-watcher/network-watcher-nsg-flow-logging-overview for details on this format

import argparse
import sys
import os
import json
import csv
import hashlib

default_destdir = '/logstash/nfarch/'
flow_fields = ['timestamp', 'source_ip', 'destination_ip', 'source_port', 'destination_port', 'protocol', 'traffic_flow', 'traffic_decision', 'flow_state', 'out_packets', 'out_bytes', 'in_packets', 'in_bytes']

def process_azure_vpc_flow(infile, outfh):
    input_file = open(infile, 'r')
    try:
        rawjson = json.load(input_file)
    except json.decoder.JSONDecodeError:
        sys.stderr.write('- ERROR: Could not process JSON from %s. Skipping file.\n' % (infile))
        return

    input_file.close()

    inflight_flows = {}

    for record in rawjson['records']:
        # get record-level metadata values
        exporter_guid = record['systemId']
        flow_version = record['properties']['Version']

        for ruleset in record['properties']['flows']:
            flow_rule = ruleset['rule']

            for flowset in ruleset['flows']:
                #process all flow records in flowset['flowTuples']
                exporter_mac = flowset['mac'].lower()
                flowtuples = csv.DictReader(flowset['flowTuples'], flow_fields)

                for flowtuple in flowtuples:
                    index_string = '-'.join((flowtuple['source_ip'], flowtuple['destination_ip'], flowtuple['source_port'], flowtuple['destination_port'], flowtuple['protocol']))
                    inflight_index = hashlib.sha256(index_string.encode('utf-8')).hexdigest()

                    if flowtuple['flow_state'] == 'B':
                        # we are at the start of the flow
                        # create the "in flight" tracker
                        inflight_flows[inflight_index] = {}
                        inflight_flows[inflight_index]['exporter_guid'] = exporter_guid
                        inflight_flows[inflight_index]['exporter_mac'] = ':'.join(exporter_mac[i:i+2] for i in range(0, len(exporter_mac), 2))
                        inflight_flows[inflight_index]['version'] = int(flow_version)
                        inflight_flows[inflight_index]['flow_rule'] = flow_rule
                        inflight_flows[inflight_index]['source'] = infile

                        inflight_flows[inflight_index]['first_seen'] = int(flowtuple['timestamp'])
                        inflight_flows[inflight_index]['source_ip'] = flowtuple['source_ip']
                        inflight_flows[inflight_index]['source_port'] = int(flowtuple['source_port'])
                        inflight_flows[inflight_index]['destination_ip'] = flowtuple['destination_ip']
                        inflight_flows[inflight_index]['destination_port'] = int(flowtuple['destination_port'])
                        if flowtuple['protocol'] == 'T':
                            inflight_flows[inflight_index]['protocol'] = 6
                        elif flowtuple['protocol'] == 'U':
                            inflight_flows[inflight_index]['protocol'] = 17

                        inflight_flows[inflight_index]['out_bytes'] = 0
                        inflight_flows[inflight_index]['out_packets'] = 0
                        inflight_flows[inflight_index]['in_bytes'] = 0
                        inflight_flows[inflight_index]['in_packets'] = 0

                    elif flowtuple['flow_state'] == 'C':
                        # continuation of flow record
                        # if there is no "in flight" tracker yet, we caught a random continue without a begin
                        if not inflight_index in inflight_flows:
                            sys.stderr.write('  - Found continue event without begin - skipping.\n')
                            continue

                        # update the "in flight" tracker
                        inflight_flows[inflight_index]['out_bytes'] += int(flowtuple['out_bytes'])
                        inflight_flows[inflight_index]['out_packets'] += int(flowtuple['out_packets'])
                        inflight_flows[inflight_index]['in_bytes'] += int(flowtuple['in_bytes'])
                        inflight_flows[inflight_index]['in_packets'] += int(flowtuple['in_packets'])
                    
                    elif flowtuple['flow_state'] == 'E':
                        # close out the flow
                        # if there is no "in flight" tracker yet, we caught a random end without a begin
                        if not inflight_index in inflight_flows:
                            sys.stderr.write('  - Found end event without begin - skipping\n')
                            continue

                        # update the "in flight" tracker
                        inflight_flows[inflight_index]['last_seen'] = int(flowtuple['timestamp'])
                        inflight_flows[inflight_index]['out_bytes'] += int(flowtuple['out_bytes'])
                        inflight_flows[inflight_index]['out_packets'] += int(flowtuple['out_packets'])
                        inflight_flows[inflight_index]['in_bytes'] += int(flowtuple['in_bytes'])
                        inflight_flows[inflight_index]['in_packets'] += int(flowtuple['in_packets'])

                        # write to output file and remove the "in flight" tracker
                        #flow_json = json.dumps(inflight_flows.pop(inflight_index, None))
                        #outfh.write(flow_json+'\n')
                        csv_columns = ['exporter_guid', 'exporter_mac', 'version', 'flow_rule', 'source', 'first_seen', 'source_ip', 'source_port', 'destination_ip', 'destination_port', 'protocol', 'out_bytes', 'out_packets', 'in_bytes', 'in_packets', 'last_seen']
                        writer = csv.DictWriter(outfh, fieldnames=csv_columns)
                        writer.writerow(inflight_flows.pop(inflight_index, None))

parser = argparse.ArgumentParser(description='Process Azure VPC Flow logs into a format that is consistent with other SOF-ELK(R) NetFlow entries and place them into an output file.')
parser.add_argument('-r', '--read', dest='infile', help='Azure VPC Flow log file to read, or a directory containing Azure VPC Flow log files.')
parser.add_argument('-w', '--write', dest='outfile', help='File to create containing processed Azure VPC Flow data.')
parser.add_argument('-f', '--force', dest='force_outfile', help='Force creating an output file in a location other than the default SOF-ELK ingest location, %s' % (default_destdir), default=False, action='store_true')
parser.add_argument('-a', '--append', dest='append', help='Append to the output file if it exists.', default=False, action='store_true')
parser.add_argument('-v', '--verbose', dest='verbose', help='Display progress and related status information while parsing input files.', default=False, action='store_true')
args = parser.parse_args()

if args.infile == None:
    sys.stderr.write('ERROR: No input file or root directory specified.\n')
    sys.exit(2)

if args.outfile == None:
    sys.stderr.write('ERROR: No output file specified.\n')
    sys.exit(2)
elif not args.outfile.startswith(default_destdir) and not args.force_outfile:
    sys.stderr.write('ERROR: Output file is not in %s, which is the SOF-ELK ingest location. Use "-f" to force creating a file in this location.\n' % (default_destdir))
    sys.exit(2)

input_files= []
if os.path.isfile(args.infile):
    input_files.append(args.infile)
elif os.path.isdir(args.infile):
    for root, dirs, files in os.walk(args.infile):
        for name in files:
            input_files.append(os.path.join(root, name))
else:
    sys.stderr.write('No input files could be processed.  Exiting.\n')
    sys.exit(4)

if args.verbose:
    print('Found %d files to parse.' % (len(input_files)))
    print()

if os.path.isfile(args.outfile) and args.append == True:
    outfh = open(args.outfile, 'a')
if os.path.isfile(args.outfile) and args.append == False:
    sys.stderr.write('ERROR: Output file %s already exists. Use "-a" to append to the file at this location or specify a different filename.\n' % (args.outfile))
    sys.exit(3)
else:
    outfh = open(args.outfile, 'w')

for infile in input_files:
    if args.verbose:
        print('- Parsing file: %s' % (infile))
    process_azure_vpc_flow(infile, outfh)

print('Output complete.')
if not args.outfile.startswith(default_destdir):
    print('You must move/copy the generated file to teh /logstash/nfarch/ directory before SOF-ELK can process it.')
else:
    print('SOF-ELK should now be processing the generated file - check system load and the Kibana interface to confirm.')