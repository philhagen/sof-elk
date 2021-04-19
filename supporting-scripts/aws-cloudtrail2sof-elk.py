#!/usr/bin/env python3
# SOF-ELK® Supporting script
# (C)2021 Lewes Technology Consulting, LLC
#
# This script will recursively read a file or directory tree of JSON AWS Cloudtrail logs and output in a format that SOF-ELK® can read.  Both gzipped and native JSON is supported.

import argparse
import sys
import os
import json
import gzip

default_destdir = '/logstash/aws/'

def process_cloudtrail_file(infile, outfh):
    # determine if this is a gzip file first
    input_file = gzip.open(infile, 'r')
    try:
        input_file.read()
        is_gzip = True
        input_file.seek(0)

    # py3.8+: except gzip.BadGzipFile:
    except OSError:
        # not a gzip file
        is_gzip = False
        input_file = open(infile, 'r')

    try:
        rawjson = json.load(input_file)

    except json.decoder.JSONDecodeError:
        sys.stderr.write('- ERROR: Could not process JSON from %s. Skipping file.\n' % (infile))
        return

    if not 'Records' in rawjson.keys():
        sys.stderr.write('- ERROR: Input file %s does not appear to contain AWS Cloudtrail records. Skipping file.\n' % (infile))
        return

    for record in rawjson['Records']:
        outfh.write('%s\n' % (record))

parser = argparse.ArgumentParser(description='Process AWS Cloudtrail logs into a format that SOF-ELK(R) can read, in ndjson form.')
parser.add_argument('-r', '--read', dest='infile', help='AWS Cloudtrail log file to read, or a directory containing AWS Cloudtrail log files.  Files can be in native JSON or gzipped JSON.')
parser.add_argument('-w', '--write', dest='outfile', help='File to create containing processed AWS Cloudtrail data.')
parser.add_argument('-f', '--force', dest='force_outfile', help='Force creating an output file in a location other than the default SOF-ELK ingest location, %s' % (default_destdir), default=False, action='store_true')
parser.add_argument('-a', '--append', dest='append', help='Append to the output file if it exists.', default=False, action='store_true')
parser.add_argument('-v', '--verbose', dest='verbose', help='Display progress and related status information while parsing input files.', default=False, action='store_true')
args = parser.parse_args()

if args.infile == None:
    sys.stderr.write('ERROR: No input file or root directory specified.\n')
    sys.exit(2)

if args.outfile == None:
    sys.stderr.write('ERROR: No output file specified.\n')
    sys.exit(2)
elif not args.outfile.startswith(default_destdir) and not args.force_outfile:
    sys.stderr.write('ERROR: Output file is not in %s, which is the SOF-ELK ingest location. Use "-f" to force creating a file in this location.\n' % (default_destdir))
    sys.exit(2)
elif not args.outfile.endswith('.json'):
    sys.stderr.write('ERROR: Output file does not end with ".json".  SOF-ELK requires this extension to process these logs.  Exiting.\n')
    sys.exit(2)

input_files= []
if os.path.isfile(args.infile):
    input_files.append(args.infile)
elif os.path.isdir(args.infile):
    for root, dirs, files in os.walk(args.infile):
        for name in files:
            input_files.append(os.path.join(root, name))
else:
    sys.stderr.write('No input files could be processed.  Exiting.\n')
    sys.exit(4)

if args.verbose:
    print('Found %d files to parse.' % (len(input_files)))
    print()

if os.path.isfile(args.outfile) and args.append == True:
    outfh = open(args.outfile, 'a')
if os.path.isfile(args.outfile) and args.append == False:
    sys.stderr.write('ERROR: Output file %s already exists. Use "-a" to append to the file at this location or specify a different filename.\n' % (args.outfile))
    sys.exit(3)
else:
    outfh = open(args.outfile, 'w')

for infile in input_files:
    if args.verbose:
        print('- Parsing file: %s' % (infile))
    process_cloudtrail_file(infile, outfh)

print('Output complete.')
if not args.outfile.startswith(default_destdir):
    print('You must move/copy the generated file to the %s directory before SOF-ELK can process it.' % (default_destdir))
else:
    print('SOF-ELK should now be processing the generated file - check system load and the Kibana interface to confirm.')
