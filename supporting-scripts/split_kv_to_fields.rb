# SOF-ELK® Supporting script
# (C)2026 Lewes Technology Consulting, LLC
#
# This script takes an array of "name: x, value: y" pairs and creates "x: y" fields
# for example:
# - source: [{"Name":"Identity","Value":"jvandyne"}]
# - result: [{"Identity":"jvandyne"}]

# the value of `params` is the value of the hash passed to `script_params`
# in the logstash configuration
def register(params)
  @source_field = params.fetch("source_field")
  @destination_field = params.fetch("destination_field")
  @key_field = params.fetch("key_field")
  @val_field = params.fetch("val_field")
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
  output = {}

  if source_data.is_a?(Array)
    source_data.each do |item|
      if item.key?(@val_field) && !(item[@val_field] == "")
        output[item[@key_field]] = item[@val_field]
      end
    end

  elsif source_data.is_a?(Hash)
    item = source_data
    if item.key?(@val_field) && !(item[@val_field] == "")
      output[item[@key_field]] = item[@val_field]
    end

  else
    event.tag("#{@source_field}_unexpected_type")
    return [event]
  end

  event.set(@destination_field, output)
  return [event]
end

## Validation tests
test "single entry in source (hash)" do
  parameters {{ "source_field" => "source", "destination_field" => "dest", "key_field" => "name", "val_field" => "value" }}
  in_event {{ "source" => { "name" => "identity", "value" => "jvandyne" } }}
  expect ("the source element is restructured") { |events|
    events.first.get("[dest][identity]") == "jvandyne"
  }
end

test "single entry in source (array)" do
  parameters {{ "source_field" => "source", "destination_field" => "dest", "key_field" => "name", "val_field" => "value" }}
  in_event {{ "source" => [{ "name" => "identity", "value" => "jvandyne" }] }}
  expect ("the source element is restructured") { |events|
    events.first.get("[dest][identity]") == "jvandyne"
  }
end

test "multiple entries in source (array)" do
  parameters {{ "source_field" => "source", "destination_field" => "dest", "key_field" => "name", "val_field" => "value" }}
  in_event {{ "source" => [{ "name" => "identity", "value" => "jvandyne" }, { "name" => "color", "value" => "red" }] }}
  expect ("the source element is restructured") { |events|
    events.first.get("[dest][identity]") == "jvandyne" &&
    events.first.get("[dest][color]") == "red"
  }
end

test "nonexistent source field" do
  parameters {{ "source_field" => "source", "destination_field" => "dest", "key_field" => "name", "val_field" => "value" }}
  in_event {{ "source2" => [{ "name" => "identity", "value" => "jvandyne" }] }}
  expect ("the event is tagged"){ |events|
    events.first.get("tags")&.include?("source_not_found")
  }
end
