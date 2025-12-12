import os
import subprocess
import re
import argparse
from sof_elk.api.client import SOFElkSession

class VMManager:
    VM_UPDATE_STATUS_FILE = "/var/run/sof-elk_vm_update"
    VERSION_CHECK_URL = "https://for572.com/sof-elk-versioncheck"
    
    @staticmethod
    def check_update() -> None:
        """
        Check for a new SOF-ELK VM version by querying the remote version check URL.
        
        If a new version is found, creates a flag file (`VM_UPDATE_STATUS_FILE`) 
        to notify other system components (like motd).
        """
        if os.path.exists(VMManager.VM_UPDATE_STATUS_FILE):
             return

        # Get current branch
        try:
             # git branch | grep ^* | awk {print $2}
             # or git rev-parse --abbrev-ref HEAD
             # Assume cwd is /usr/local/sof-elk/ or we run command there
             cwd = "/usr/local/sof-elk/"
             if not os.path.isdir(cwd):
                 cwd = os.getcwd()
             
             branch = subprocess.check_output(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=cwd, text=True).strip()
        except subprocess.CalledProcessError:
             return

        # Check regex
        match = re.match(r"^public/v([0-9]{8})$", branch)
        if not match:
             # Not a public/community branch
             return
        
        current_release_s = match.group(1)
        
        # Check remote
        try:
             # Use SOFElkSession for consistent timeout and headers
             # Note: SOFElkSession.get_session() returns the client wrapper
             client = SOFElkSession.get_session()
             
             # Current release as referer
             headers = {"Referer": current_release_s}
             
             # The logic relies on getting the final URL after redirects.
             # requests follows redirects by default.
             response = client.head(VMManager.VERSION_CHECK_URL, headers=headers, allow_redirects=True)
             
             final_url = response.url
             
             # Format check on final_url
             # Looking for vYYYYMMDD
             remote_match = re.search(r"v([0-9]{8})", final_url)
             if remote_match:
                  latest_release_s = remote_match.group(1)
                  
                  if current_release_s < latest_release_s:
                      # Update available
                      try:
                          with open(VMManager.VM_UPDATE_STATUS_FILE, 'w'):
                              pass
                      except OSError:
                          pass
        except Exception:
             pass

def run_vm_check(args: argparse.Namespace) -> None:
    VMManager.check_update()
