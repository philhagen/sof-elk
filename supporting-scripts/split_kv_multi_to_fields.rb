# SOF-ELK® Supporting script
# (C)2025 Lewes Technology Consulting, LLC
#
# This script takes an array of hashes like "{ name: x, value1: y, value2: z }" elements and creates "x: { y, z }" fields
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

## Validation tests

test "single entry in source" do
    parameters {{ "source_field" => "source", "destination_field" => "dest", "key_field" => "name" }}
    in_event {{ "source" => [{ "name": "identity", "value1": "jvandyne", "value2": "orange" }] }}
    expect ("the source element is restructured") { |events|
        events.first.get("[dest][identity][value1]") == "jvandyne" &&
        events.first.get("[dest][identity][value2]") == "orange"
    }
end

test "single value in source" do
    parameters {{ "source_field" => "source", "destination_field" => "dest", "key_field" => "name" }}
    in_event {{ "source" => [{ "name": "identity", "value1": "jvandyne" }] }}
    expect ("the source element is restructured") { |events|
        events.first.get("[dest][identity][value1]") == "jvandyne"
    }
end

test "multiple items in source array" do
    parameters {{ "source_field" => "source", "destination_field" => "dest", "key_field" => "name" }}
    in_event {{ "source" => [{ "name": "identity", "value1": "jvandyne", "value2": "orange" }, { "name": "alert_data", "level": "debug", "message": "this is a test" }] }}
    expect ("the source element is restructured") { |events|
        events.first.get("[dest][identity][value1]") == "jvandyne" &&
        events.first.get("[dest][identity][value2]") == "orange" &&
        events.first.get("[dest][alert_data][level]") == "debug" &&
        events.first.get("[dest][alert_data][message]") == "this is a test"
    }
end

test "nonexistent source field" do
    parameters {{ "source_field" => "source", "destination_field" => "dest", "key_field" => "name" }}
    in_event {{ "source2" => [{ "name": "identity", "value1": "jvandyne", "value2": "orange" }] }}
    expect ("the event is tagged") { |events|
        events.first.get("tags")&.include?("source_not_found")
    }
end
