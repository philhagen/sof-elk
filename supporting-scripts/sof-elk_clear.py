#!/usr/bin/env python3
# SOF-ELK(R) Supporting script
# (C)2026 Lewes Technology Consulting, LLC
#
# This script is used to NUKE data from elasticsearch.  This is incredibly destructive!
# Optionally, re-load data from disk for the selected index or filepath

from elasticsearch import Elasticsearch
from subprocess import call, DEVNULL
from io import open
import json
import os
import argparse
import signal
import re

# set the top-level root location for all loaded files
topdir = "/logstash/"
log_path_field = "log.file.path.keyword"
filebeat_registry_filename = "/var/lib/filebeat/registry/filebeat/log.json"
filebeat_registry_checkpoint_filename = "/var/lib/filebeat/registry/filebeat/active.dat"
files_to_reload = []
doccount = 0
populated_indices = []

# source: http://code.activestate.com/recipes/541096-prompt-the-user-for-confirmation/
def confirm(prompt=None, default_resp=False):
    """prompts for yes or no response from the user. Returns True for yes and
    False for no.

    'resp' should be set to the default value assumed by the caller when
    user simply types ENTER.

    >>> confirm(prompt='Create Directory?', resp=True)
    Create Directory? [y]|n:
    True
    >>> confirm(prompt='Create Directory?', resp=False)
    Create Directory? [n]|y:
    False
    >>> confirm(prompt='Create Directory?', resp=False)
    Create Directory? [n]|y: y
    True
    """

    if prompt is None:
        prompt = "Confirm"

    if default_resp:
        prompt = "%s [%s]|%s: " % (prompt, "y", "n")
    else:
        prompt = "%s [%s]|%s: " % (prompt, "n", "y")

    while True:
        ans = input(prompt).lower()
        if not ans:
            return default_resp
        if ans not in ["y", "n" ]:
            print("please enter y or n.")
            continue
        if ans == "y":
            return True
        if ans == "n":
            return False


# return a list of files that match the supplied root path
def file_path_matches(path):
    matches = []

    if os.path.isfile(path):
        matches.append(path)

    else:
        for root, dirnames, filenames in os.walk(path):

            for filename in filenames:
                filepath = os.path.join(root, filename)
                if filepath.startswith(path):
                    matches.append(filepath)

    return matches


# handle a ctrl-c cleanly
# source: https://stackoverflow.com/a/1112350
def ctrlc_handler(signal, frame):
    print("\n\nCtrl-C pressed. Exiting.")

    if 'args' in globals() and args.reload:
        if call(["/usr/bin/systemctl", "unmask", "filebeat"], stdout=DEVNULL, stderr=DEVNULL) != 0:
            print("ERROR: Could not unmask filebeat service,  Exiting.")
            exit(1)

        if call(["/usr/bin/systemctl", "start", "filebeat"], stdout=DEVNULL, stderr=DEVNULL) != 0:
            print("ERROR: Could not start filebeat service.  Exiting.")
            exit(1)

    exit()


signal.signal(signal.SIGINT, ctrlc_handler)


# get a list of indices other than the standard set
def get_es_indices(es):
    special_index_rawregex = [
        ".elasticsearch",
        ".kibana",
        ".logstash",
        ".tasks",
        "elastalert_.*",
        ".apm.*",
        ".async",
        ".ds",
        ".internal.alerts",
        ".internal.cases",
        ".monitoring",
    ]
    special_index_regex = []
    for raw_regex in special_index_rawregex:
        special_index_regex.append(re.compile(raw_regex))

    index_dict = {}
    indices = list(es.indices.get_alias(index="*", expand_wildcards="open"))
    for index in indices:
        baseindex = "-".join(index.split("-")[:-1])
        if baseindex in index_dict:
            pass
        elif not any(compiled_reg.match(index) for compiled_reg in special_index_regex):
            index_dict[baseindex] = True
    return list(index_dict)


