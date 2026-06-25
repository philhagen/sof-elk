# SOF-ELK® Supporting script
# (C)2026 Lewes Technology Consulting, LLC
#
# This script uses the TCP flags field (as an array of words, string of letters,
#   or integer) and calculates the missing values, overwriting or adding fields
#   (array of words, integer, and hex value) as needed

# the value of `params` is the value of the hash passed to `script_params`
# in the logstash configuration
def register(params)
  @source_field = params.fetch("source_field")
  @source_type = params.fetch("source_type")
end

# the filter method receives an event and must return a list of events.
# Dropping an event means not including it in the return array,
# while creating new ones only requires you to add a new instance of
# LogStash::Event to the returned array
def filter(event)
  if event.get(@source_field) == nil
    return [event]
  end

  derived_source_type = nil

  if @source_type == "int"
    tcp_flags_int_new = event.get(@source_field).to_i

  elsif @source_type == "arr"
    # get source array
    tcp_flags = event.get(@source_field)

    # build a string
    tcp_flags_str = ""
    tcp_flags.each { |flag| tcp_flags_str += "#{flag[0].upcase}" }

    # treat the derived string as such for the rest of the process
    derived_source_type = "str"

  elsif @source_type == "str"
    # get source string
    tcp_flags_str = event.get(@source_field).upcase
  end

  if @source_type == "str" || derived_source_type == "str"
    # calculate the integer value
    tcp_flags_int_new = 0
    tcp_flags_int_new += 1 if tcp_flags_str.include?("F")
    tcp_flags_int_new += 2 if tcp_flags_str.include?("S")
    tcp_flags_int_new += 4 if tcp_flags_str.include?("R")
    tcp_flags_int_new += 8 if tcp_flags_str.include?("P")
    tcp_flags_int_new += 16 if tcp_flags_str.include?("A")
    tcp_flags_int_new += 32 if tcp_flags_str.include?("U")
    tcp_flags_int_new += 64 if tcp_flags_str.include?("E")
    tcp_flags_int_new += 128 if tcp_flags_str.include?("C")
  end

  # Create array based on values in the bitmask
  tcp_flags_new = []
  tcp_flags_new.push("cwr") if (tcp_flags_int_new & 0x80 != 0)
  tcp_flags_new.push("ece") if (tcp_flags_int_new & 0x40 != 0)
  tcp_flags_new.push("urg") if (tcp_flags_int_new & 0x20 != 0)
  tcp_flags_new.push("ack") if (tcp_flags_int_new & 0x10 != 0)
  tcp_flags_new.push("psh") if (tcp_flags_int_new & 0x08 != 0)
  tcp_flags_new.push("rst") if (tcp_flags_int_new & 0x04 != 0)
  tcp_flags_new.push("syn") if (tcp_flags_int_new & 0x02 != 0)
  tcp_flags_new.push("fin") if (tcp_flags_int_new & 0x01 != 0)

  # set the field for the array
  event.remove("[network][tcp_flags]")
  event.set("[network][tcp_flags]", tcp_flags_new)

  # set the field for the integer
  event.remove("[netflow][tcp_control_bits]")
  event.set("[netflow][tcp_control_bits]", tcp_flags_int_new)

  # set the field for the hex version
  event.remove("[network][tcp_flags_hex]")
  event.set("[network][tcp_flags_hex]", "0x" + tcp_flags_int_new.to_s(16).rjust(2, '0').upcase)

  return [event]
end

## Validation tests
test "no flags in string" do
  parameters {{ "source_field" => "flags", "source_type" => "str" }}
  in_event {{ "flags" => "........" }}
  expect("empty output array, and zero for integer, 0x00 for hex string") { |events|
    events.first.get("[network][tcp_flags]") == [] &&
    events.first.get("[netflow][tcp_control_bits]") == 0 &&
    events.first.get("[network][tcp_flags_hex]") == "0x00"
  }
end

test "no flags in integer" do
  parameters {{ "source_field" => "flags", "source_type" => "int" }}
  in_event {{ "flags" => 0 }}
  expect("empty output array, and zero for integer, 0x00 for hex string") { |events|
    events.first.get("[network][tcp_flags]") == [] &&
    events.first.get("[netflow][tcp_control_bits]") == 0 &&
    events.first.get("[network][tcp_flags_hex]") == "0x00"
  }
end

test "no flags in array" do
  parameters {{ "source_field" => "flags", "source_type" => "arr" }}
  in_event {{ "flags" => [] }}
  expect("empty output array, and zero for integer, 0x00 for hex string") { |events|
    events.first.get("[network][tcp_flags]") == [] &&
    events.first.get("[netflow][tcp_control_bits]") == 0 &&
    events.first.get("[network][tcp_flags_hex]") == "0x00"
  }
end

