# SOF-ELK® Supporting script
# (C)2022 Lewes Technology Consulting, LLC
#
# This script takes an array of "name: x, value: y" pairs and creates "x: y" fields
# for example:
# - source: [{"Name":"Identity","Value":"jvandyne"}]
# - result: [{"Identity":"jvandyne"}]

# the value of `params` is the value of the hash passed to `script_params`
# in the logstash configuration
def register(params)
    @source_field = params["source_field"]
    @destination_field = params["destination_field"]
    @key_field = params["key_field"]
    @val_field = params["val_field"]
end

# the filter method receives an event and must return a list of events.
# Dropping an event means not including it in the return array,
# while creating new ones only requires you to add a new instance of
# LogStash::Event to the returned array
def filter(event)
    # if source field is not present
    if event.get(@source_field).nil?
        event.tag("#{@source_field}_not_found")
        return [event]
    end
    source_array = event.get(@source_field)

    # create empty hash to hold new result
    output = Hash.new()

    for item in source_array
        if item.key?(@val_field) and item.key?(@val_field).length > 0
            output[item[@key_field]] = item[@val_field]
        end
    end

    event.set(@destination_field, output)

    return [event]
end
