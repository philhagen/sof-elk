import platform
import subprocess
import os
import sys
import argparse
from typing import Any

# Import GitManager to check for updates functionality
from sof_elk.management.git import GitManager

class LoginManager:
    """
    Manages the message of the day (MOTD) and login validation/checks.
    """
    @staticmethod
    def show_login_message() -> None:
        """
        Displays the SOF-ELK welcome message, system information, and helpful commands.
        Also performs a check for git updates.
        """
        # Get Distribution Info
        dist_desc = "Unknown Linux"
        try:
             # Try lsb_release like the script
             # DISTRIB_DESCRIPTION=$(lsb_release -s -d)
             res = subprocess.run(["lsb_release", "-s", "-d"], capture_output=True, text=True)
             if res.returncode == 0:
                 dist_desc = res.stdout.strip()
             else:
                 # Fallback to reading /etc/lsb-release or /etc/os-release
                 if os.path.exists("/etc/lsb-release"):
                     with open("/etc/lsb-release") as f:
                         for line in f:
                             if line.startswith("DISTRIB_DESCRIPTION="):
                                 dist_desc = line.split("=", 1)[1].strip().strip('"')
        except Exception:
             pass

        uname_o = platform.system() # Linux
        uname_r = platform.release()
        uname_m = platform.machine()
        # uname -o is actually "operating system" usually GNU/Linux
        # platform.system() gives Linux. platform.uname().system
        
        # script: printf "Built on %s (%s %s %s)\n" "$DISTRIB_DESCRIPTION" "$(uname -o)" "$(uname -r)" "$(uname -m)"
        # Note: uname -o might return "GNU/Linux"
        try:
             uname_o = subprocess.check_output(["uname", "-o"], text=True).strip()
        except:
             pass

        print()
        print("Welcome to the SOF-ELK® VM Distribution")
        print(f"Built on {dist_desc} ({uname_o} {uname_r} {uname_m})")
        print("--------------------------------------")
        print("Here are some useful commands:")
        print("  sof-elk_clear.py")
        print("    Forcibly removes all records from the Elasticsearch index.")
        print("    Use '-h' for usage.")
        print("  load_all_dashboards.sh")
        print("    Resets all Kibana dashboards to the versions on disk in the")
        print("    /usr/local/sof-elk/ directory.")
        print()

        # Run git check
        # /usr/local/sof-elk/supporting-scripts/git-check-pull-needed.sh
        # This wrapper calls python sof_elk.management.git.check_pull_needed
        # We can call it directly.
        try:
             GitManager.check_pull_needed()
        except Exception as e:
             # Don't fail login if this fails
             pass

def run_login(args: argparse.Namespace) -> None:
    LoginManager.show_login_message()

def register_subcommand(subparsers: Any) -> None:
    parser = subparsers.add_parser("login", help="Show login message")
    parser.set_defaults(func=run_login)
