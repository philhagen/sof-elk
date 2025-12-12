import argparse
import subprocess
import sys
import shutil
import os

class FirewallManager:
    """
    Manages system firewall configurations (firewall-cmd).
    """
    @staticmethod
    def modify_firewall(action: str, port: int, protocol: str) -> None:
        """
        Modifies the firewall rules to open or close a port.

        Args:
            action: The action to perform ("open" or "close").
            port: The port number to modify.
            protocol: The protocol ("tcp" or "udp").

        Raises:
            SystemExit: If the script is not run as root, firewall-cmd is missing, or the action is invalid.
        """
        if not shutil.which("firewall-cmd"):
            print("Error: firewall-cmd not found.")
            sys.exit(1)
            
        if os.geteuid() != 0:
            print("This script must be run as root. Exiting.")
            sys.exit(1)

        if action == "open":
            fw_arg = "--add-port"
        elif action == "close":
            fw_arg = "--remove-port"
        else:
             print(f"Invalid action: {action}")
             sys.exit(1)
             
        cmd = ["firewall-cmd", "--zone=public", f"{fw_arg}={port}/{protocol}", "--permanent"]
        
        try:
            subprocess.check_call(cmd, stdout=subprocess.DEVNULL)
            subprocess.check_call(["firewall-cmd", "--reload"], stdout=subprocess.DEVNULL)
        except subprocess.CalledProcessError as e:
            print(f"Error modifying firewall: {e}")
            sys.exit(1)

def run_firewall(args: argparse.Namespace) -> None:
    FirewallManager.modify_firewall(args.action, args.port, args.protocol)

def register_subcommand(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser("firewall", help="Modify system firewall")
    parser.add_argument("-a", "--action", dest="action", choices=["open", "close"], required=True, help="Action to take")
    parser.add_argument("-p", "--port", dest="port", required=True, type=int, help="Port number")
    parser.add_argument("-r", "--protocol", dest="protocol", choices=["tcp", "udp"], required=True, help="Protocol")
    parser.set_defaults(func=run_firewall)
