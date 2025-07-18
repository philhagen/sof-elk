# SOF-ELK® Supporting script
# (C)2025 Lewes Technology Consulting, LLC
#
# This script uses the TCP flags field (as an array of words, string of letters,
#   or integer) and calculates the missing values, overwriting or adding fields
#   (array of words, integer, and hex value) as needed

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
    if @source_type == "int"
        tcp_flags_int = event.get(@source_field).to_i

    elsif @source_type == "arr"
        # get source array
        tcp_flags = event.get(@source_field)

        # build a string
        tcp_flags_str = ""
        tcp_flags.each { |flag| tcp_flags_str += "#{flag[0].upcase}" }

        # treat the derived string as such for the rest of the process
        @source_type = "str"

    elsif @source_type == "str"
        # get source string
        tcp_flags_str = event.get(@source_field)
    end

    if @source_type == "str"
        # calculate the integer value
        tcp_flags_int = 0
        tcp_flags_int += 1 if tcp_flags_str.include?("F")
        tcp_flags_int += 2 if tcp_flags_str.include?("S")
        tcp_flags_int += 4 if tcp_flags_str.include?("R")
        tcp_flags_int += 8 if tcp_flags_str.include?("P")
        tcp_flags_int += 16 if tcp_flags_str.include?("A")
        tcp_flags_int += 32 if tcp_flags_str.include?("U")
        tcp_flags_int += 64 if tcp_flags_str.include?("E")
        tcp_flags_int += 128 if tcp_flags_str.include?("C")
    end

    # Create array based on values in the bitmask
    tcp_flags = Array.new()
    tcp_flags.push("cwr") if (tcp_flags_int & 0x80 != 0)
    tcp_flags.push("ece") if (tcp_flags_int & 0x40 != 0)
    tcp_flags.push("urg") if (tcp_flags_int & 0x20 != 0)
    tcp_flags.push("ack") if (tcp_flags_int & 0x10 != 0)
    tcp_flags.push("psh") if (tcp_flags_int & 0x08 != 0)
    tcp_flags.push("rst") if (tcp_flags_int & 0x04 != 0)
    tcp_flags.push("syn") if (tcp_flags_int & 0x02 != 0)
    tcp_flags.push("fin") if (tcp_flags_int & 0x01 != 0)

    # set the field for the array
    event.remove("[network][tcp_flags]")
    event.set("network.tcp_flags", tcp_flags)

    # set the field for the integer
    event.remove("[netflow][tcp_control_bits]")
    event.set("netflow.tcp_control_bits", tcp_flags_int)

    # set the field for the hex version of the integer
    event.remove("[network.tcp_flags_hex]")
    event.set("network.tcp_flags_hex", "0x" + tcp_flags_int.to_s(16).upcase)

    return [event]
end
