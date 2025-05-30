#!/usr/bin/env python3
# SOF-ELK® Supporting script
# (C)2025 Lewes Technology Consulting, LLC
#
# This script reads a file or directory tree of JSON files containing Azure
#   Virtual Network or legacy VPC Flow logs and output in a format that
#   SOF-ELK® can read with its NetFlow ingest feature

# See https://learn.microsoft.com/en-us/azure/network-watcher/vnet-flow-logs-overview
#   for details on the newer Virtual Network Flow format
# See https://docs.microsoft.com/en-us/azure/network-watcher/network-watcher-nsg-flow-logging-overview
#   for details on the legacy VPC Flow format

import argparse
import sys
import os
import json
import csv

default_destdir = "/logstash/nfarch/"
vnet_flow_fields = [
    "timestamp",
    "source_ip",
    "destination_ip",
    "source_port",
    "destination_port",
    "protocol",
    "traffic_flow",
    "flow_state",
    "encryption_state",
    "out_packets",
    "out_bytes",
    "in_packets",
    "in_bytes",
]
vpc_flow_fields = [
    "timestamp",
    "source_ip",
    "destination_ip",
    "source_port",
    "destination_port",
    "protocol",
    "traffic_flow",
    "traffic_decision",
    "flow_state",
    "out_packets",
    "out_bytes",
    "in_packets",
    "in_bytes",
]
output_csv_columns = [
    "exporter_guid",
    "exporter_mac",
    "version",
    "flow_rule",
    "source",
    "state",
    "first_seen",
    "last_seen",
    "source_ip",
    "source_port",
    "destination_ip",
    "destination_port",
    "protocol",
    "out_bytes",
    "out_packets",
    "in_bytes",
    "in_packets",
    "direction",
    "traffic_decision",
    "encrypted",
    "non_encrypted_reason",
]


def create_inflight_index(flowtuple):
    index_string = "-".join(
        (
            flowtuple["source_ip"],
            flowtuple["destination_ip"],
            flowtuple["source_port"],
            flowtuple["destination_port"],
            flowtuple["protocol"],
        )
    )
    return index_string


def create_inflight_entry(flowtuple, record_meta):
    inflight_record = {}
    inflight_record["exporter_guid"] = record_meta["exporter_guid"]
    exporter_mac = record_meta["exporter_mac"]
    inflight_record["exporter_mac"] = ":".join(
        exporter_mac[i : i + 2] for i in range(0, len(exporter_mac), 2)
    )
    inflight_record["version"] = record_meta["flow_version"]
    inflight_record["flow_rule"] = record_meta["flow_rule"]
    inflight_record["source"] = record_meta["infile"]
    inflight_record["state"] = record_meta["state"]

    inflight_record["first_seen"] = int(flowtuple["timestamp"])
    inflight_record["last_seen"] = int(flowtuple["timestamp"])
    inflight_record["source_ip"] = flowtuple["source_ip"]
    inflight_record["source_port"] = int(flowtuple["source_port"])
    inflight_record["destination_ip"] = flowtuple["destination_ip"]
    inflight_record["destination_port"] = int(flowtuple["destination_port"])

    if record_meta["flow_type"] == "vnet":
        inflight_record["protocol"] = flowtuple["protocol"]
        inflight_record["traffic_decision"] = "allowed"

        if flowtuple["encryption_state"] == "X":
            inflight_record["encrypted"] = 1
        else:
            inflight_record["encrypted"] = 0
            if flowtuple["encryption_state"] != "NX":
                inflight_record["non_encrypted_reason"] = flowtuple["encryption_state"]

    elif record_meta["flow_type"] == "vpc":
        if flowtuple["protocol"] == "T":
            inflight_record["protocol"] = 6
        elif flowtuple["protocol"] == "U":
            inflight_record["protocol"] = 17

        if flowtuple["traffic_decision"] == "A":
            inflight_record["traffic_decision"] = "allowed"
        elif flowtuple["traffic_decision"] == "D":
            inflight_record["traffic_decision"] = "denied"

    if flowtuple["traffic_flow"] == "I":
        inflight_record["direction"] = "inbound"
    elif flowtuple["traffic_flow"] == "O":
        inflight_record["direction"] = "outbound"

    inflight_record["out_packets"] = 0
    inflight_record["out_bytes"] = 0
    inflight_record["in_packets"] = 0
    inflight_record["in_bytes"] = 0

    return inflight_record


def update_inflight_record(inflight_record, flowtuple, state):
    inflight_record["state"] = state

    inflight_record["last_seen"] = int(flowtuple["timestamp"])
    inflight_record["out_bytes"] += int(flowtuple["out_bytes"])
    inflight_record["out_packets"] += int(flowtuple["out_packets"])
    inflight_record["in_bytes"] += int(flowtuple["in_bytes"])
    inflight_record["in_packets"] += int(flowtuple["in_packets"])

    return inflight_record


