#!/usr/bin/env python3
# SOF-ELK(R) Supporting script
# (C)2025 Lewes Technology Consulting, LLC
#
# This script is used to take elasticsearch indices offline or back online again.
# The resulting frozen index is not truly "hidden" from someone that knows Elasticsearch well, but will prevent casual browsing until the index is thawed.

# operations:
# - freeze: take an index or indices offline and hide from wildcard searches
# - thaw:   return an index or indices to online status and allow discovery with wildcard searches
# - list:   list all indices

from elasticsearch import Elasticsearch
from builtins import input
import argparse
import signal
import re
import sys

# regex for SOF-ELK's index patterns, which split documents by month
date_index_re = re.compile("(.*)-([0-9]{4}\.[0-9]{2})")

# settings applied to each newly cloned index prior to freezing
clone_settings = '{ "settings": { "index.number_of_shards": 1 } }'


# ask a yes/no question and comprehensively get response
# source: http://code.activestate.com/recipes/541096-prompt-the-user-for-confirmation/
def confirm(prompt=None, resp=False):
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

    if resp:
        prompt = "%s [%s]|%s: " % (prompt, "y", "n")
    else:
        prompt = "%s [%s]|%s: " % (prompt, "n", "y")

    while True:
        ans = input(prompt)
        if not ans:
            return resp
        if ans not in ["y", "Y", "n", "N"]:
            print("please enter y or n.")
            continue
        if ans == "y" or ans == "Y":
            return True
        if ans == "n" or ans == "N":
            return False


# handle a ctrl-c cleanly
# source: https://stackoverflow.com/a/1112350
def ctrlc_handler(signal, frame):
    print("\n\nCtrl-C pressed. Exiting.")
    exit()


signal.signal(signal.SIGINT, ctrlc_handler)


# create a nullwriter to suppress stderr
# source: http://coreygoldberg.blogspot.com/2009/05/python-redirect-or-turn-off-stdout-and.html
class NullDevice:
    def write(self, s):
        pass


# get a list of indices *other than* system indices and specified ignored indices
def get_es_indices(es, full_listing=False):
    system_index_rawregex = ["\..*", "elastalert_.*"]
    system_index_regex = []
    for raw_regex in system_index_rawregex:
        system_index_regex.append(re.compile(raw_regex))

    indices = list(es.indices.get(index="*", expand_wildcards="open,closed"))

    index_dict = {}
    for index in indices:
        if not any(compiled_reg.match(index) for compiled_reg in system_index_regex):
            if full_listing:
                index_dict[index] = True
            else:
                baseindex = date_index_re.match(index).groups()[0]
                index_dict[baseindex] = True

    return list(index_dict)


def freeze_index(es, source_index_spec, delete_source, newindex=False, tag=False):
    # we might get an index specification with a wildcard like "foo-*" so that notation needs to be regex-ified
    source_index_regex = source_index_spec.replace("*", ".*")
    source_index_re = re.compile(source_index_regex)

    indices = get_es_indices(es, True)
    for index in indices:
        # ignore indices that don't match the constructed regex
        if source_index_re.match(index) == None:
            continue

        print("Freezing index: %s" % (index))

        if newindex:
            frozen_index = newindex
            tag = False

        else:
            frozen_index = index

        # if we're applying a tag, create the new index name
        if tag:
            index_match = date_index_re.match(index)

            # if the index name has a SOF-ELK-formatted year+month, place the tag accordingly
            if index_match:
                indexbase = index_match.groups()[0]
                indexmonth = index_match.groups()[1]
                frozen_index = "%s-%s-%s" % (indexbase, tag, indexmonth)

            # if the index name doesn't have a year+month, append the tag to the end
            else:
                frozen_index = "%s-%s" % (index, tag)

            ### take the current index offline
            ## set it read-only
            print("- Marking read only: %s" % (index))
            es.indices.put_settings(
                index=index, body='{ "index": { "blocks.read_only": true } }'
            )
            ### this should work but there is no reverse method at this time... so I'm using the above to remain parallel with the later un-read-only step
            # es.indices.add_block(index=index, block='read_only')

            ## clone to a new index
            print("- Cloning to %s" % (frozen_index))
            es.indices.clone(index=index, target=frozen_index, body=clone_settings)

            ## set clone and original back to read-write
            print("- Return source index to read-write")
            es.indices.put_settings(
                index=index, body='{ "index": { "blocks.read_only": null } }'
            )
            print("- Return clone index to read-write")
            es.indices.put_settings(
                index=frozen_index, body='{ "index": { "blocks.read_only": null } }'
            )

            if delete_source:
                ## delete original index
                print("- Deleting source index")
                es.indices.delete(index=index)

        ## close and "hide" the clone (however "hide" just prevents the index from being shown as a result of wildcard searches)
        print("- Closing index: %s" % (frozen_index))
        es.indices.close(index=frozen_index, wait_for_active_shards="index-setting")

        print("- Hiding index: %s" % (frozen_index))
        es.indices.put_settings(index=frozen_index, body='{ "hidden": true }')

    ## TODO: optionally encrypt the files?
    #        - get the filesystem source directory for the index via ES API
    #        - run a 7z or similar command, placing encrypted archive in e.g. <index_name>.7z
    #        - remove the source directory


