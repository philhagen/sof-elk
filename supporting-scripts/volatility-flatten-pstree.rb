# SOF-ELK® Supporting script
# (C)2026 Lewes Technology Consulting, LLC
#
# This script processes a volatility 3 "pstree" object and recursively structures all child processes into a flat set of results with a process depth field applied

def register(params)
  @source_field = params.fetch("source", "[message]")
  @target_field = params.fetch("target", "[processes]")
end

def handle(process, depth = 0)
  result = []

  process['process_depth'] = depth

  if process['__children'].is_a?(Array) && process['__children'].length > 0
    children = process.delete('__children')
    result << process
    children.each do |child_process|
      result += handle(child_process, depth+1)
    end
  else
    # this occurs when there is no __children or __children==[]
    process.delete('__children')
    result << process
  end

  return result
end

def filter(event)
  # Tag and quit if source field isn't present
  if event.get("#{@source_field}").nil?
    event.tag("#{@source_field}_not_found")
    return [event]
  end

  # Retrieve the source
  source = event.get("#{@source_field}")

  flatlist = handle(source)

  event.set("#{@target_field}", flatlist)
  return [event]
end

### Validation Tests
test "when no child processes" do
  parameters {{ "source" => "raw", "target" => "output" }}
  in_event {{ "raw" => { "Audit" => nil, "Cmd" => nil, "PID" => 4, "__children" => [] } }}

  expect("event is returned without __children") do |events|
    events.first.get("[output][0][Audit]") == nil &&
    events.first.get("[output][0][Cmd]") == nil &&
    events.first.get("[output][0][PID]") == 4 &&
    events.first.get("[output][0][process_depth]") == 0
  end
end

test "when one child process" do
  parameters {{ "source" => "raw", "target" => "output" }}
  in_event {{ "raw" => { "Audit" => nil, "Cmd" => nil, "PID" => 4, "__children" => [{ "Audit" => "MemCompression", "Cmd" => "MemCompression", "PID" => 1816, "__children" => [] } ] } }}
  
  expect("events are returned flat, without __children") do |events|
    events.first.get("[output][0][Audit]") == nil &&
    events.first.get("[output][0][Cmd]") == nil &&
    events.first.get("[output][0][PID]") == 4 &&
    events.first.get("[output][0][process_depth]") == 0 &&

    events.first.get("[output][1][Audit]") == "MemCompression" &&
    events.first.get("[output][1][Cmd]") == "MemCompression" &&
    events.first.get("[output][1][PID]") == 1816 &&
    events.first.get("[output][1][process_depth]") == 1
  end
end

test "when multiple child processes at same level" do
  parameters {{ "source" => "raw", "target" => "output" }}
  in_event {{ "raw" => { "Audit" => nil, "Cmd" => nil, "PID" => 4, "__children" => [ { "Audit" => "MemCompression", "Cmd" => "MemCompression", "PID" => 1816, "__children" => [] }, { "Audit" => "Registry", "Cmd" => "Registry", "PID" => 92, "__children" => [] } ] } }}

  expect("events are returned flat, without __children") do |events|
    events.first.get("[output][0][Audit]") == nil &&
    events.first.get("[output][0][Cmd]") == nil &&
    events.first.get("[output][0][PID]") == 4 &&
    events.first.get("[output][0][process_depth]") == 0 &&

    events.first.get("[output][1][Audit]") == "MemCompression" &&
    events.first.get("[output][1][Cmd]") == "MemCompression" &&
    events.first.get("[output][1][PID]") == 1816 &&
    events.first.get("[output][1][process_depth]") == 1 &&

    events.first.get("[output][2][Audit]") == "Registry" &&
    events.first.get("[output][2][Cmd]") == "Registry" &&
    events.first.get("[output][2][PID]") == 92 &&
    events.first.get("[output][2][process_depth]") == 1
  end
end

test "when multiple child processes at different levels" do
  parameters {{ "source" => "raw", "target" => "output" }}
  in_event {{ "raw" => { "Audit" => nil, "Cmd" => nil, "PID" => 4, "__children" => [ { "Audit" => "MemCompression", "Cmd" => "MemCompression", "PID" => 1816, "__children" => [ { "Audit" => "Registry", "Cmd" => "Registry", "PID" => 92, "__children" => [] } ] }, { "Audit" => "\\Device\\HarddiskVolume3\\Windows\\System32\\RuntimeBroker.exe", "Cmd" => "C:\\Windows\\System32\\RuntimeBroker.exe -Embedding", "PID" => 7852, "__children" => [] } ] } }}
  expect("events are returned flat, without __children") do |events|
    events.first.get("[output][0][Audit]") == nil &&
    events.first.get("[output][0][Cmd]") == nil &&
    events.first.get("[output][0][PID]") == 4 &&
    events.first.get("[output][0][process_depth]") == 0 &&

    events.first.get("[output][1][Audit]") == "MemCompression" &&
    events.first.get("[output][1][Cmd]") == "MemCompression" &&
    events.first.get("[output][1][PID]") == 1816 &&
    events.first.get("[output][1][process_depth]") == 1 &&

    events.first.get("[output][2][Audit]") == "Registry" &&
    events.first.get("[output][2][Cmd]") == "Registry" &&
    events.first.get("[output][2][PID]") == 92 &&
    events.first.get("[output][2][process_depth]") == 1 &&

    events.first.get("[output][3][Audit]") == "\\Device\\HarddiskVolume3\\Windows\\System32\\RuntimeBroker.exe" &&
    events.first.get("[output][3][Cmd]") == "C:\\Windows\\System32\\RuntimeBroker.exe -Embedding" &&
    events.first.get("[output][3][PID]") == 7852 &&
    events.first.get("[output][3][process_depth]") == 2
  end
end

test "when source field does not exist" do
  parameters {{ "source" => "raw2", "target" => "output" }}
  in_event {{ "raw" => { "Audit" => nil, "Cmd" => nil, "PID" => 4, "__children" => [] } }}
  expect("tags as not found") do |events|
    events.first.get("tags").include?("raw2_not_found")
  end
end
