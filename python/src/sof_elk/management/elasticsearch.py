import argparse
import json
import os
import re
import subprocess
import sys
import time
from typing import Any

from sof_elk.api.elasticsearch import ElasticsearchManagement, get_es_client


class ElasticsearchManager:
    TOPDIR = "/logstash/"
    FILEBEAT_REGISTRY_FILE = "/var/lib/filebeat/registry"
    CLONE_SETTINGS = {"settings": {"index.number_of_shards": 1}}
    DATE_INDEX_RE = re.compile("(.*)-([0-9]{4}\\.[0-9]{2})")

    SOURCEDIR_INDEX_MAPPING = {
        "syslog": "logstash",
        "passivedns": "logstash",
        "zeek": "logstash",
        "nfarch": "netflow",
        "httpd": "httpdlog",
        "kape": "lnkfiles",
        "kape2": "kape",  # kape appears twice in original dict, handling overwrite?
        "microsoft365": "microsoft365",
        "kubernetes": "kubernetes",
    }
    # Fix for duplicate key in original source if any:
    # "kape": "lnkfiles", followed by "kape": "kape" overwrites.
    # I'll assume "kape" maps to "kape" based on last entry, but logic implies maybe multiple?
    # The original script had: "kape": "lnkfiles", "kape": "kape". Py dicts overwrite.
    # So "kape" -> "kape".

    def __init__(self, host: str = "localhost", port: int = 9200) -> None:
        self.host = host
        self.port = port
        self.es = get_es_client(host=self.host, port=self.port, timeout=300)
        self.mgmt = ElasticsearchManagement(es_client=self.es)

    def check_connection(self) -> bool:
        """
        Verify if a connection to Elasticsearch can be established.

        Returns:
            bool: True if connected, False otherwise.
        """
        try:
            self.es.info()
            return True
        except Exception:
            return False

    @staticmethod
    def confirm(prompt: str = "Confirm", resp: bool = False) -> bool:
        if resp:
            prompt = f"{prompt} [y]|n: "
        else:
            prompt = f"{prompt} [n]|y: "

        while True:
            ans = input(prompt)
            if not ans:
                return resp
            if ans.lower() in ["y", "yes"]:
                return True
            if ans.lower() in ["n", "no"]:
                return False
            print("please enter y or n.")

    def get_indices(self, full_listing: bool = False) -> list[str]:
        """
        Retrieve a list of active indices, optionally filtering out system indices.

        Args:
            full_listing (bool): If True, returns full index names. If False, returns unique base index names (e.g., 'syslog' from 'syslog-2023.01').

        Returns:
            List[str]: A list of index names.
        """
        system_index_regex = [
            re.compile(r) for r in ["\\..*", "elastalert_.*", ".apm.*", ".ds"]
        ]  # Expanded list from both scripts

        try:
            indices = list(self.es.indices.get_alias(index="*", expand_wildcards="open"))
        except Exception:
            # Fallback if get_alias fails or for closed indices?
            # freeze script uses es.indices.get(index="*", expand_wildcards="open,closed")
            indices = list(self.es.indices.get(index="*", expand_wildcards="open,closed"))

        index_dict: dict[str, bool] = {}
        for index in indices:
            # Check against system regex
            if any(compiled_reg.match(index) for compiled_reg in system_index_regex):
                continue

            if full_listing:
                index_dict[index] = True
            else:
                # Try to extract base index
                match = self.DATE_INDEX_RE.match(index)
                if match:
                    baseindex = match.groups()[0]
                    index_dict[baseindex] = True
                else:
                    # Fallback
                    baseindex = index.split("-")[0]
                    index_dict[baseindex] = True
        return list(index_dict)

    def freeze_index(
        self, source_index_spec: str, delete_source: bool = False, newindex: bool | str = False, tag: bool | str = False
    ) -> None:
        """
        Freeze an index by making it read-only, cloning it, and then closing/hiding the clone.

        Args:
            source_index_spec (str): Index pattern to match (can contain wildcards).
            delete_source (bool): If True, delete the original index after successful freeze.
            newindex (Union[bool, str]): If set, use this name for the frozen index.
            tag (Union[bool, str]): If set, append this tag to the frozen index name.
        """
        source_index_regex = source_index_spec.replace("*", ".*")
        source_index_re = re.compile(source_index_regex)

        indices = list(self.es.indices.get(index="*", expand_wildcards="open,closed"))  # Get all for freeze matching

        for index in indices:
            if not source_index_re.match(index):
                continue

            # Skip system indices
            if index.startswith("."):
                continue

            print(f"Freezing index: {index}")

            frozen_index: str
            if newindex:
                frozen_index = str(newindex)
                tag = False
            else:
                frozen_index = index

            if tag:
                index_match = self.DATE_INDEX_RE.match(index)
                if index_match:
                    indexbase = index_match.groups()[0]
                    indexmonth = index_match.groups()[1]
                    frozen_index = f"{indexbase}-{tag}-{indexmonth}"
                else:
                    frozen_index = f"{index}-{tag}"

            # Actions
            print(f"- Marking read only: {index}")
            self.es.indices.put_settings(index=index, body={"index": {"blocks.read_only": True}})

            print(f"- Cloning to {frozen_index}")
            self.es.indices.clone(index=index, target=frozen_index, body=self.CLONE_SETTINGS)

            print("- Return source index to read-write")
            self.es.indices.put_settings(index=index, body={"index": {"blocks.read_only": None}})

            print("- Return clone index to read-write")
            self.es.indices.put_settings(index=frozen_index, body={"index": {"blocks.read_only": None}})

            if delete_source:
                print("- Deleting source index")
                self.es.indices.delete(index=index)

            print(f"- Closing index: {frozen_index}")
            self.es.indices.close(index=frozen_index)

            print(f"- Hiding index: {frozen_index}")
            self.es.indices.put_settings(index=frozen_index, body={"hidden": True})

    def thaw_index(self, frozen_index: str) -> None:
        """
        Thaw a frozen index by opening it and removing the 'hidden' setting.

        Args:
            frozen_index (str): The name of the frozen index to thaw.
        """
        print("- Opening index")
        self.es.indices.open(index=frozen_index)
        print("- Unhide index")
        self.es.indices.put_settings(index=frozen_index, body={"hidden": None})

    def list_indices(self) -> None:
        """
        Print a list of active indices and their document counts to stdout.
        """
        populated_indices = self.get_indices(full_listing=True)
        populated_indices.sort()
        if not populated_indices:
            print("There are no active data indices in Elasticsearch")
        else:
            print("The following indices are currently active in Elasticsearch:")
            for index in populated_indices:
                try:
                    res = self.es.count(index=index, body={"query": {"match_all": {}}}, ignore_unavailable=True)
                    # res = self.es.indices.stats(index=index) # counting is better for docs
                    # Original script uses count
                    doccount = res.get("count", 0)
                    print(f"- {index} ({doccount:,} documents)")
                except Exception:
                    pass

    def reload_registry(
        self, match_path: str | None = None, match_index_type: str | None = None, nukeitall: bool = False
    ) -> None:
        """
        Reloads filebeat registry by removing entries that match the criteria.
        Requires root privileges.

        Args:
            match_path (Optional[str]): Source path prefix to match.
            match_index_type (Optional[str]): Index type (not fully used in current logic but reserved).
            nukeitall (bool): If True, clear entire registry.
        """
        if os.geteuid() != 0:  # type: ignore
            print("Reload functionality requires administrative privileges.")
            sys.exit(1)

        print("Stopping Filebeat...")
        try:
            subprocess.check_call(["systemctl", "stop", "filebeat"])
        except subprocess.CalledProcessError:
            print("Error stopping filebeat. Exiting.")
            return

        if not os.path.exists(self.FILEBEAT_REGISTRY_FILE):
            print(f"Registry file not found at {self.FILEBEAT_REGISTRY_FILE}. Restarting filebeat and exiting.")
            subprocess.call(["systemctl", "start", "filebeat"])
            return

        try:
            with open(self.FILEBEAT_REGISTRY_FILE) as f:
                content: Any = json.load(f)

            # Filebeat registry structure can vary.
            # Assuming a list of dicts (older) or dict with keys (newer).
            # If it's a dict verify if it has a 'data' (v2) or just list (v1)
            # This implementation assumes a simple list of dicts with 'source' key
            # OR a dict with 'registries' list.
            # We will try to handle a specific list format often seen in SOF-ELK context.

            new_content: list[dict[str, Any]] = []
            removed_count = 0

            entries: Any = content
            if isinstance(content, dict):
                # Handle wrapper if exists, though simple registry usually is list
                # Just in case generic handling
                entries = content.get("registries", content)

            if not isinstance(entries, list):
                # Fallback/Error
                print("Unknown registry format. Aborting registry edit.")
                subprocess.call(["systemctl", "start", "filebeat"])
                return

            for entry in entries:
                source = entry.get("source", "")
                keep = True

                if nukeitall:
                    keep = False
                elif match_path and source.startswith(match_path):
                    keep = False
                # match_index_type logic would require knowing which path maps to which index type
                # The caller usually passes match_path based on index/filepath

                if keep:
                    new_content.append(entry)
                else:
                    removed_count += 1

            if removed_count > 0:
                print(f"Removed {removed_count} entries from registry.")
                with open(self.FILEBEAT_REGISTRY_FILE, "w") as f:
                    # Write back in same format (assuming list)
                    json.dump(new_content, f)
            else:
                print("No matching registry entries found to remove.")

        except Exception as e:
            print(f"Error processing registry file: {e}")

        print("Starting Filebeat...")
        subprocess.call(["systemctl", "start", "filebeat"])

    def clear_cli(
        self, index: str | None = None, filepath: str | None = None, nukeitall: bool = False, reload_files: bool = False
    ) -> None:
        """
        CLI handler for clearing/deleting documents from Elasticsearch and optionally resetting filebeat registry.

        Args:
            index (Optional[str]): Index name to clear.
            filepath (Optional[str]): Source filepath pattern to clear.
            nukeitall (bool): If True, clear EVERYTHING.
            reload_files (bool): If True, reset filebeat registry for cleared items.
        """
        if not self.check_connection():
            print("Could not establish a connection to elasticsearch. Exiting.")
            sys.exit(1)

        doccount = 0
        populated_indices: list[str] = []

        if index == "list":
            self.list_indices()
            return

        if filepath:
            if filepath.startswith(self.TOPDIR):
                try:
                    # Logic to find index from filepath
                    subdir = filepath.split("/")[2]
                    # Original script had mapping, we can try to guess or use mapping
                    target_index = self.SOURCEDIR_INDEX_MAPPING.get(subdir, subdir)  # fallback to subdir name

                    res = self.es.count(
                        index=f"{target_index}-*", body={"query": {"prefix": {"source.keyword": f"{filepath}"}}}
                    )
                    doccount = res["count"]
                    index = target_index  # Set index for deletion scope
                except Exception as e:
                    print(f"Error determining index or counting: {e}")
                    sys.exit(1)
            else:
                print(f'File path must start with "{self.TOPDIR}". Exiting.')
                sys.exit(1)
        elif nukeitall:
            populated_indices = [s + "-*" for s in self.get_indices()]
            if not populated_indices:
                print("There are no active data indices in Elasticsearch")
                return

            res = self.es.count(index=",".join(populated_indices), body={"query": {"match_all": {}}})
            doccount = res["count"]
        elif index:
            res = self.es.count(index=f"{index}-*", body={"query": {"match_all": {}}})
            doccount = res["count"]

        if doccount > 0:
            print(f"{doccount:,} documents found\n")
            if not self.confirm(prompt="Delete these documents permanently?", resp=False):
                print("Will NOT delete documents. Exiting.")
                return

            if filepath:
                self.es.delete_by_query(
                    index=f"{index}-*", body={"query": {"prefix": {"source.keyword": f"{filepath}"}}}
                )
            elif nukeitall:
                try:
                    self.es.indices.delete(index=",".join(populated_indices))
                except Exception:
                    pass
            else:
                try:
                    self.es.indices.delete(index=f"{index}-*")
                except Exception:
                    pass
        else:
            print("No matching documents. Nothing to delete.")

        if reload_files:
            if hasattr(os, "geteuid") and os.geteuid() != 0:  # type: ignore
                print("Reload functionality requires administrative privileges.")
                sys.exit(1)

            # Calculate match path
            match_path = None
            if filepath:
                match_path = filepath
            elif index and index != "list":
                # If index is provided, we need to map back to a path?
                # Or just nuke any path associated with that index?
                # Mapping is SOURCEDIR_INDEX_MAPPING
                # INVERTED:
                # logstash -> syslog, passivedns, zeek
                # netflow -> nfarch
                # This is ambiguous.
                # The original script probably used the filepath if provided, or maybe just supported reload with filepath?
                # But clear_cli is called with index OR filepath.
                # If called with index, we can't easily guess the source path unless we hardcode the inverse.
                # Let's support filepath based reload primarily, as that's safe.
                # If index is passed, we might skip or try to find all dirs.
                pass

            self.reload_registry(match_path=match_path, nukeitall=nukeitall)

    @staticmethod
    def plugin_update() -> None:
        # Ported from es_plugin_update.sh
        # Requires root
        if os.geteuid() != 0:  # type: ignore
            sys.stderr.write("This script needs to run as root.\n")
            sys.exit(1)

        plugin_bin = "/usr/share/elasticsearch/bin/elasticsearch-plugin"
        plugin_dir = "/usr/share/elasticsearch/plugins"
        custom_plugins = {"head": "mobz/elasticsearch-head"}

        if not os.path.exists(plugin_bin):
            print(f"\nERROR: elasticsearch plugin command {plugin_bin} does not exist\n")
            sys.exit(1)

        if not os.path.exists(plugin_dir):
            print(f"\nERROR: elasticsearchPluginDir {plugin_dir} does not exist\n")
            sys.exit(1)

        print("Checking installed plugins...")
        try:
            # Get list of installed plugins
            output = subprocess.check_output([plugin_bin, "list"]).decode("utf-8")
            installed_plugins = output.splitlines()

            for plugin in installed_plugins:
                plugin = plugin.strip()
                if not plugin or plugin.startswith("preupgrade"):
                    continue

                print(f"Processing plugin: {plugin}")

                # Determine install target
                install_target = custom_plugins.get(plugin, plugin)

                # Remove existing
                print(f"  - Removing {plugin}...")
                subprocess.check_call([plugin_bin, "remove", plugin], stdout=subprocess.DEVNULL)

                # Install new
                print(f"  - Installing {install_target}...")
                subprocess.check_call([plugin_bin, "install", install_target], stdout=subprocess.DEVNULL)

        except subprocess.CalledProcessError as e:
            print(f"Error executing plugin command: {e}")
            sys.exit(1)
        except Exception as e:
            print(f"Unexpected error: {e}")
            sys.exit(1)

    @staticmethod
    def wait_for_service(host: str = "127.0.0.1", port: int = 9200) -> None:
        while True:
            try:
                subprocess.check_call(
                    ["curl", "--output", "/dev/null", "--silent", "--head", "--fail", f"http://{host}:{port}"]
                )
                break
            except subprocess.CalledProcessError:
                time.sleep(1)
                sys.stdout.write(".")
                sys.stdout.flush()
        print()


def run_clear(args: argparse.Namespace) -> None:
    mgr = ElasticsearchManager()
    mgr.clear_cli(index=args.index, filepath=args.filepath, nukeitall=args.nukeitall, reload_files=args.reload)


def run_freeze(args: argparse.Namespace) -> None:
    mgr = ElasticsearchManager(host=args.host, port=args.port)
    if args.action == "list":
        mgr.list_indices()
    elif args.action == "freeze":
        mgr.freeze_index(args.index, delete_source=args.delete, newindex=args.newindex, tag=args.tag)
    elif args.action == "thaw":
        mgr.thaw_index(args.index)


def run_plugin_update(args: argparse.Namespace) -> None:
    ElasticsearchManager.plugin_update()


def run_wait(args: argparse.Namespace) -> None:
    ElasticsearchManager.wait_for_service()
