#!/bin/bash
# SOF-ELK® Supporting script
# (C)2021 Lewes Technology Consulting, LLC
#
# This script fixes the elasticsearch jvm.options file to maximize use of available RAM

# location for overrides changed in ES 7.9
es_version=$( rpm -q --queryformat '%{VERSION}' elasticsearch )
rpmdev-vercmp 7.9 ${es_version} > /dev/null
es_vercmp_result=$?
if [ ${es_vercmp_result} -eq 11 ]; then
    jvm_options_file="/etc/elasticsearch/jvm.options"
else
    jvm_options_file="/etc/elasticsearch/jvm.options.d/sof-elk"
fi

ES_HEAP_MAX=31000

TMPFILE=$( mktemp )
chmod 644 $TMPFILE
if [ -f ${jvm_options_file} ]; then
    grep -v ^-Xm[sx] ${jvm_options_file} > $TMPFILE
fi

ES_HEAP_SIZE=$( echo \( $( free -m | grep Mem|awk '{print $2}' ) - 1536 \) / 2 | bc )
if [[ $ES_HEAP_SIZE -gt $ES_HEAP_MAX ]]; then
    ES_HEAP_SIZE=$ES_HEAP_MAX
fi

echo "-Xms${ES_HEAP_SIZE}m" >> $TMPFILE
echo "-Xmx${ES_HEAP_SIZE}m" >> $TMPFILE

cat $TMPFILE > ${jvm_options_file}
rm -f $TMPFILE
