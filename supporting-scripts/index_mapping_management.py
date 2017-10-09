#!/usr/bin/python
# SOF-ELK® Supporting script
# (C)2017 Lewes Technology Consulting, LLC
#
# This script will dump or load Kibana mappings to/from files

import json
from collections import OrderedDict
import argparse
import urllib
import requests
import os.path

parser = argparse.ArgumentParser(description='Dump or load Kibana index-mappings to/from files')
parser.add_argument('--dump', dest='mode', action='store_const', const='dump', default='dump', help='Dump values from Elasticsearch to a file. (Default)')
parser.add_argument('--load', dest='mode', action='store_const', const='load', default='load', help='Load value from file to Elasticsearch')
parser.add_argument('-f', '--file', dest='file', required=True, help='File to load from or write to')
parser.add_argument('-i', '--index', dest='index', required=True, help='Index to use.  ("-*" is appended, so "-i logstash" will address the "logstash-*" indices)')
args = parser.parse_args()

kibana_url = 'http://127.0.0.1:9200/.kibana/index-pattern/%s-*' % (args.index)

if args.mode == 'dump':
    # TODO : re-do this with requests
    es_fh = urllib.urlopen(kibana_url)
    source_data = es_fh.read()
    es_fh.close()
    source_obj = json.loads(source_data)
    fields = source_obj['_source']['fields']

    field_dict_list = sorted(json.loads(fields), key=lambda k: k['name'])

    new_field_list = []
    new_field_filecontent = []

    for field_dict in field_dict_list:
        new_field_dict = OrderedDict()
        for key in ['name', 'type', 'count', 'scripted', 'indexed', 'analyzed', 'doc_values']:
            new_field_dict[key] = field_dict[key]
            field_dict.pop(key, None)

        for key in field_dict.keys():
            new_field_dict[key] = field_dict[key]

        new_field_list.append(new_field_dict)
        new_field_filecontent.append(json.dumps(new_field_dict))

    save_fh = open(args.file, 'w')
    save_fh.write('\n'.join(new_field_filecontent))
    save_fh.close()

    if 'fieldFormatMap' in source_obj['_source']:
        format_string = source_obj['_source']['fieldFormatMap']

        format_save_fh = open('%s.format' % (args.file), 'w')
        format_save_fh.write(format_string)
        format_save_fh.close()

elif args.mode == 'load':
    new_mapping = OrderedDict()
    new_mapping['title'] = args.index + '-*'
    new_mapping['timeFieldName'] = '@timestamp'

    load_fh = open(args.file, 'r')
    field_list = load_fh.read().splitlines()
    load_fh.close()

    new_mapping['fields'] = '[%s]' % (','.join(field_list))

    if os.path.isfile('%s.format' % (args.file)):
        format_load_fh = open('%s.format' % (args.file), 'r')
        format_string = format_load_fh.read()
        format_load_fh.close()

        new_mapping['fieldFormatMap'] = format_string

    mapping_load = requests.put(kibana_url, data=json.dumps(new_mapping))
    #print mapping_load.status_code
