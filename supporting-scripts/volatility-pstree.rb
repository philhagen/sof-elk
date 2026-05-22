# SOF-ELK® Supporting script
# (C)2026 Lewes Technology Consulting, LLC
#
# This script processes a volatility 3  "pstree" object and recursively structures all child processes into a flat set of results with a process depth field applied

def register(params)
  @source_field = params.fetch("source", "[message]")

  @target_field = params.fetch("target", "[processes]")
end

def filter(event, depth = 0)
  # Tag and quit if source field isn't present
  if event.get("#{@source_field}").nil?
    event.tag("#{source_field}_not_found")
    return [event]
  end

  output = []

  # Retrieve the source
  source = event.get("#{@source_field}")

  source['process_depth'] = depth

  if source['__children'].is_a?(Array) && source['__children'].length > 0
    source['__children'].each do |child_process|
      output << filter(child_process, depth + 1)
    end

  elsif source['__children'].length == 0
    event.delete('__children')
    output << event
  end

  if depth > 0
    return output

  elsif depth == 0
    event.set("#{@target_field}", output)
    return [event]
  end
end

### Validation Tests
test "when no child processes" do
  parameters {{ "source" => "raw", "target" => "output" }}
  in_event {{ "raw" => { "Audit" => nil, "Cmd" => nil, "PID" => 4, "__children" => [] } }}
  expect("event is returned without __children") { |events|
    events.first.get("output") == '[ { "Audit" => nil, "Cmd" => nil, "PID" => 4 } ]'
  }
end

test "when one child process" do
  parameters {{ "source" => "raw", "target" => "output" }}
  in_event {{ "raw" => { "Audit" => nil, "Cmd" => nil, "PID" => 4, "__children" => [ { "Audit" => "MemCompression", "Cmd" => "MemCompression", "PID" => 1816, "__children" => [] } ] } }}
  expect("events are returned flat, without __children") { |events|
    events.get("output") == '[ { "Audit" => nil, "Cmd" => nil, "PID" => 4 }, { "Audit" => "MemCompression", "Cmd" => "MemCompression", "PID" => 1816 } ]'
  }
end

test "when multiple child processes at same level" do
  parameters {{ "source" => "raw", "target" => "output" }}
  in_event {{ "raw" => { "Audit" => nil, "Cmd" => nil, "PID" => 4, "__children" => [ { "Audit" => "MemCompression", "Cmd" => "MemCompression", "PID" => 1816, "__children" => [] }, { "Audit" => "Registry", "Cmd" => "Registry", "PID" => 92, "__children" => [] } ] } }}
  expect("events are returned flat, without __children") { |events|
    events.get("output") == '[ { "Audit" => nil, "Cmd" => nil, "PID" => 4 }, { "Audit" => "MemCompression", "Cmd" => "MemCompression", "PID" => 1816 } ]'
  }
end

test "when multiple child processes at different levels" do
  parameters {{ "source" => "raw", "target" => "output" }}
  in_event {{ "raw" => { "Audit" => nil, "Cmd" => nil, "PID" => 4, "__children" => [ { "Audit" => "MemCompression", "Cmd" => "MemCompression", "PID" => 1816, "__children" => [ { "Audit" => "Registry", "Cmd" => "Registry", "PID" => 92, "__children" => [] } ] }, { "Audit" => "\\Device\\HarddiskVolume3\\Windows\\System32\\RuntimeBroker.exe", "Cmd" => "C:\\Windows\\System32\\RuntimeBroker.exe -Embedding", "PID" => 7852, "__children" => [] } ] } }}
  expect("events are returned flat, without __children") { |events|
    events.get("output") == '[ { "Audit" => nil, "Cmd" => nil, "PID" => 4 }, { "Audit" => "MemCompression", "Cmd" => "MemCompression", "PID" => 1816 }, "Audit" => "\\Device\\HarddiskVolume3\\Windows\\System32\\RuntimeBroker.exe", "Cmd": "C:\\Windows\\System32\\RuntimeBroker.exe -Embedding", "PID" => 7852 ]'
  }
end

test "when source field does not exist" do
  parameters {{ "source" => "raw2", "target" => "output" }}
  in_event {{ "raw" => { "Audit" => nil, "Cmd" => nil, "PID" => 4, "__children" => [] } }}
  expect("tags as not found") { |events|
    events.get("tags").include?("raw2_not_found")
  }
end
