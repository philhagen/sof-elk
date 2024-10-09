# This script will convert a string with a hex representation of a number to
# its integer value, overwriting the source

# the value of `params` is the value of the hash passed to `script_params`
# in the logstash configuration
def register(params)
    @source_field = params["source_field"]
end

# the filter method receives an event and must return a list of events.
# Dropping an event means not including it in the return array,
# while creating new ones only requires you to add a new instance of
# LogStash::Event to the returned array
def filter(event)
    hex_string = event.get(@source_field)

    event.set(@source_field, hex_string.hex)

    return [event]
end