def thaw_index(es, frozen_index):
    ## TODO: Handle wildcarded frozen_index specification

    ## TODO: handle encrypted files?
    #        - run a 7z or similar command, extracting and decrypting files from archive
    #        - remove the archive file??

    # open and un-"hide" the index
    print("- Opening index")
    es.indices.open(index=frozen_index)
    print("- Unhide index")
    es.indices.put_settings(index=frozen_index, body='{ "hidden": null }')


parser = argparse.ArgumentParser(
    description="Disable or re-enable Elasticsearch indices, optionally renaming the frozen index."
)
parser.add_argument(
    "-e", "--host", dest="host", default="127.0.0.1", help="Elasticsearch IP address"
)
parser.add_argument(
    "-p", "--port", dest="port", default="9200", help="Elasticsearch port"
)
parser.add_argument(
    "-a",
    "--action",
    dest="action",
    help="Action to take.",
    choices=["freeze", "thaw", "list"],
    required=True,
)
parser.add_argument("-i", "--index", dest="index", help="Index to act on.")
parser.add_argument(
    "-t",
    "--tag",
    dest="tag",
    default=False,
    help='An optional tag to add to indices being frozen.  E.g. the "httpdlog-2021.10" index becomes "httpdlog-lab3.1-2021.10" by specifying a tag of "lab3.1".  Only works for the freeze action.',
)
parser.add_argument(
    "-n",
    "--newindex",
    dest="newindex",
    default=False,
    help="Name for the new index to be created.  Overrides -t/--tag.",
)
parser.add_argument(
    "-d",
    "--delete",
    dest="delete",
    action="store_true",
    help='Delete the source index for a "freeze" action.  Only works when -t or -n are specified.',
)
args = parser.parse_args()

if args.action in ["freeze", "thaw"] and not args.index:
    print("Requested action requires index name but none was supplied.  Exiting.")
    exit(1)

# create Elasticsearch handle
es = Elasticsearch([{"host": args.host, "port": args.port, "timeout": 300}])
try:
    es.info()
except:
    print("Could not establish a connection to elasticsearch.  Exiting.")
    exit(1)

# get list of top-level indices if requested
if args.action == "list":
    populated_indices = get_es_indices(es, True)
    populated_indices.sort()

    if len(populated_indices) == 0:
        print("There are no active data indices in Elasticsearch")

    else:
        print("The following indices are currently active in Elasticsearch:")
        for index in populated_indices:
            res = es.count(
                index="%s" % (index),
                body={"query": {"match_all": {}}},
                ignore_unavailable=True,
            )

            # this will be zero if the index is closed, and therefore it shouldn't be listed
            if res["_shards"]["total"] > 0:
                doccount = res["count"]
                print("- %s (%s documents)" % (index, "{:,}".format(doccount)))

    exit(0)

elif args.action == "freeze":
    freeze_index(es, args.index, args.delete, args.newindex, args.tag)

elif args.action == "thaw":
    thaw_index(es, args.index)