# scrub a registry file of any entry that is in the supplied list of files
# this function overwrites the specified registry file, so be sure filebeat is stopped first
def scrub_registry_file(registry_filename, file_list, checkpoint=False):
    if os.path.isfile(registry_filename) and os.path.getsize(registry_filename) > 0:
        # load existing filebeat registry
        with open (registry_filename, "r") as registry_file:
            reg_data = []

            # checkpoint files are arrays.  main registry file is jsonl. ugh.
            if checkpoint:
                try:
                    reg_data = json.load(registry_file, parse_float=preserve_sci_notation)

                except json.JSONDecodeError:
                    print(
                        "ERROR: Could not load json data from registry file %s."
                        % registry_filename
                    )

            else:
                for registry_line in registry_file:
                    try:
                        reg_data.append(
                            json.loads(registry_line, parse_float=preserve_sci_notation)
                        )

                    except json.JSONDecodeError:
                        print(
                            "ERROR: Skipping invalid json line in registry file %s."
                            % (registry_filename)
                        )


        # create new registry, minus the files to be re-loaded
        new_reg_data = []
        for registry_entry in reg_data:
            try:
                file = str(registry_entry["v"]["meta"]["source"])
                if not file in file_list:
                    new_reg_data.append(registry_entry)

            except KeyError:
                new_reg_data.append(registry_entry)

        with open(registry_filename, "w") as new_reg_file:

            if checkpoint:
                new_reg_file.write(dumps_preserving_notation(new_reg_data))

            else:
                for new_line in new_reg_data:
                    new_reg_file.write(dumps_preserving_notation(new_line) + "\n")


# these are needed to preserve numerical formatting within the JSON in the registry file
class RawJSON:
    """Wraps a raw JSON number/text so it's emitted verbatim, unquoted."""

    def __init__(self, raw_text):
        self.raw = raw_text


def preserve_sci_notation(s):
    # s is the original numeric substring exactly as it appeared in the source
    if "e" in s or "E" in s:
        return RawJSON(s)
    return float(s)  # normal floats parse/format as usual


class RawJSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, RawJSON):
            return f"@@RAW@@{o.raw}@@RAW@@"
        return super().default(o)


def dumps_preserving_notation(data):
    s = json.dumps(data, cls=RawJSONEncoder, ensure_ascii=False, separators=(",", ":"))
    return re.sub(r'"@@RAW@@(.*?)@@RAW@@"', lambda m: m.group(1), s)


# end numerical-formatting preservation

parser = argparse.ArgumentParser(
    description="Clear the SOF-ELK(R) Elasticsearch database and optionally reload the input files for the deleted index.  Optionally narrow delete/reload scope to a file or parent path on the local filesystem."
)
operation = parser.add_mutually_exclusive_group(required=True)
operation.add_argument(
    "-i",
    "--index",
    dest="index",
    help='Index to clear.  Use "-i list" to see what is currently loaded.',
)
operation.add_argument(
    "-f",
    "--filepath",
    dest="filepath",
    help="Local directory root or single local file to clear.",
)
operation.add_argument(
    "-a",
    "--all",
    dest="nukeitall",
    action="store_true",
    default=False,
    help="Remove all documents from all indices.",
)
parser.add_argument(
    "-r",
    "--reload",
    dest="reload",
    action="store_true",
    default=False,
    help='Reload source files from SOF-ELK(R) filesystem, as indicated by existing documents and their respective sources, or the index and the documents it contains.',
)
args = parser.parse_args()

# create Elasticsearch handle
es = Elasticsearch(["http://localhost:9200"])
try:
    es.info()
except Exception:
    print("Could not establish a connection to elasticsearch.  Exiting.")
    exit(1)

if args.index == "":
    print("ERROR: Must specify index name with '-i'.")
    exit(1)

# get list of top-level indices if requested
if args.index == "list":
    populated_indices = get_es_indices(es)
    populated_indices.sort()
    if len(populated_indices) == 0:
        print("There are no active data indices in Elasticsearch")

    else:
        print("The following indices are currently active in Elasticsearch:")
        for index in populated_indices:
            res = es.count(index="%s-*" % (index), query={"match_all": {}})
            doccount = res["count"]

            print("- %s (%s documents)" % (index, "{:,}".format(doccount)))
    exit(0)


# do this up front to ensure full and consistent deletion of records if there is a reload (aka prevent records from shipping while this script is running)
if args.reload:
    if os.geteuid() != 0:
        print("Reload functionality requires administrative privileges.  Run with 'sudo'.")
        exit(1)

    # stop and mask filebeat service
    # masking prevents another process from starting the service while this script is operating
    # TODO: this will result in a race condition if this script fails before the service is unmasked and restarted
    if call(["/usr/bin/systemctl", "stop", "filebeat"], stdout=DEVNULL, stderr=DEVNULL) != 0:
        print("ERROR: Could not stop filebeat service.  Exiting.")
        exit(1)

    if call(["/usr/bin/systemctl", "mask", "filebeat"], stdout=DEVNULL, stderr=DEVNULL) != 0:
        print("ERROR: Could not mask filebeat service,  Exiting.")
        exit(1)

