import argparse
import json
import os
import sys
import time
from typing import Any

from elasticsearch import Elasticsearch


class KibanaManager:
    SOF_ELK_ROOT = "/usr/local/sof-elk/"
    KIBANA_FILE_DIR = os.path.join(SOF_ELK_ROOT, "kibana/")

    def __init__(
        self, es_host: str = "localhost", es_port: int = 9200, kibana_host: str = "localhost", kibana_port: int = 5601
    ) -> None:
        self.es_host = es_host
        self.es_port = es_port
        self.kibana_host = kibana_host
        self.kibana_port = kibana_port
        self.es_url = f"http://{es_host}:{es_port}"
        self.kibana_url = f"http://{kibana_host}:{kibana_port}"
        self.es = Elasticsearch([{"host": es_host, "port": es_port}])

    def _wait_for_es(self, max_wait: int = 60) -> bool:
        wait_step = 0
        interval = 5
        while wait_step <= max_wait:
            try:
                self.es.cluster.health()
                return True
            except Exception:
                time.sleep(interval)
                wait_step += interval
        return False

    def _load_template(self, template_type: str, filepath: str) -> None:
        # Template type: component_template or index_template
        # filename component-NAME.json -> NAME
        filename = os.path.basename(filepath)
        if template_type == "component_template":
            name = filename.replace("component-", "").replace(".json", "")
        else:
            name = filename.replace("index-", "").replace(".json", "")

        with open(filepath) as f:
            data: dict[str, Any] = json.load(f)

        # Use ES client or requests?
        # Using ES client for templates is cleaner
        try:
            if template_type == "component_template":
                self.es.cluster.put_component_template(name=name, body=data)
            else:
                self.es.indices.put_index_template(name=name, body=data)
            print(f"Loaded ES {template_type.replace('_', ' ').title()}: {name}")
        except Exception as e:
            print(f"Error loading template {name}: {e}")

    # _kibana_request removed in favor of sof_elk.api.kibana.KibanaClient

    def load_all(self) -> None:
        """
        Load all core Kibana objects, including templates, config defaults, priority settings, data views, and dashboards.

        Steps:
        1. Checks Elasticsearch availability.
        2. Loads Component and Index templates from the filesystem.
        3. Applies Kibana configuration defaults (e.g., dark mode, state saving).
        4. Increases index recovery priority for .kibana indices.
        5. Loads Data Views ( Index Patterns).
        6. Loads Saved Objects (Visualizations, Dashboards, etc.) in bulk.
        """
        if not self._wait_for_es():
            print("Elasticsearch not available.")
            sys.exit(5)

        # 1. Load ES Templates
        tpl_base = os.path.join(self.SOF_ELK_ROOT, "lib/elasticsearch_templates")

        comp_dir = os.path.join(tpl_base, "component_templates")
        if os.path.exists(comp_dir):
            for f in os.listdir(comp_dir):
                if f.endswith(".json"):
                    self._load_template("component_template", os.path.join(comp_dir, f))

        idx_dir = os.path.join(tpl_base, "index_templates")
        if os.path.exists(idx_dir):
            for f in os.listdir(idx_dir):
                if f.endswith(".json"):
                    self._load_template("index_template", os.path.join(idx_dir, f))

        # 2. Kibana Defaults
        kibana_version = "7.17.0"
        try:
            with open("/usr/share/kibana/package.json") as f:
                pkg = json.load(f)
                kibana_version = pkg.get("version", kibana_version)
        except Exception:
            pass

        # Initialize KibanaClient
        from sof_elk.api.kibana import KibanaClient

        k_client = KibanaClient(host=self.kibana_host, port=self.kibana_port)

        config_file = os.path.join(self.KIBANA_FILE_DIR, "sof-elk_config.json")
        if os.path.exists(config_file):
            print("Setting Kibana Defaults")
            with open(config_file) as f:
                data = json.load(f)

            # Native call using client internal session or create explicit method for config?
            # KibanaClient doesn't have 'post_config', but we can use client base or add it.
            # For now, using direct client access for non-standard saved object endpoint
            # Or better, extend the client if frequent. Here it's one-off.
            # Actually, /api/saved_objects/config/... IS a saved object call, but distinct.
            # We will use the generic 'import' or just custom post.
            url = k_client._get_url(f"/api/saved_objects/config/{kibana_version}?overwrite=true")
            try:
                k_client.client.post(url, json=data)
            except Exception as e:
                print(f"Error setting config: {e}")

        # 3. Priority
        print("Increasing Kibana index recovery priority")
        try:
            self.es.indices.put_settings(index=".kibana", body={"index": {"priority": 100}})
        except Exception:
            pass

        # 4. Data Views
        dv_dir = os.path.join(self.KIBANA_FILE_DIR, "data_views")
        if os.path.exists(dv_dir):
            for f in os.listdir(dv_dir):
                if f.endswith(".json"):
                    dvid = f.replace(".json", "")
                    print(f"Loading Data View: {dvid}")
                    # Delete first
                    try:
                        k_client.client.delete(k_client._get_url(f"/api/data_views/data_view/{dvid}"))
                    except Exception:
                        pass

                    with open(os.path.join(dv_dir, f)) as jf:
                        jdata = json.load(jf)
                    try:
                        k_client.client.post(k_client._get_url("/api/data_views/data_view"), json=jdata)
                    except Exception as e:
                        print(f"Error loading data view {dvid}: {e}")

        # 5. Objects (bulk)
        ndjson_lines = []
        for obj_type in ["visualization", "lens", "map", "search", "dashboard"]:
            obj_dir = os.path.join(self.KIBANA_FILE_DIR, obj_type)
            if os.path.exists(obj_dir):
                print(f"Preparing objects: {obj_type}")
                for f in os.listdir(obj_dir):
                    if f.endswith(".json"):
                        with open(os.path.join(obj_dir, f)) as jf:
                            line = json.load(jf)
                            ndjson_lines.append(json.dumps(line))

        if ndjson_lines:
            print("Loading objects in bulk")
            import tempfile

            with tempfile.NamedTemporaryFile(mode="w", suffix=".ndjson", delete=False) as tmp:
                tmp.write("\n".join(ndjson_lines))
                tmp_path = tmp.name

            try:
                k_client.import_objects(tmp_path)
            except Exception as e:
                print(f"Error importing objects: {e}")

            os.remove(tmp_path)


def run_load_dashboards(args: argparse.Namespace) -> None:
    mgr = KibanaManager(
        es_host=args.es_host, es_port=args.es_port, kibana_host=args.kibana_host, kibana_port=args.kibana_port
    )
    mgr.load_all()


def register_subcommand(subparsers: Any) -> None:
    # This might need to be added to management/cli.py manually as its structure is different
    # But if we treat this module as part of management package, we can expose it.
    pass
