#!/usr/bin/env python2
# SOF-ELK(R) Supporting script
# (C)2018 Lewes Technology Consulting, LLC
#
# This script will dump or load Kibana mappings to/from files
# https://github.com/elastic/kibana/issues/3709 was helpful figuring this functionality out

import json
from collections import OrderedDict
import argparse
import requests
import os.path

parser = argparse.ArgumentParser(description='Dump or load Kibana index-mappings to/from files')
parser.add_argument('--dump', dest='mode', action='store_const', const='dump', default='dump', help='Dump values from Elasticsearch to a file. (Default)')
parser.add_argument('--load', dest='mode', action='store_const', const='load', default='load', help='Load value from file to Elasticsearch')
parser.add_argument('-f', '--file', dest='file', required=True, help='File to load from or write to')
parser.add_argument('-i', '--index', dest='index', required=True, help='Index to use.  ("-*" is appended, so "-i logstash" will address the "logstash-*" indices)')
args = parser.parse_args()

kibana_url = 'http://127.0.0.1:5601/api/saved_objects/index-pattern/%s' % (args.index)
httpheaders = { 'kbn-xsrf': 'sof-elk' }

if args.mode == 'dump':
    mapping_dump = requests.get(kibana_url, headers=httpheaders)
    source_obj = json.loads(mapping_dump.text)
    fields = source_obj['attributes']['fields']

    field_dict_list = sorted(json.loads(fields), key=lambda k: k['name'])

    new_field_list = []
    new_field_filecontent = []

    for field_dict in field_dict_list:
        new_field_dict = OrderedDict()
        for key in ['name', 'type', 'count', 'scripted', 'searchable', 'aggregatable', 'readFromDocValues']:
            new_field_dict[key] = field_dict[key]
            field_dict.pop(key, None)

        for key in field_dict.keys():
            new_field_dict[key] = field_dict[key]

        new_field_list.append(new_field_dict)
        new_field_filecontent.append(json.dumps(new_field_dict))

    save_fh = open(args.file, 'w')
    save_fh.write('\n'.join(new_field_filecontent))
    save_fh.close()

    if 'fieldFormatMap' in source_obj['attributes'].keys():
        format_string = source_obj['attributes']['fieldFormatMap']

        format_save_fh = open('%s.format' % (args.file), 'w')
        format_save_fh.write(format_string)
        format_save_fh.close()

elif args.mode == 'load':
    load_fh = open(args.file, 'r')
    field_list = load_fh.read().splitlines()
    load_fh.close()

    new_mapping = OrderedDict()
    new_mapping['attributes'] = {}
    new_mapping['attributes']['fields'] = '[%s]' % (',\n'.join(field_list))
    new_mapping['attributes']['timeFieldName'] = '@timestamp'
    new_mapping['attributes']['title'] = args.index + '-*'

    if os.path.isfile('%s.format' % (args.file)):
        format_load_fh = open('%s.format' % (args.file), 'r')
        format_string = format_load_fh.read()
        format_load_fh.close()

        new_mapping['attributes']['fieldFormatMap'] = format_string

    mapping_load = requests.post(kibana_url + '?overwrite=true', data=json.dumps(new_mapping), headers=httpheaders)
    #print mapping_load.status_code
