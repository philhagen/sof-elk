#!/usr/bin/env python3
# SOF-ELK(R) Supporting script
# (C)2019 Lewes Technology Consulting, LLC
#
# This script is used to NUKE data from elasticsearch.  This is incredibly destructive!
# Optionally, re-load data from disk for the selected index or filepath

from elasticsearch import Elasticsearch
from subprocess import call
from io import open
from builtins import input
import json
import os
import argparse
import signal
import re

# set the top-level root location for all loaded files
topdir = '/logstash/'

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
        prompt = 'Confirm'

    if resp:
        prompt = '%s [%s]|%s: ' % (prompt, 'y', 'n')
    else:
        prompt = '%s [%s]|%s: ' % (prompt, 'n', 'y')

    while True:
        ans = input(prompt)
        if not ans:
            return resp
        if ans not in ['y', 'Y', 'n', 'N']:
            print('please enter y or n.')
            continue
        if ans == 'y' or ans == 'Y':
            return True
        if ans == 'n' or ans == 'N':
            return False

# return a list of files that match the supplied root path
def file_path_matches(path):
    matches = []
    for root, dirnames, filenames in os.walk(path):
        for filename in filenames:
            filepath = os.path.join(root, filename)
            if filepath.startswith(path):
                matches.append(filepath)
    return matches

# handle a ctrl-c cleanly
# source: https://stackoverflow.com/a/1112350
def ctrlc_handler(signal, frame):
    print('\n\nCtrl-C pressed. Exiting.')
    exit()
signal.signal(signal.SIGINT, ctrlc_handler)

# get a list of indices other than the standard set
def get_es_indices(es):
    special_index_rawregex = [ '\.elasticsearch', '\.kibana', '\.logstash', '\.tasks', 'elastalert_.*', '.apm*' ]
    special_index_regex = []
    for raw_regex in special_index_rawregex:
        special_index_regex.append(re.compile(raw_regex))

    index_dict = {}
    indices = list(es.indices.get_alias('*'))
    for index in indices:
        if not any(compiled_reg.match(index) for compiled_reg in special_index_regex):
            baseindex = index.split('-')[0]
            index_dict[baseindex] = True
    return list(index_dict)

# this dictionary associates each on-disk source location with its corresponding ES index root name
sourcedir_index_mapping = {
    'syslog': 'logstash',
    'passivedns': 'logstash',
    'zeek': 'logstash',
    'nfarch': 'netflow',
    'httpd': 'httpdlog',
    'kape': 'lnkfiles',
    'kape': 'filesystem',
    'kape': 'evtxfiles',
}
# automatically create the reverse dictionary
index_sourcedir_mapping = {}
for (k, v) in sourcedir_index_mapping.items():
    index_sourcedir_mapping[v] = index_sourcedir_mapping.get(v, [])
    index_sourcedir_mapping[v].append(topdir + k)

filebeat_registry_file='/var/lib/filebeat/registry'

parser = argparse.ArgumentParser(description='Clear the SOF-ELK(R) Elasticsearch database and optionally reload the input files for the deleted index.  Optionally narrow delete/reload scope to a file or parent path on the local filesystem.')
group = parser.add_mutually_exclusive_group(required=True)
group.add_argument('-i', '--index', dest='index', help='Index to clear.  Use "-i list" to see what is currently loaded.')
group.add_argument('-f', '--filepath', dest='filepath', help='Local directory root or single local file to clear.')
group.add_argument('-a', '--all', dest='nukeitall', action='store_true', default=False, help='Remove all documents from all indices.')
parser.add_argument('-r', '--reload', dest='reload', action='store_true', default=False, help='Reload source files from SOF-ELK(R) filesystem.  Requires "-f".')
args = parser.parse_args()

if args.reload and os.geteuid() != 0:
    print("Reload functionality requires administrative privileges.  Run with 'sudo'.")
    exit(1)

# create Elasticsearch handle
es = Elasticsearch([{'host': 'localhost', 'port': 9200}])
try:
    es.info()    
