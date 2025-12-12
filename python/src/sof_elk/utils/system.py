import subprocess
import sys
import os
import re
import argparse
from typing import Any

class SystemManager:
    """
    Manages system-level configurations, such as keyboard layout.
    """
    KEYBOARD_DEFAULT_FILE = "/etc/default/keyboard"

    @staticmethod
    def change_keyboard(layout_code: str) -> None:
        """
        Changes the system keyboard layout for the current session and persistently.

        Args:
            layout_code: The country code for the keyboard layout (e.g., "us", "uk", "it").

        Raises:
            SystemExit: If run without root privileges, if `loadkeys` is missing, or if the layout code is invalid.
        """
        if not layout_code:
            print("ERROR: No language provided.")
            sys.exit(2)
        
        layout_code = layout_code.lower()
        
        if os.geteuid() != 0:
            print("This script must be run as root. Exiting.")
            sys.exit(1)

        # 1. Change current session
        print(f"Changing keymap for this session to {layout_code}")
        try:
            # loadkeys output to stdout/stderr or /dev/null?
            # Script: loadkeys ${MAPNAME} > /dev/null
            subprocess.check_call(["loadkeys", layout_code], stdout=subprocess.DEVNULL)
        except subprocess.CalledProcessError:
             print(f"Error loading keymap {layout_code}")
             # Script says "The script will error out if an incorrect code is provided"
             # loadkeys fails on bad code.
             sys.exit(3)
        except FileNotFoundError:
             print("Error: loadkeys command not found.")
             sys.exit(1)

        # 2. Change persistent
        # sed -i 's/^XKBLAYOUT=.*/XKBLAYOUT=\"'${MAPNAME}'\"/g' /etc/default/keyboard
        if os.path.exists(SystemManager.KEYBOARD_DEFAULT_FILE):
             try:
                 # Read file
                 with open(SystemManager.KEYBOARD_DEFAULT_FILE, 'r') as f:
                     lines = f.readlines()
                 
                 new_lines = []
                 replaced = False
                 for line in lines:
                     if line.startswith("XKBLAYOUT="):
                         new_lines.append(f'XKBLAYOUT="{layout_code}"\n')
                         replaced = True
                     else:
                         new_lines.append(line)
                 
                 if not replaced:
                     # Append if not found? Script logic relies on replacement regex.
                     # If not present, maybe append? 
                     # The script assumes it's there. Let's append if missing just to be safe/robust.
                     new_lines.append(f'XKBLAYOUT="{layout_code}"\n')
                 
                 with open(SystemManager.KEYBOARD_DEFAULT_FILE, 'w') as f:
                     f.writelines(new_lines)
                     
                 print(f"Changed keymap persistently to {layout_code}")
             except Exception as e:
                 print(f"Error updating {SystemManager.KEYBOARD_DEFAULT_FILE}: {e}")
        else:
             print(f"Warning: {SystemManager.KEYBOARD_DEFAULT_FILE} not found. Persistent change not applied.")

def run_change_keyboard(args: argparse.Namespace) -> None:
    SystemManager.change_keyboard(args.layout)

def register_subcommand(subparsers: Any) -> None:
    parser = subparsers.add_parser("system", help="System configuration utilities")
    sys_subs = parser.add_subparsers(dest="system_command", required=True)
    
    kb_parser = sys_subs.add_parser("keyboard", help="Change keyboard layout")
    kb_parser.add_argument("layout", help="Country code (e.g. us, it, de)")
    kb_parser.set_defaults(func=run_change_keyboard)
