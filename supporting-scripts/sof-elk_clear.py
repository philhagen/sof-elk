#!/usr/bin/python
# SOF-ELK Supporting script
# (C)2017 Lewes Technology Consulting, LLC
#
# This script is used to NUKE data from elasticsearch.  This is incredibly destructive!
# Optionally, re-load data from disk for the selected index or filepath

from elasticsearch import Elasticsearch
from subprocess import call
import json
import os
import argparse

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
        ans = raw_input(prompt)
        if not ans:
            return resp
        if ans not in ['y', 'Y', 'n', 'N']:
            print 'please enter y or n.'
            continue
        if ans == 'y' or ans == 'Y':
            return True
        if ans == 'n' or ans == 'N':
            return False

parser = argparse.ArgumentParser(description='Clear the SOF-ELK Elasticsearch database and optionally reload the input files for the deleted index.  Optionally narrow delete/reload scope to a file or parent path on the local filesystem.')
parser.add_argument('-i', '--index', dest='index', required=True, help='Index to clear.')
parser.add_argument('-f', '--filepath', dest='filepath', help='Local file or directory to clear.')
parser.add_argument('-r', '--reload', dest='reload', action='store_true', default=False, help='Reload source files from SOF-ELK filesystem.')
args = parser.parse_args()

### delete from existing ES indices
# display document count
es = Elasticsearch([{'host': 'localhost', 'port': 9200}])
if args.filepath:
    res = es.search(index='%s-*' % (args.index), body={'query': {'prefix': {'source.raw': '%s' % (args.filepath)}}})

else:
    res = es.search(index='%s-*' % (args.index), body={'query': {'match_all': {}}})

doccount = res['hits']['total']
if doccount > 0:
    # get user confirmation to proceed
    print '%d documents found' % res['hits']['total']
    print
    if not confirm(prompt='Delete these documents permanently?', resp=False):
        print 'Will NOT delete documents.  Exiting.'
        exit(1)

    # delete the records
    if args.filepath:
        es.delete_by_query(index='%s-*' % (args.index), body={'query': {'prefix': {'source.raw': '%s' % (args.filepath)}}})

    else:
        delres = es.indices.delete(index='%s-*' % (args.index), ignore=[400, 404])

else:
    print 'No documents in the %s index.  Nothing to delete.' % (args.index)

### reload from source files
if args.reload:
    # display files to be re-loaded
    matches = []
    for root, dirnames, filenames in os.walk('/logstash/%s' % (args.index)):
        for filename in filenames:
            filepath = os.path.join(root, filename)
            if args.filepath:
                if filepath.startswith(args.filepath):
                    matches.append(filepath)

            else:
                matches.append(filepath)

    # get user confirmation to proceed
    print 'will re-load the following files:'
    for match in matches:
            print '- %s' % ( match )
    print

    if not confirm(prompt='Reload these files?', resp=False):
        print 'Will NOT reload from files.  Exiting.'
        exit(1)

    # stop filebeat service
    call(['/usr/bin/systemctl', 'stop', 'filebeat'])

    # load existing filebeat registry
    reg_file = open('/var/lib/filebeat/registry')
    reg_data = json.load(reg_file)
    reg_file.close()

    # create new registry, minus the files to be re-loaded
    new_reg_data = {}
    for file in reg_data.keys():
        if not file.startswith('/logstash/%s' % (args.index)):
            new_reg_data[file] = reg_data[file]

    new_reg_file = open('/var/lib/filebeat/registry', 'w')
    json.dump(new_reg_data, new_reg_file)
    new_reg_file.close()

    # restart the filebeat service
    call(['/usr/bin/systemctl', 'start', 'filebeat'])