import os
import subprocess
import hashlib
import sys
import logging

class GeoIPUpdater:
    def __init__(self, config_file="/etc/GeoIP.conf", db_dir_default="/usr/local/share/GeoIP/"):
        self.config_file = config_file
        self.db_dir = db_dir_default
        self.databases = []
        self.logger = logging.getLogger(__name__)

    def _parse_config(self):
        """Parse GeoIP.conf to find DatabaseDirectory and EditionIDs."""
        if not os.path.exists(self.config_file):
            self.logger.error(f"The GeoIP configuration file {self.config_file} has not been created.")
            print(f"The GeoIP configuration file {self.config_file} has not been created - exiting.")
            print("\nNo updates can be downloaded without this file.")
            print("Run 'geoip_bootstrap.sh' as root to configure this system for automatic updates.")
            print("\nYou will need an Account ID and License Key from a free MaxMind account to enable them.")
            return False

        try:
            with open(self.config_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("DatabaseDirectory"):
                        parts = line.split(maxsplit=1)
                        if len(parts) > 1:
                            self.db_dir = parts[1]
                    elif line.startswith("EditionIDs"):
                        parts = line.split(maxsplit=1)
                        if len(parts) > 1:
                            # EditionIDs can be space or comma separated usually, script assumed space
                            self.databases = parts[1].split()
        except Exception as e:
            self.logger.error(f"Error reading config file: {e}")
            return False
        
        return True

    def _get_md5(self, filepath):
        """Calculate MD5 checksum of a file."""
        if not os.path.exists(filepath):
            return ""
        try:
            with open(filepath, "rb") as f:
                file_hash = hashlib.md5()
                while chunk := f.read(8192):
                    file_hash.update(chunk)
            return file_hash.hexdigest()
        except Exception as e:
            self.logger.warning(f"Could not calculate MD5 for {filepath}: {e}")
            return ""

    def update(self):
        """Run the update process."""
        if not self._parse_config():
            return False

        if not self.databases:
            self.logger.info("No databases configured.")
            return True

        # Calculate initial hashes
        initial_hashes = {}
        for db in self.databases:
            db_path = os.path.join(self.db_dir, f"{db}.mmdb")
            initial_hashes[db] = self._get_md5(db_path)

        # Run geoipupdate
        try:
            subprocess.run(["geoipupdate", "-f", self.config_file], check=True)
        except FileNotFoundError:
            self.logger.error("geoipupdate command not found.")
            print("Error: geoipupdate command not found.")
            return False
        except subprocess.CalledProcessError as e:
            self.logger.error(f"geoipupdate failed: {e}")
            print(f"Error: geoipupdate failed.")
            return False

        # Calculate new hashes and check for changes
        updates_found = False
        for db in self.databases:
            db_path = os.path.join(self.db_dir, f"{db}.mmdb")
            new_hash = self._get_md5(db_path)
            if new_hash != initial_hashes.get(db):
                updates_found = True
                self.logger.info(f"Database {db} updated.")

        # Restart Logstash if updates found
        if updates_found:
            print("Updates found. Restarting Logstash...")
            try:
                subprocess.run(["systemctl", "restart", "logstash.service"], check=True)
                print("Logstash restarted successfully.")
            except FileNotFoundError:
                 # Likely not on a system with systemctl (e.g. dev environment)
                 self.logger.warning("systemctl not found, cannot restart logstash.")
                 print("Warning: systemctl not found, cannot restart logstash.")
            except subprocess.CalledProcessError as e:
                self.logger.error(f"Failed to restart logstash: {e}")
                print("Error: Failed to restart logstash.")
                return False
        else:
            print("No updates found.")

        return True

def main():
    logging.basicConfig(level=logging.INFO)
    updater = GeoIPUpdater()
    updater.update()

if __name__ == "__main__":
    main()