test "all flags in string" do
  parameters {{ "source_field" => "flags", "source_type" => "str" }}
  in_event {{ "flags" => "cEuAprsF" }}
  expect("full output array, 255 for integer, and 0xFF for hex string") { |events|
    events.first.get("[network][tcp_flags]").sort == [ "cwr", "ece", "urg", "ack", "psh", "rst", "syn", "fin" ].sort &&
    events.first.get("[netflow][tcp_control_bits]") == 255 &&
    events.first.get("[network][tcp_flags_hex]") == "0xFF"
  }
end

test "all flags in integer" do
  parameters {{ "source_field" => "flags", "source_type" => "int" }}
  in_event {{ "flags" => 255 }}
  expect("full output array, 255 for integer, and 0xFF for hex string") { |events|
    events.first.get("[network][tcp_flags]").sort == [ "cwr", "ece", "urg", "ack", "psh", "rst", "syn", "fin" ].sort &&
    events.first.get("[netflow][tcp_control_bits]") == 255 &&
    events.first.get("[network][tcp_flags_hex]") == "0xFF"
  }
end

test "all flags in array (strings)" do
  parameters {{ "source_field" => "flags", "source_type" => "arr" }}
  in_event {{ "flags" => [ "cwr", "ece", "urg", "ack", "psh", "rst", "syn", "fin" ] }}
  expect("full output array, 255 for integer, and 0xFF for hex string") { |events|
    events.first.get("[network][tcp_flags]").sort == [ "cwr", "ece", "urg", "ack", "psh", "rst", "syn", "fin" ].sort &&
    events.first.get("[netflow][tcp_control_bits]") == 255 &&
    events.first.get("[network][tcp_flags_hex]") == "0xFF"
  }
end

test "all flags in array (letters)" do
  parameters {{ "source_field" => "flags", "source_type" => "arr" }}
  in_event {{ "flags" => [ "C", "E", "U", "A", "P", "R", "S", "F" ] }}
  expect("full output array, 255 for integer, and 0xFF for hex string") { |events|
    events.first.get("[network][tcp_flags]").sort == [ "cwr", "ece", "urg", "ack", "psh", "rst", "syn", "fin" ].sort &&
    events.first.get("[netflow][tcp_control_bits]") == 255 &&
    events.first.get("[network][tcp_flags_hex]") == "0xFF"
  }
end

test "some flags in string" do
  parameters {{ "source_field" => "flags", "source_type" => "str" }}
  in_event {{ "flags" => "...AP.SF" }}
  expect("proper output array, 27 for integer, and 0x1B for hex string") { |events|
    events.first.get("[network][tcp_flags]").sort == [ "ack", "fin", "psh", "syn" ].sort &&
    events.first.get("[netflow][tcp_control_bits]") == 27 &&
    events.first.get("[network][tcp_flags_hex]") == "0x1B"
  }
end

test "some flags in integer" do
  parameters {{ "source_field" => "flags", "source_type" => "int" }}
  in_event {{ "flags" => 197 }}
  expect("proper output array, 197 for integer, and 0xC5 for hex string") { |events|
    events.first.get("[network][tcp_flags]").sort == [ "cwr", "ece", "fin", "rst" ].sort &&
    events.first.get("[netflow][tcp_control_bits]") == 197 &&
    events.first.get("[network][tcp_flags_hex]") == "0xC5"
  }
end

test "some flags in array (strings)" do
  parameters {{ "source_field" => "flags", "source_type" => "arr" }}
  in_event {{ "flags" => [ "ack", "psh", "urg", "rst" ] }}
  expect("the event includes no flags in any resulting fields") { |events|
    events.first.get("[network][tcp_flags]").sort == [ "ack", "psh", "urg", "rst" ].sort &&
    events.first.get("[netflow][tcp_control_bits]") == 60 &&
    events.first.get("[network][tcp_flags_hex]") == "0x3C"
  }
end

test "some flags in array (letters)" do
  parameters {{ "source_field" => "flags", "source_type" => "arr" }}
  in_event {{ "flags" => ["E","A","R","S"] }}
  expect("proper output array, 86 for integer, and 0x56 for hex string") { |events|
    events.first.get("[network][tcp_flags]").sort == [ "ack", "ece", "rst", "syn" ].sort &&
    events.first.get("[netflow][tcp_control_bits]") == 86 &&
    events.first.get("[network][tcp_flags_hex]") == "0x56"
  }
end

test "nonexistent source field" do
  parameters {{ "source_field" => "flags", "source_type" => "str" }}
  in_event {{ "flags2" => "......S." }}
  expect("the event should be returned unchanged") { |events|
    events.first.get("flags2") == "......S." &&
    events.first.get("[network][tcp_flags]") == nil &&
    events.first.get("[netflow][tcp_control_bits]") == nil &&
    events.first.get("[network][tcp_flags_hex]") == nil
  }
end