def process_azure_flow(infile, outfh):
    input_file = open(infile, "r")

    inflight_flows = {}
    writer = csv.DictWriter(outfh, fieldnames=output_csv_columns)

    input_linenum = 0
    for line in input_file:
        input_linenum += 1

        try:
            rawjson = json.loads(line)
        except json.decoder.JSONDecodeError:
            sys.stderr.write(
                "- ERROR: Did not detect JSON content in %s, line %d. Skipping line.\n"
                % (infile, input_linenum)
            )
            return

        for record in rawjson["records"]:
            # this is a new vnet flow format
            if record["category"] == "FlowLogFlowEvent":
                process_azure_vnet_flow(record, writer, inflight_flows, infile)

            # this is a legacy VPC flow format
            elif record["category"] == "NetworkSecurityGroupFlowEvent":
                process_azure_vpc_flow(record, writer, inflight_flows, infile)

            else:
                sys.stderr.write(
                    "- ERROR: Could not determine flow log type from a record in %s - skipping.\n"
                    % (infile)
                )

        # finish out any still in flight, but omit any without statistics (e.g. started but not continued/ended)
        for flow in inflight_flows.keys():
            if (
                inflight_flows[flow]["out_bytes"]
                + inflight_flows[flow]["out_bytes"]
                + inflight_flows[flow]["in_bytes"]
                + inflight_flows[flow]["in_packets"]
                != 0
            ):
                writer.writerow(inflight_flows[flow])

    input_file.close()


def process_azure_vnet_flow(record, output_csv_writer, inflight_flows, infile):
    record_meta = {
        "flow_type": "vnet",
        "exporter_guid": record["flowLogGUID"],
        "exporter_mac": record["macAddress"].lower(),
        "flow_version": int(record["flowLogVersion"]),
        "infile": infile,
    }
    for flowset in record["flowRecords"]["flows"]:
        for flowgroup in flowset["flowGroups"]:
            record_meta["flow_rule"] = flowgroup["rule"]

            flowtuples = csv.DictReader(flowgroup["flowTuples"], vnet_flow_fields)

            for flowtuple in flowtuples:
                inflight_index = create_inflight_index(flowtuple)

                if flowtuple["flow_state"] == "B":
                    # we are at the start of the flow
                    # create the "in flight" tracker
                    record_meta["state"] = "initial"
                    inflight_flows[inflight_index] = create_inflight_entry(
                        flowtuple, record_meta
                    )

                elif flowtuple["flow_state"] == "C":
                    # continuation of flow record
                    record_meta["state"] = "partial"

                    # if there is no "in flight" tracker yet, we caught a random continue without a begin
                    # create an empty record to start from
                    if not inflight_index in inflight_flows:
                        inflight_flows[inflight_index] = create_inflight_entry(
                            flowtuple, record_meta
                        )

                    # update the "in flight" tracker
                    inflight_flows[inflight_index] = update_inflight_record(
                        inflight_flows[inflight_index], flowtuple, record_meta["state"]
                    )

                elif flowtuple["flow_state"] == "E":
                    # close out the flow
                    record_meta["state"] = "complete"

                    # if there is no "in flight" tracker yet, we caught a random end without a begin
                    # create an empty record to start from
                    if not inflight_index in inflight_flows:
                        inflight_flows[inflight_index] = create_inflight_entry(
                            flowtuple, record_meta
                        )

                    # update the "in flight" tracker
                    inflight_flows[inflight_index] = update_inflight_record(
                        inflight_flows[inflight_index], flowtuple, record_meta["state"]
                    )

                    # write to output file and remove the "in flight" tracker
                    output_csv_writer.writerow(inflight_flows.pop(inflight_index, None))

                elif flowtuple["flow_state"] == "D":
                    # denied flow
                    record_meta["state"] = "denied"

                    # if there is no "in flight" tracker yet, we caught a random deny without a begin
                    # create an empty record to start from
                    if not inflight_index in inflight_flows:
                        inflight_flows[inflight_index] = create_inflight_entry(
                            flowtuple, record_meta
                        )

                    # update the "in flight" tracker
                    inflight_flows[inflight_index] = update_inflight_record(
                        inflight_flows[inflight_index], flowtuple, record_meta["state"]
                    )

                    inflight_flows[inflight_index]["traffic_decision"] = record_meta[
                        "state"
                    ]

                    # write to output file and remove the "in flight" tracker
                    output_csv_writer.writerow(inflight_flows.pop(inflight_index, None))


