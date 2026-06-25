# SOF-ELK® Supporting script
# (C)2026 Lewes Technology Consulting, LLC
#
# This script will convert a string with a hex representation of a number to
# its integer value, overwriting the source

# the value of `params` is the value of the hash passed to `script_params`
# in the logstash configuration
def register(params)
  @source_field = params.fetch("source_field")
end

# the filter method receives an event and must return a list of events.
# Dropping an event means not including it in the return array,
# while creating new ones only requires you to add a new instance of
# LogStash::Event to the returned array
def filter(event)
  hex_string = event.get(@source_field)

  # field doesn't exist or it's already an integer, return an unchanged event
  if hex_string.nil? || hex_string.is_a?(Integer)
    return [event]
  end
  
  # invalid hex input or 0xZZ
  if (hex_string.start_with?("0x") && !hex_string[2..].match?(/\A\h+\z/)) || (!hex_string.start_with?("0x") && !hex_string.match?(/\A\h+\z/))
    event.tag("_hex_to_integer_fail")
    return [event]

  # bare hex like ff
  elsif !hex_string.start_with?("0x") && hex_string[/\h/]
    hex_string = "0x" + hex_string
  end

  event.set(@source_field, Integer(hex_string, 16))

  return [event]
end

### Validation tests
test "lowercase hex (no 0x prefix) to integer" do
  parameters {{ "source_field" => "hex1" }}
  in_event {{ "hex1" => "1a" }}
  expect("the hex value is converted to an integer") { |events|
    events.first.get("hex1") == 26
  }
end

test "lowercase hex (with 0x prefix) to integer" do
  parameters {{ "source_field" => "hex2" }}
  in_event {{ "hex2" => "0x1a" }}
  expect("the hex value is converted to an integer") { |events|
      events.first.get("hex2") == 26
  }
end

test "uppercase hex (no 0x prefix) to integer" do
  parameters {{ "source_field" => "hex3" }}
  in_event {{ "hex3" => "FF" }}
  expect("the hex value is converted to an integer") { |events|
      events.first.get("hex3") == 255
  }
end

test "uppercase hex (with 0x prefix) to integer" do
  parameters {{ "source_field" => "hex4" }}
  in_event {{ "hex4" => "0xFF" }}
  expect("the hex value is converted to an integer") { |events|
    events.first.get("hex4") == 255
  }
end

test "mixed case hex (no 0x prefix) to integer" do
  parameters {{ "source_field" => "hex5" }}
  in_event {{ "hex5" => "4aF2" }}
  expect("the hex value is converted to an integer") { |events|
    events.first.get("hex5") == 19186
  }
end

test "mixed case hex (with 0x prefix) to integer" do
  parameters {{ "source_field" => "hex6" }}
  in_event {{ "hex6" => "0x4Db3" }}
  expect("the hex value is converted to an integer") { |events|
    events.first.get("hex6") == 19891
  }
end

test "nil in source field" do
  parameters {{ "source_field" => "hex7" }}
  in_event {{ "hex7" => nil, "other_field" => "test" }}
  expect("source field is nil so object should be returned unchanged") { |events|
      events.first.get("tags").nil? && events.first.get("hex7").nil? && events.first.get("other_field") == "test"
  }
end

test "invalid hex string" do
  parameters {{ "source_field" => "hex8" }}
  in_event {{ "hex8" => "ZZZ" }}
  expect("the hex cannot be converted but the event is tagged") { |events|
    events.first.get("tags")&.include?("_hex_to_integer_fail")
  }
end

test "numeric value in source field" do
  parameters {{ "source_field" => "hex9" }}
  in_event {{ "hex9" => 123 }}
  expect("the event should be returned unchanged") { |events|
    events.first.get("hex9") == 123
  }
end

test "nonexistent source field" do
  parameters {{ "source_field" => "hex10" }}
  in_event {{ "hex10b" => "aa" }}
  expect("the event should be returned unchanged") { |events|
    events.first.get("hex10b") == "aa"
  }
end
