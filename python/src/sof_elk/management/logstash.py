import subprocess
import os
import sys
import shutil
import argparse
from typing import Any

class LogstashManager:
    LOGSTASH_PLUGIN_BIN = "/usr/share/logstash/bin/logstash-plugin"
    PLUGINS = [
        "logstash-filter-translate",
        "logstash-filter-geoip",
        "logstash-filter-cidr",
        "logstash-filter-dns",
        "logstash-filter-prune",
        "logstash-filter-tld",
        "logstash-filter-json",
        "logstash-filter-grok",
        "logstash-filter-kv",
        "logstash-filter-date",
        "logstash-filter-mutate",
        "logstash-filter-ruby",
        "logstash-codec-netflow",
        "logstash-codec-sflow",
        "logstash-codec-json_lines",
        "logstash-codec-rubydebug",
        "logstash-input-udp",
        "logstash-input-tcp",
        "logstash-input-beats",
        "logstash-input-syslog",
        "logstash-output-elasticsearch"
    ]

    @staticmethod
    def update_plugins() -> None:
        """
        Check for and install/update required Logstash plugins.
        
        Iterates through the defined `PLUGINS` list and uses `logstash-plugin install`
        to ensure they are present and up to date.
        
        Requires root privileges.
        """
        if os.geteuid() != 0:
            print("This script must be run as root. Exiting.")
            sys.exit(1)

        plugin_bin = LogstashManager.LOGSTASH_PLUGIN_BIN
        # Fallback search if not at default location?
        if not os.path.exists(plugin_bin):
            found = shutil.which("logstash-plugin")
            if found:
                plugin_bin = found
            else:
                print(f"Error: {plugin_bin} not found and logstash-plugin not in PATH.")
                sys.exit(1)

        print("Updating/Installing Logstash plugins...")
        for plugin in LogstashManager.PLUGINS:
            print(f"Processing {plugin}...")
            try:
                subprocess.check_call([plugin_bin, "install", plugin], stdout=subprocess.DEVNULL)
            except subprocess.CalledProcessError as e:
                print(f"Error installing/updating {plugin}: {e}")
                # Don't exit, continue to next
            except Exception as e:
                print(f"Error: {e}")

def run_plugin_update(args: argparse.Namespace) -> None:
    LogstashManager.update_plugins()

def register_subcommand(subparsers: Any) -> None:
    pass