def process_azure_vpc_flow(record, output_csv_writer, inflight_flows, infile):
    # set record-level metadata values
    record_meta = {
        "flow_type": "vpc",
        "exporter_guid": record["systemId"],
        "flow_version": int(record["properties"]["Version"]),
        "infile": infile,
    }

    for ruleset in record["properties"]["flows"]:
        record_meta["flow_rule"] = ruleset["rule"]

        for flowset in ruleset["flows"]:
            # process all flow records in flowset['flowTuples']
            record_meta["exporter_mac"] = flowset["mac"].lower()
            flowtuples = csv.DictReader(sorted(flowset["flowTuples"]), vpc_flow_fields)

            for flowtuple in flowtuples:
                inflight_index = create_inflight_index(flowtuple)

                if flowtuple["flow_state"] == "B":
                    # we are at the start of the flow
                    record_meta["state"] = "initial"
                    inflight_flows[inflight_index] = create_inflight_entry(
                        flowtuple, record_meta
                    )

                elif flowtuple["flow_state"] == "C":
                    # continuation of flow record
                    record_meta["state"] = "partial"

                    # if there is no "in flight" tracker yet, we caught a random continue without a begin
                    # create an empty record to start from
                    if not inflight_index in inflight_flows:
                        inflight_flows[inflight_index] = create_inflight_entry(
                            flowtuple, record_meta
                        )

                    # update the "in flight" tracker
                    inflight_flows[inflight_index] = update_inflight_record(
                        inflight_flows[inflight_index], flowtuple, record_meta["state"]
                    )

                elif flowtuple["flow_state"] == "E":
                    # close out the flow
                    record_meta["state"] = "complete"

                    # if there is no "in flight" tracker yet, we caught a random end without a begin
                    # create an empty record to start from
                    if not inflight_index in inflight_flows:
                        inflight_flows[inflight_index] = create_inflight_entry(
                            flowtuple, record_meta
                        )

                    # update the "in flight" tracker
                    inflight_flows[inflight_index] = update_inflight_record(
                        inflight_flows[inflight_index], flowtuple, record_meta["state"]
                    )

                    # write to output file and remove the "in flight" tracker
                    output_csv_writer.writerow(inflight_flows.pop(inflight_index, None))


parser = argparse.ArgumentParser(
    description="Process Azure Flow logs into a format that is consistent with other SOF-ELK(R) NetFlow entries and place them into an output file.  Both Virtual Network Flow Logs and legacy VPC Flow Logs are supported."
)
parser.add_argument(
    "-r",
    "--read",
    dest="infile",
    help="Azure Flow log file to read or a directory containing JSON-formatted Azure Flow log files.",
)
parser.add_argument(
    "-w",
    "--write",
    dest="outfile",
    help="File to create containing processed Azure Flow data.",
)
parser.add_argument(
    "-f",
    "--force",
    dest="force_outfile",
    help="Force creating an output file in a location other than the default SOF-ELK ingest location, %s"
    % (default_destdir),
    default=False,
    action="store_true",
)
parser.add_argument(
    "-a",
    "--append",
    dest="append",
    help="Append to the output file if it exists.",
    default=False,
    action="store_true",
)
parser.add_argument(
    "-v",
    "--verbose",
    dest="verbose",
    help="Display progress and related status information while parsing input files.",
    default=False,
    action="store_true",
)
args = parser.parse_args()

if args.infile == None:
    sys.stderr.write("ERROR: No input file or root directory specified.\n")
    sys.exit(2)

if args.outfile == None:
    sys.stderr.write("ERROR: No output file specified.\n")
    sys.exit(2)
elif not args.outfile.startswith(default_destdir) and not args.force_outfile:
    sys.stderr.write(
        'ERROR: Output file is not in %s, which is the SOF-ELK ingest location. Use "-f" to force creating a file in this location.\n'
        % (default_destdir)
    )
    sys.exit(2)

input_files = []
if os.path.isfile(args.infile):
    input_files.append(args.infile)
elif os.path.isdir(args.infile):
    for root, dirs, files in os.walk(args.infile):
        for name in files:
            input_files.append(os.path.join(root, name))
else:
    sys.stderr.write("No input files could be processed.  Exiting.\n")
    sys.exit(4)

if args.verbose:
    print("Found %d files to parse." % (len(input_files)))
    print()

if os.path.isfile(args.outfile) and args.append == True:
    outfh = open(args.outfile, "a")
if os.path.isfile(args.outfile) and args.append == False:
    sys.stderr.write(
        'ERROR: Output file %s already exists. Use "-a" to append to the file at this location or specify a different filename.\n'
        % (args.outfile)
    )
    sys.exit(3)
else:
    outfh = open(args.outfile, "w")

fileno = 0
for infile in input_files:
    fileno = fileno + 1
    if args.verbose:
        print("- Parsing file: %s (%d of %d)" % (infile, fileno, len(input_files)))

    process_azure_flow(infile, outfh)

print("Output complete.")
if not args.outfile.startswith(default_destdir):
    print(
        "You must move/copy the generated file to the /logstash/nfarch/ directory before SOF-ELK can process it."
    )
else:
    print(
        "SOF-ELK should now be processing the generated file - check system load and the Kibana interface to confirm."
    )