### delete from existing ES indices
# display document count
if args.filepath:
    if os.path.isdir(args.filepath) and not args.filepath.endswith(os.sep):
        args.filepath += os.sep

    ### TODO: CHANGE FROM PREFIX TO FILEGLOB.  WILL NEED TO CHANGE ES QUERY AS WELL
    if args.filepath.startswith(topdir):
        res = es.count(
            index="*",
            query={"prefix": {log_path_field: args.filepath}},
        )
        doccount = res["count"]

    else:
        print('File path must start with "%s".  Exiting.' % (topdir))
        exit(1)

elif args.nukeitall:
    populated_indices = [s + "-*" for s in get_es_indices(es)]
    if len(populated_indices) == 0:
        print("There are no active data indices in Elasticsearch")

    else:
        res = es.count(
            index="%s" % (",".join(populated_indices)),
            query={"match_all": {}},
        )
        doccount = res["count"]

elif args.index:
    if args.reload:
        res = es.search(index="%s-*" % (args.index), size=0, aggs={"unique_categories": {"terms": {"field": log_path_field, "size": 10000}}})

        for file in res.body['aggregations']['unique_categories']['buckets']:
            filename = file['key']
            doccount += file['doc_count']

            if os.path.isfile(filename):
                files_to_reload.append(filename)
            else:
                print("- FILE NO LONGER PRESENT - WILL DELETE BUT CANNOT RELOAD: %s (%d records)" % (file['key'], file['doc_count']))

    else:
        res = es.count(index="%s-*" % (args.index), query={"match_all": {}})
        doccount = res["count"]

if doccount > 0:
    # get user confirmation to proceed
    print("%s documents found\n" % ("{:,}".format(doccount)))

    if not confirm(prompt="Delete these documents permanently?", default_resp=False):
        print("Will NOT delete documents.  Exiting.")
        exit(0)

    # delete the records
    if args.filepath:
        es.delete_by_query(
            index="*",
            query={"prefix": {log_path_field: args.filepath}},
        )

    elif args.nukeitall:
        es.options(ignore_status=[400, 404]).indices.delete(
            index="%s" % (",".join(populated_indices))
        )

    elif args.index:
        es.options(ignore_status=[400, 404]).indices.delete(index="%s-*" % (args.index))

else:
    print("No matching documents.  Nothing to delete.")

### reload from source files
if args.reload:
    # if args.index is set, files_to_reload[] has been populated above
    if args.filepath:
        files_to_reload = file_path_matches(args.filepath)
    elif args.nukeitall:
        files_to_reload = file_path_matches(topdir)

    # get user confirmation to proceed
    print("will re-load the following files:")
    for match in files_to_reload:
        print("- %s" % (match))

    if not confirm(prompt="Reload these files?", default_resp=False):
        print("Will NOT reload from files.  Exiting.")
        exit(1)

    # if there is a checkpoint file, scrub it first
    if (
        os.path.isfile(filebeat_registry_checkpoint_filename)
        and os.path.getsize(filebeat_registry_checkpoint_filename) > 0
    ):
        with open(
            filebeat_registry_checkpoint_filename, "r"
        ) as filebeat_registry_checkpoint_file:
            checkpoint_filename = filebeat_registry_checkpoint_file.read().strip()

        scrub_registry_file(checkpoint_filename, files_to_reload, checkpoint=True)

    # scrub the main registry file
    scrub_registry_file(filebeat_registry_filename, files_to_reload)

    # TODO: this should probably be put inside an exit/cleanup handler to ensure it restarts
    # unmask and restart the filebeat service
    if call(["/usr/bin/systemctl", "unmask", "filebeat"], stdout=DEVNULL, stderr=DEVNULL) != 0:
        print("ERROR: Could not unmask filebeat service.  Exiting.")
        exit(1)

    if call(["/usr/bin/systemctl", "start", "filebeat"], stdout=DEVNULL, stderr=DEVNULL) != 0:
        print("ERROR: Could not start filebeat service,  Exiting.")
        exit(1)
