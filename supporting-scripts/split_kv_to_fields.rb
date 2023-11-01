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
    source_data = event.get(@source_field)

    # create empty hash to hold new result
    output = Hash.new()

    if source_data.is_a?(Array)
        for item in source_data
            if item.key?(@val_field) && !(item[@val_field] == "")
                output[item[@key_field]] = item[@val_field]
            end
        end

    elsif source_data.is_a?(Hash)
        item = source_data
        if item.key?(@val_field) && !(item[@val_field] == "")
            output[item[@key_field]] = item[@val_field]
        end
    
    # PJH: This should probably have a final "else" stanza to raise an exception
    #      if the source is not a hash or an array of hashes
    end

    event.set(@destination_field, output)

    return [event]
end
