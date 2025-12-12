from .elasticsearch import run_clear, run_freeze, run_plugin_update as run_es_plugin_update, run_wait
from .git import run_branch, run_update, run_check_pull, run_remote_update
from .kibana import run_load_dashboards
from .logstash import run_plugin_update as run_ls_plugin_update
from .vm import run_vm_check
from .distro import DistroManager
from typing import Any

"""
Management Subcommands
======================

This module registers the `management` subcommand and its various children (elasticsearch,
kibana, git, logstash, vm) with the main CLI parser.
"""

def register_subcommand(subparsers: Any) -> None:
    parser = subparsers.add_parser("management", help="Core management utilities")
    sub_subparsers = parser.add_subparsers(dest="mgmt_command", required=True)

    # ElasticSearch
    clear_parser = sub_subparsers.add_parser("clear", help="Clear ES indices")
    clear_parser.add_argument("-i", "--index", dest="index", help="Index to clear or 'list'")
    clear_parser.add_argument("-f", "--filepath", dest="filepath", help="Local directory root/file to clear")
    clear_parser.add_argument("-a", "--all", dest="nukeitall", action="store_true", help="Remove all documents")
    clear_parser.add_argument("-r", "--reload", dest="reload", action="store_true", help="Reload source files")
    clear_parser.set_defaults(func=run_clear)

    freeze_parser = sub_subparsers.add_parser("freeze", help="Freeze/Thaw ES indices")
    freeze_parser.add_argument("-a", "--action", dest="action", choices=["freeze", "thaw", "list"], required=True)
    freeze_parser.add_argument("-i", "--index", dest="index", help="Index to act on")
    freeze_parser.add_argument("-t", "--tag", dest="tag", default=False, help="Tag for frozen index")
    freeze_parser.add_argument("-n", "--newindex", dest="newindex", default=False, help="Name for new index")
    freeze_parser.add_argument("-d", "--delete", dest="delete", action="store_true", help="Delete source index")
    freeze_parser.add_argument("-e", "--host", dest="host", default="127.0.0.1", help="ES host")
    freeze_parser.add_argument("-p", "--port", dest="port", default=9200, type=int, help="ES port")
    freeze_parser.set_defaults(func=run_freeze)

    plugin_parser = sub_subparsers.add_parser("plugin_update", help="Update ES plugins")
    plugin_parser.set_defaults(func=run_es_plugin_update)

    wait_parser = sub_subparsers.add_parser("wait_for_es", help="Wait for ES service")
    wait_parser.set_defaults(func=run_wait)
    
    # Kibana
    kb_parser = sub_subparsers.add_parser("load_dashboards", help="Load Kibana dashboards and objects")
    kb_parser.add_argument("--es-host", dest="es_host", default="localhost", help="Elasticsearch Host")
    kb_parser.add_argument("--es-port", dest="es_port", default=9200, type=int, help="Elasticsearch Port")
    kb_parser.add_argument("--kibana-host", dest="kibana_host", default="localhost", help="Kibana Host")
    kb_parser.add_argument("--kibana-port", dest="kibana_port", default=5601, type=int, help="Kibana Port")
    kb_parser.set_defaults(func=run_load_dashboards)
    
    # Logstash
    ls_parser = sub_subparsers.add_parser("ls_plugin_update", help="Update Logstash plugins")
    ls_parser.set_defaults(func=run_ls_plugin_update)

    # VM
    vm_parser = sub_subparsers.add_parser("vm_update_check", help="Check for VM updates")
    vm_parser.set_defaults(func=run_vm_check)

    # Git
    branch_parser = sub_subparsers.add_parser("branch", help="Switch SOF-ELK branch")
    branch_parser.add_argument("branch", help="Branch name")
    branch_parser.add_argument("-f", dest="force", action="store_true", help="Force switch")
    branch_parser.set_defaults(func=run_branch)

    update_parser = sub_subparsers.add_parser("update", help="Update SOF-ELK repo")
    update_parser.add_argument("-f", dest="force", action="store_true", help="Force update")
    update_parser.set_defaults(func=run_update)

    check_parser = sub_subparsers.add_parser("check_pull", help="Check if git pull is needed")
    check_parser.add_argument("upstream", nargs="?", default="@{u}", help="Upstream branch")
    check_parser.set_defaults(func=run_check_pull)

    remote_update_parser = sub_subparsers.add_parser("remote_update", help="Update git remote")
    remote_update_parser.add_argument("-now", dest="now", action="store_true", help="Run immediately")
    remote_update_parser.set_defaults(func=run_remote_update)

    # Distro
    distro_parser = sub_subparsers.add_parser("distro_prep", help="Prepare VM for distribution")
    distro_parser.add_argument("-nodisk", dest="nodisk", action="store_true", help="Do not shrink disks")
    distro_parser.add_argument("-cloud", dest="cloud", action="store_true", help="Prepare cloud instance")
    distro_parser.set_defaults(func=lambda args: DistroManager.prep_for_distribution(args.nodisk, args.cloud))

    post_merge_parser = sub_subparsers.add_parser("post_merge", help="Run post-merge steps")
    post_merge_parser.set_defaults(func=lambda args: DistroManager.post_merge())
