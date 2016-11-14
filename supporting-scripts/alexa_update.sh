#!/bin/bash
cd /tmp
/usr/bin/wget http://s3.amazonaws.com/alexa-static/top-1m.csv.zip
<<<<<<< HEAD
/usr/bin/unzip -o top-1m.csv.zip -d /lib/logstash_data
rm /tmp/top-1m.csv.zip
sleep 60
DATE=`date -u +%Y.%m.%d`
DATE2=`date -u +%Y.%m.%d -d "1 day ago"`
DATE3=`date -u +%Y.%m.%d -d "2 day ago"`
DATE4=`date -u +%Y.%m.%d -d "3 day ago"`
curl -XPOST 'http://localhost:9200/_aliases' -d '
=======
mkdir /lib/logstash_data
/usr/bin/unzip -o top-1m.csv.zip -d /lib/logstash_data
rm /tmp/top-1m.csv.zip
sleep 60
curl -XPOST 'http://es01.test.int:9200/_aliases' -d '
>>>>>>> origin/master
{
    "actions" : [
        { "add" : { "index" : "logstash-alexa-'$DATE'", "alias" : "alexa" } }
    ]
}'
curl -XPOST 'http://localhost:9200/_aliases' -d '
{
    "actions" : [
        { "remove" : { "index" : "logstash-alexa-'$DATE2'", "alias" : "alexa" } }
    ]
}'
curl -XPOST 'http://localhost:9200/_aliases' -d '
{
    "actions" : [
        { "remove" : { "index" : "logstash-alexa-'$DATE3'", "alias" : "alexa" } }
    ]
}'
curl -XPOST 'http://localhost:9200/_aliases' -d '
{
    "actions" : [
        { "remove" : { "index" : "logstash-alexa-'$DATE4'", "alias" : "alexa" } }
    ]
}'
curl -XDELETE "http://localhost:9200/logstash-alexa-$DATE2"
curl -XDELETE "http://localhost:9200/logstash-alexa-$DATE3"
curl -XDELETE "http://localhost:9200/logstash-alexa-$DATE4"