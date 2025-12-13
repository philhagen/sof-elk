import argparse
import os
import shutil
import subprocess
import sys
from typing import Any


class NfdumpManager:
    """
    Manages the processing of Netflow data using `nfdump`.
    """

    NFDUMP_FMT = "%das %dmk %eng %ts %fl 0 %byt %pkt %in %da %nh %sa %dp %sp %te %out %pr 0 0 %sas %smk %stos %flg 0"

    @staticmethod
    def process_nfdump(source: str, destination: str, exporter_ip: str | None = None) -> None:
        """
        Runs `nfdump` to process netflow data and output it to a file.

        Args:
            source: The source file or directory containing netflow data.
            destination: The output file path.
            exporter_ip: The exporter IP address (default: "0.0.0.0").

        Raises:
            SystemExit: If nfdump is missing, files are invalid, or processing fails.
        """
        if not shutil.which("nfdump"):
            print("Error: nfdump not found.")
            sys.exit(1)

        if not os.path.exists(source):
            print(f"Error: Source location {source} does not exist.")
            sys.exit(1)

        is_dir = os.path.isdir(source)
        read_flag = "-R" if is_dir else "-r"

        # Validate source
        try:
            subprocess.check_call(
                ["nfdump", read_flag, source, "-q", "-c", "1"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            )
        except subprocess.CalledProcessError:
            print("Error: Source data problem.")
            sys.exit(1)

        if not exporter_ip:
            print("Warning: Using default exporter IP 0.0.0.0")
            exporter_ip = "0.0.0.0"

        # Validate exporter IP (basic check, could use regex or ipaddress lib)
        # For simple port, relying on nfdump to complain or just passing string

        dest_dir = os.path.dirname(os.path.abspath(destination))
        if not os.path.exists(dest_dir):
            print(f"Error: Destination directory {dest_dir} does not exist.")
            sys.exit(1)

        if not destination.startswith("/logstash/nfarch/"):
            print("WARNING: Output file location is not in /logstash/nfarch/.")

        print(f"Running distillation. Outputting to {destination}")

        # Command construction
        # nfdump "${READFLAG}" "${SOURCE_LOCATION}" -6 -q -N -o "fmt:${EXPORTER_IP} ${NFDUMP2SOFELK_FMT}" > "${DESTINATION_FILE}"

        fmt_string = f"fmt:{exporter_ip} {NfdumpManager.NFDUMP_FMT}"
        cmd = ["nfdump", read_flag, source, "-6", "-q", "-N", "-o", fmt_string]

        try:
            with open(destination, "w") as outfile:
                subprocess.check_call(cmd, stdout=outfile)
            print("Output complete.")
        except subprocess.CalledProcessError as e:
            print(f"Error running nfdump: {e}")
            sys.exit(1)
        except Exception as e:
            print(f"Error: {e}")
            sys.exit(1)


def run_nfdump(args: argparse.Namespace) -> None:
    NfdumpManager.process_nfdump(args.source, args.destination, args.exporter_ip)


def register_subcommand(subparsers: Any) -> None:
    parser = subparsers.add_parser("nfdump", help="Process netflow data")
    parser.add_argument("-r", "--read", "--source", dest="source", required=True, help="Source file or directory")
    parser.add_argument("-w", "--write", "--destination", dest="destination", required=True, help="Destination file")
    parser.add_argument("-e", "--exporter", dest="exporter_ip", help="Exporter IP address")
    parser.set_defaults(func=run_nfdump)
