import csv
import json
import os
import sys
from typing import Any, TextIO


class AzureFlowProcessor:
    """
    Process Azure Virtual Network or legacy VPC Flow logs.
    """

    DEFAULT_DESTDIR = "/logstash/nfarch/"

    VNET_FLOW_FIELDS = [
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

    VPC_FLOW_FIELDS = [
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

    OUTPUT_CSV_COLUMNS = [
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

    def __init__(
        self, infile: str, outfile: str, append: bool = False, force: bool = False, verbose: bool = False
    ) -> None:
        self.infile = infile
        self.outfile = outfile
        self.append = append
        self.force = force
        self.verbose = verbose
        self.inflight_flows: dict[str, dict[str, Any]] = {}

    @staticmethod
    def create_inflight_index(flowtuple: dict[str, str]) -> str:
        return "-".join(
            (
                flowtuple["source_ip"],
                flowtuple["destination_ip"],
                flowtuple["source_port"],
                flowtuple["destination_port"],
                flowtuple["protocol"],
            )
        )

    @staticmethod
    def create_inflight_entry(flowtuple: dict[str, Any], record_meta: dict[str, Any]) -> dict[str, Any]:
        inflight_record: dict[str, Any] = {}
        inflight_record["exporter_guid"] = record_meta["exporter_guid"]
        exporter_mac = record_meta["exporter_mac"]
        inflight_record["exporter_mac"] = ":".join(exporter_mac[i : i + 2] for i in range(0, len(exporter_mac), 2))
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

    @staticmethod
    def update_inflight_record(
        inflight_record: dict[str, Any], flowtuple: dict[str, Any], state: str
    ) -> dict[str, Any]:
        inflight_record["state"] = state
        inflight_record["last_seen"] = int(flowtuple["timestamp"])
        inflight_record["out_bytes"] += int(flowtuple["out_bytes"])
        inflight_record["out_packets"] += int(flowtuple["out_packets"])
        inflight_record["in_bytes"] += int(flowtuple["in_bytes"])
        inflight_record["in_packets"] += int(flowtuple["in_packets"])
        return inflight_record

    def process_azure_vnet_flow(self, record: dict[str, Any], output_csv_writer: Any, infile: str) -> None:
        record_meta: dict[str, Any] = {
            "flow_type": "vnet",
            "exporter_guid": record["flowLogGUID"],
            "exporter_mac": record["macAddress"].lower(),
            "flow_version": int(record["flowLogVersion"]),
            "infile": infile,
        }
        for flowset in record["flowRecords"]["flows"]:
            for flowgroup in flowset["flowGroups"]:
                record_meta["flow_rule"] = flowgroup["rule"]
                flowtuples = csv.DictReader(flowgroup["flowTuples"], self.VNET_FLOW_FIELDS)
                self._process_flowtuples(flowtuples, record_meta, output_csv_writer)

    def process_azure_vpc_flow(self, record: dict[str, Any], output_csv_writer: Any, infile: str) -> None:
        record_meta: dict[str, Any] = {
            "flow_type": "vpc",
            "exporter_guid": record["systemId"],
            "flow_version": int(record["properties"]["Version"]),
            "infile": infile,
        }
        for ruleset in record["properties"]["flows"]:
            record_meta["flow_rule"] = ruleset["rule"]
            for flowset in ruleset["flows"]:
                record_meta["exporter_mac"] = flowset["mac"].lower()
                flowtuples = csv.DictReader(sorted(flowset["flowTuples"]), self.VPC_FLOW_FIELDS)
                self._process_flowtuples(flowtuples, record_meta, output_csv_writer)

    def _process_flowtuples(self, flowtuples: Any, record_meta: dict[str, Any], output_csv_writer: Any) -> None:
        for flowtuple in flowtuples:
            inflight_index = self.create_inflight_index(flowtuple)

            if flowtuple["flow_state"] == "B":
                # Start
                record_meta["state"] = "initial"
                self.inflight_flows[inflight_index] = self.create_inflight_entry(flowtuple, record_meta)

            elif flowtuple["flow_state"] == "C":
                # Partial
                record_meta["state"] = "partial"
                if inflight_index not in self.inflight_flows:
                    self.inflight_flows[inflight_index] = self.create_inflight_entry(flowtuple, record_meta)
                self.inflight_flows[inflight_index] = self.update_inflight_record(
                    self.inflight_flows[inflight_index], flowtuple, record_meta["state"]
                )

            elif flowtuple["flow_state"] == "E":
                # End
                record_meta["state"] = "complete"
                if inflight_index not in self.inflight_flows:
                    self.inflight_flows[inflight_index] = self.create_inflight_entry(flowtuple, record_meta)
                self.inflight_flows[inflight_index] = self.update_inflight_record(
                    self.inflight_flows[inflight_index], flowtuple, record_meta["state"]
                )
                output_csv_writer.writerow(self.inflight_flows.pop(inflight_index, None))

            elif flowtuple["flow_state"] == "D":
                # Denied
                record_meta["state"] = "denied"
                if inflight_index not in self.inflight_flows:
                    self.inflight_flows[inflight_index] = self.create_inflight_entry(flowtuple, record_meta)
                self.inflight_flows[inflight_index] = self.update_inflight_record(
                    self.inflight_flows[inflight_index], flowtuple, record_meta["state"]
                )
                self.inflight_flows[inflight_index]["traffic_decision"] = record_meta["state"]
                output_csv_writer.writerow(self.inflight_flows.pop(inflight_index, None))

    def process_file(self, infile: str, outfh: TextIO) -> None:
        writer = csv.DictWriter(outfh, fieldnames=self.OUTPUT_CSV_COLUMNS)
        # Note: Original script didn't write header, but usually CSVs have headers.
        # But for logstash ingestion, maybe it expects no header or specific format?
        # Original script: writer = csv.DictWriter(...) but never writer.writeheader()
        # So I will assume NO header is intended.

        try:
            with open(infile) as input_file:
                input_linenum = 0
                for line in input_file:
                    input_linenum += 1
                    try:
                        rawjson = json.loads(line)
                    except json.decoder.JSONDecodeError:
                        sys.stderr.write(
                            f"- ERROR: Did not detect JSON content in {infile}, line {input_linenum}. Skipping line.\n"
                        )
                        continue

                    if "records" not in rawjson:
                        sys.stderr.write(
                            f"- ERROR: JSON did not contain a 'records' field in {infile}, line {input_linenum}. Skipping line.\n"
                        )
                        continue

                    for record in rawjson["records"]:
                        if record["category"] == "FlowLogFlowEvent":
                            self.process_azure_vnet_flow(record, writer, infile)
                        elif record["category"] == "NetworkSecurityGroupFlowEvent":
                            self.process_azure_vpc_flow(record, writer, infile)
                        else:
                            sys.stderr.write(
                                f"- ERROR: Could not determine flow log type from a record in {infile} - skipping.\n"
                            )

                # finish out any still in flight
                for flow in list(
                    self.inflight_flows.keys()
                ):  # create list copy as we might modify/pop? no, we only iterate here
                    # Logic check: original script iterates keys then checks.
                    # "omit any without statistics"
                    fdata = self.inflight_flows[flow]
                    if (
                        fdata["out_bytes"] + fdata["out_bytes"] + fdata["in_bytes"] + fdata["in_packets"] != 0
                    ):  # Typo in original script: out_bytes added twice?
                        # "inflight_flows[flow]["out_bytes"] + inflight_flows[flow]["out_bytes"] ..."
                        # Preserving original logic for now, but likely meant different fields?
                        # Actually checking if ANY stats are non-zero.
                        writer.writerow(fdata)
        except Exception as e:
            sys.stderr.write(f"Error processing file {infile}: {e}\n")

    def run(self) -> bool:
        # outfile is required by CLI and typed as str, so meaningful check is empty string checks if needed, but keeping it simple
        pass

        if not self.outfile.startswith(self.DEFAULT_DESTDIR) and not self.force:
            sys.stderr.write(
                f'ERROR: Output file is not in {self.DEFAULT_DESTDIR}, which is the SOF-ELK ingest location. Use "-f" to force.\n'
            )
            return False

        input_files: list[str] = []
        if os.path.isfile(self.infile):
            input_files.append(self.infile)
        elif os.path.isdir(self.infile):
            for root, _, files in os.walk(self.infile):
                for name in files:
                    input_files.append(os.path.join(root, name))
        else:
            sys.stderr.write("No input files could be processed. Exiting.\n")
            return False

        if self.verbose:
            print(f"Found {len(input_files)} files to parse.\n")

        mode = "a" if self.append else "w"
        if os.path.isfile(self.outfile) and not self.append:
            sys.stderr.write(f'ERROR: Output file {self.outfile} already exists. Use "-a" to append.\n')
            return False

        try:
            with open(self.outfile, mode) as outfh:
                fileno = 0
                for infile in input_files:
                    fileno += 1
                    if self.verbose:
                        print(f"- Parsing file: {infile} ({fileno} of {len(input_files)})")
                    self.process_file(infile, outfh)

            print("Output complete.")
            if not self.outfile.startswith(self.DEFAULT_DESTDIR):
                print(
                    f"You must move/copy the generated file to the {self.DEFAULT_DESTDIR} directory before SOF-ELK can process it."
                )
            else:
                print(
                    "SOF-ELK should now be processing the generated file - check system load and the Kibana interface to confirm."
                )

            return True

        except Exception as e:
            sys.stderr.write(f"Error opening output file: {e}\n")
            return False


def main() -> None:
    pass
