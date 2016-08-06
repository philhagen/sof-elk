#!/bin/bash

ES_HEAP_MAX=31000

TMPFILE=$( mktemp )
chmod 644 $TMPFILE
grep -v ^ES_HEAP_SIZE /etc/sysconfig/elasticsearch > $TMPFILE

ES_HEAP_SIZE=$( echo \( $( free -m | grep Mem|awk '{print $2}' ) - 1024 \) / 2 | bc )
if [[ $ES_HEAP_SIZE -gt $ES_HEAP_MAX ]]; then
    ES_HEAP_SIZE=$ES_HEAP_MAX
fi

echo "ES_HEAP_SIZE=${ES_HEAP_SIZE}m" >> $TMPFILE
cat $TMPFILE > /etc/sysconfig/elasticsearch
rm -f $TMPFILE