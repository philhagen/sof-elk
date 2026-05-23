# SOF-ELK® Supporting script
# (C)2026 Lewes Technology Consulting, LLC
#
# This script processes a volatility 3 "pstree" object and recursively structures all child processes into a flat set of results with a process depth field applied

def register(params)
  @source_field = params.fetch("source", "[message]")
  @target_field = params.fetch("target", "[processes]")
end

# this is a recursive function that will add each individual process structure to the "result" array,
#   then traverse down the __children array, if present+populated.  depth will be assigned at each level,
#   starting with 0
def flatten_process_tree(process, depth = 0)
  result = []

  process['process_depth'] = depth

  if process['__children'].is_a?(Array) && process['__children'].length > 0

    # peel off the __children field and add what's left at the top level to the result array
    children = process.delete('__children')
    result << process

    # traverse the child processes, adding the output from each iteration to the result array
    children.each do |child_process|
      result += flatten_process_tree(child_process, depth + 1)
    end

  else
    # this occurs when there is no __children or __children==[]
    # if so, add what's at the top-level to the result array
    process.delete('__children')
    result << process
  end

  return result
end

def filter(event)
  # Tag and exit if source field isn't present
  if event.get(@source_field).nil?
    event.tag("#{@source_field}_not_found")
    return [event]
  end

  # Retrieve the source
  source = event.get(@source_field)

  flat_process_list = flatten_process_tree(source)

  event.set(@target_field, flat_process_list)
  return [event]
end

### Validation Tests
test "when no child processes" do
  parameters {{ "source" => "raw", "target" => "output" }}
  in_event {{ "raw" => { "Audit" => nil, "Cmd" => nil, "PID" => 4, "__children" => [] } }}

  expect("event is returned without __children") { |events|
    events.first.get("[output][0][Audit]") == nil &&
    events.first.get("[output][0][Cmd]") == nil &&
    events.first.get("[output][0][PID]") == 4 &&
    events.first.get("[output][0][process_depth]") == 0 &&
    events.first.get("[output][0][__children]") == nil
  }
end

test "when one child process" do
  parameters {{ "source" => "raw", "target" => "output" }}
  in_event {{ "raw" => { "Audit" => nil, "Cmd" => nil, "PID" => 4, "__children" => [{ "Audit" => "MemCompression", "Cmd" => "MemCompression", "PID" => 1816, "__children" => [] } ] } }}
  
  expect("events are returned flat, without __children") { |events|
    events.first.get("[output][0][Audit]") == nil &&
    events.first.get("[output][0][Cmd]") == nil &&
    events.first.get("[output][0][PID]") == 4 &&
    events.first.get("[output][0][process_depth]") == 0 &&
    events.first.get("[output][0][__children]") == nil &&

    events.first.get("[output][1][Audit]") == "MemCompression" &&
    events.first.get("[output][1][Cmd]") == "MemCompression" &&
    events.first.get("[output][1][PID]") == 1816 &&
    events.first.get("[output][1][process_depth]") == 1 &&
    events.first.get("[output][1][__children]") == nil
  }
end

test "when multiple child processes at same level" do
  parameters {{ "source" => "raw", "target" => "output" }}
  in_event {{ "raw" => { "Audit" => nil, "Cmd" => nil, "PID" => 4, "__children" => [ { "Audit" => "MemCompression", "Cmd" => "MemCompression", "PID" => 1816, "__children" => [] }, { "Audit" => "Registry", "Cmd" => "Registry", "PID" => 92, "__children" => [] } ] } }}

  expect("events are returned flat, without __children") { |events|
    events.first.get("[output][0][Audit]") == nil &&
    events.first.get("[output][0][Cmd]") == nil &&
    events.first.get("[output][0][PID]") == 4 &&
    events.first.get("[output][0][process_depth]") == 0 &&
    events.first.get("[output][0][__children]") == nil &&

    events.first.get("[output][1][Audit]") == "MemCompression" &&
    events.first.get("[output][1][Cmd]") == "MemCompression" &&
    events.first.get("[output][1][PID]") == 1816 &&
    events.first.get("[output][1][process_depth]") == 1 &&
    events.first.get("[output][1][__children]") == nil &&

    events.first.get("[output][2][Audit]") == "Registry" &&
    events.first.get("[output][2][Cmd]") == "Registry" &&
    events.first.get("[output][2][PID]") == 92 &&
    events.first.get("[output][2][process_depth]") == 1 &&
    events.first.get("[output][2][__children]") == nil
  }
end

test "when multiple child processes at different levels" do
  parameters {{ "source" => "raw", "target" => "output" }}
  in_event {{ "raw" => { "Audit" => nil, "Cmd" => nil, "PID" => 4, "__children" => [ { "Audit" => "MemCompression", "Cmd" => "MemCompression", "PID" => 1816, "__children" => [ { "Audit" => "Registry", "Cmd" => "Registry", "PID" => 92, "__children" => [] } ] }, { "Audit" => "\\Device\\HarddiskVolume3\\Windows\\System32\\RuntimeBroker.exe", "Cmd" => "C:\\Windows\\System32\\RuntimeBroker.exe -Embedding", "PID" => 7852, "__children" => [] } ] } }}
  expect("events are returned flat, without __children") { |events|
    events.first.get("[output][0][Audit]") == nil &&
    events.first.get("[output][0][Cmd]") == nil &&
    events.first.get("[output][0][PID]") == 4 &&
    events.first.get("[output][0][process_depth]") == 0 &&
    events.first.get("[output][0][__children]") == nil &&

    events.first.get("[output][1][Audit]") == "MemCompression" &&
    events.first.get("[output][1][Cmd]") == "MemCompression" &&
    events.first.get("[output][1][PID]") == 1816 &&
    events.first.get("[output][1][process_depth]") == 1 &&
    events.first.get("[output][1][__children]") == nil &&

    events.first.get("[output][2][Audit]") == "Registry" &&
    events.first.get("[output][2][Cmd]") == "Registry" &&
    events.first.get("[output][2][PID]") == 92 &&
    events.first.get("[output][2][process_depth]") == 2 &&
    events.first.get("[output][2][__children]") == nil &&

    events.first.get("[output][3][Audit]") == "\\Device\\HarddiskVolume3\\Windows\\System32\\RuntimeBroker.exe" &&
    events.first.get("[output][3][Cmd]") == "C:\\Windows\\System32\\RuntimeBroker.exe -Embedding" &&
    events.first.get("[output][3][PID]") == 7852 &&
    events.first.get("[output][3][process_depth]") == 1 &&
    events.first.get("[output][3][__children]") == nil
  }
end

test "when source field does not exist" do
  parameters {{ "source" => "raw2", "target" => "output" }}
  in_event {{ "raw" => { "Audit" => nil, "Cmd" => nil, "PID" => 4, "__children" => [] } }}
  expect("tags as not found") { |events|
    events.first.get("tags").include?("raw2_not_found")
  }
end