except:
    print("Could not establish a connection to elasticsearch.  Exiting.")
    exit(1)

# get list of top-level indices if requested
if args.index == 'list':
    populated_indices = get_es_indices(es)
    populated_indices.sort()
    if len(populated_indices) == 0:
        print('There are no active data indices in Elasticsearch')

    else:
        print('The following indices are currently active in Elasticsearch:')
        for index in populated_indices:
            res = es.count(index='%s-*' % (index), body={'query': {'match_all': {}}})
            doccount = res['count']

            print('- %s (%s documents)' % (index, "{:,}".format(doccount)))
    exit(0)

### delete from existing ES indices
# display document count
if args.filepath:
    if args.filepath.startswith(topdir):
        # force-set the index based on the directory
        try:
            args.index = sourcedir_index_mapping[args.filepath.split('/')[2]]
        except KeyError:
            print('No corresponding index for requested filepath.  Exiting.')
            exit(1)

        res = es.count(index='%s-*' % (args.index), body={'query': {'prefix': {'source.keyword': '%s' % (args.filepath)}}})
        doccount = res['count']

    else:
        print('File path must start with "%s".  Exiting.' % (topdir))
        exit(1)

elif args.nukeitall:
    populated_indices = [s + '-*' for s in get_es_indices(es)]
    if len(populated_indices) == 0:
        print('There are no active data indices in Elasticsearch')
        doccount = 0
    else:
        res = es.count(index='%s' % (','.join(populated_indices)), body={'query': {'match_all': {}}})
        doccount = res['count']

else:
    res = es.count(index='%s-*' % (args.index), body={'query': {'match_all': {}}})
    doccount = res['count']

if doccount > 0:
    # get user confirmation to proceed
    print('%s documents found\n' % ("{:,}".format(doccount)))

    if not confirm(prompt='Delete these documents permanently?', resp=False):
        print('Will NOT delete documents.  Exiting.')
        exit(0)

    # delete the records
    if args.filepath:
        es.delete_by_query(index='%s-*' % (args.index), body={'query': {'prefix': {'source.keyword': '%s' % (args.filepath)}}})

    elif args.nukeitall:
        es.indices.delete(index='%s' % (','.join(populated_indices)), ignore=[400, 404])

    else:
        es.indices.delete(index='%s-*' % (args.index), ignore=[400, 404])

else:
    print('No matching documents.  Nothing to delete.')

### reload from source files
if args.reload:
    # display files to be re-loaded
    matches = []

    if args.index and not args.filepath:
        for filepath in index_sourcedir_mapping[args.index]:
            matches = matches + file_path_matches(filepath)
    elif args.filepath:
        matches = file_path_matches(args.filepath)
    elif args.nukeitall:
        matches = file_path_matches(topdir)

    # get user confirmation to proceed
    print('will re-load the following files:')
    for match in matches:
            print('- %s' % (match))
    print

    if not confirm(prompt='Reload these files?', resp=False):
        print('Will NOT reload from files.  Exiting.')
        exit(1)

    # stop filebeat service
    call(['/usr/bin/systemctl', 'stop', 'filebeat'])

    if os.path.isfile(filebeat_registry_file) and os.path.getsize(filebeat_registry_file) > 0:
        # load existing filebeat registry
        reg_file = open(filebeat_registry_file, 'rb')
        try:
            reg_data = json.load(reg_file)
            reg_file.close()

            # create new registry, minus the files to be re-loaded
            new_reg_data = []
            for filebeatrecord in reg_data:
                file = str(filebeatrecord['source'])
                if not file in matches:
                    new_reg_data.append(filebeatrecord)

            new_reg_file = open(filebeat_registry_file, 'wb')
            json.dump(new_reg_data, new_reg_file)
            new_reg_file.close()


        except JSONDecodeError:
            print('ERROR: Source data in filebeat registry file %s is not valid json.  Skipping.' % filebeat_registry_file)
    
    # restart the filebeat service
    call(['/usr/bin/systemctl', 'start', 'filebeat'])
