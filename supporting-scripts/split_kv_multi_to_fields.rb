# SOF-ELK® Supporting script
# (C)2021 Lewes Technology Consulting, LLC
#
# This script takes a hash of "{ name: x, value1: y, value2: z }" elements and creates "x: { y, z }" fields
# for example:
# - source: [{"Name":"Identity","Value1":"jvandyne","Value2":"admin"}]
# - result: [{"Identity":{"Value1":"jvandyne","Value2":"admin"}]

# the value of `params` is the value of the hash passed to `script_params`
# in the logstash configuration
def register(params)
    @source_field = params["source_field"]
    @destination_field = params["destination_field"]
    @key_field = params["key_field"]
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
    source_data = event.get(@source_field)

    # create empty hash to hold new result
    output = Hash.new()

    for item in source_data
        new_value = Marshal.load(Marshal.dump(item))
        key = new_value.delete(@key_field)

        output[key] = new_value
    end

    event.set(@destination_field, output)

    return [event]
end