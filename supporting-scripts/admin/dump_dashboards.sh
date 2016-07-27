TYPES="dashboard visualization search index-pattern"
mkdir -p $TYPES

for TYPE in `echo $TYPES`; do
  curl -s -XGET "http://localhost:9200/.kibana/_search?type=$TYPE&size=50" | jq '.' | grep \"_id\" | \
    while read TITLE; do
      ID=`echo $TITLE | awk -F: '{ print $2 }' | sed 's?[", ]??g'`
      curl -s -XGET "http://localhost:9200/.kibana/$TYPE/$ID" | jq "._source"> $TYPE/$ID
    done
done
if [ -n "$TYPES" ]; then
  tar cfz objects.tgz $TYPES
  rm -rf $TYPES
fi
