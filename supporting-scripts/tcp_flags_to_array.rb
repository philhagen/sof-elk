# SOF-ELK® Supporting script
# (C)2023 Lewes Technology Consulting, LLC
#
# This script creates an array of TCP flags from an integer (or hex value)

# the value of `params` is the value of the hash passed to `script_params`
# in the logstash configuration
def register(params)
    @source_field = params["source_field"]
    @source_type = params["source_type"]
end

# the filter method receives an event and must return a list of events.
# Dropping an event means not including it in the return array,
# while creating new ones only requires you to add a new instance of
# LogStash::Event to the returned array
def filter(event)

    # create empty array
    tcp_flags = Array.new()

    if @source_type == "int"
        tcp_flags_int = event.get(@source_field).to_i
        
        # Add to the array based on values in the bitmask
        tcp_flags.push("cwr") if (tcp_flags_int & 0x80 != 0)
        tcp_flags.push("ece") if (tcp_flags_int & 0x40 != 0)
        tcp_flags.push("urg") if (tcp_flags_int & 0x20 != 0)
        tcp_flags.push("ack") if (tcp_flags_int & 0x10 != 0)
        tcp_flags.push("psh") if (tcp_flags_int & 0x08 != 0)
        tcp_flags.push("rst") if (tcp_flags_int & 0x04 != 0)
        tcp_flags.push("syn") if (tcp_flags_int & 0x02 != 0)
        tcp_flags.push("fin") if (tcp_flags_int & 0x01 != 0)

    elsif @source_type == "str"
        # remove dots
        tcp_flags_int = 0
        tcp_flags_str = event.get(@source_field).tr(".","")

        # split remaining characters to an array
        tcp_flags = tcp_flags_str.chars.sort

        # get the integer value
        tcp_flags_int += 1 if tcp_flags.include? "F"
        tcp_flags_int += 2 if tcp_flags.include? "S"
        tcp_flags_int += 4 if tcp_flags.include? "R"
        tcp_flags_int += 8 if tcp_flags.include? "P"
        tcp_flags_int += 16 if tcp_flags.include? "A"
        tcp_flags_int += 32 if tcp_flags.include? "U"
        tcp_flags_int += 64 if tcp_flags.include? "E"
        tcp_flags_int += 128 if tcp_flags.include? "C"

    end

    event.set("network.tcp_flags", tcp_flags)
    event.set("network.tcp_flags_hex", "0x" + tcp_flags_int.to_s(16).upcase)
    event.set("network.tcp_flags_str", tcp_flags.sort.join())
    event.remove("[netflow][tcp_control_bits]")
    event.set("netflow.tcp_control_bits", tcp_flags_int)

    return [event]
end
