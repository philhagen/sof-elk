#!/bin/bash

ES_HEAP_MAX=31000

TMPFILE=$( mktemp )
chmod 644 $TMPFILE
grep -v ^-Xm[sx] /etc/elasticsearch/jvm.options > $TMPFILE

ES_HEAP_SIZE=$( echo \( $( free -m | grep Mem|awk '{print $2}' ) - 1536 \) / 2 | bc )
if [[ $ES_HEAP_SIZE -gt $ES_HEAP_MAX ]]; then
    ES_HEAP_SIZE=$ES_HEAP_MAX
fi

echo "-Xms${ES_HEAP_SIZE}m" >> $TMPFILE
echo "-Xmx${ES_HEAP_SIZE}m" >> $TMPFILE

cat $TMPFILE > /etc/elasticsearch/jvm.options
rm -f $TMPFILE
