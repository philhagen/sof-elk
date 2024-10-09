# This script will convert a CSV string representing lnk file extra data
# blocks to an array of boolean values - one per flag.
#
# source_type="int" is not used at this time
# source_type="str" converts "trackerdatabaseblock,propertystoredatablock""

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
    extra_blocks_orig = event.get(@source_field)

    # set up the default fields
    extra_blocks = {
        "_rawvalue" => extra_blocks_orig,
        "environmentvariabledata" => false,
        "consoledata" => false,
        "trackerdatabase" => false,
        "consolefedata" => false,
        "specialfolderdata" => false,
        "darwindata" => false,
        "iconenvironmentdata" => false,
        "shimdata" => false,
        "propertystoredata" => false,
        "knownfolderdata" => false,
        "vistaandaboveidlistdata" => false,
        "damageddata" => false
    }

    # see https://github.com/libyal/liblnk/blob/main/documentation/Windows%20Shortcut%20File%20(LNK)%20format.asciidoc#21-data-flags
    if @source_type == "int"
        # set true/false flags for each bit in the mask
        extra_blocks["environmentvariabledata"] = true if (extra_blocks_orig & 0xa0000001 != 0)
        extra_blocks["consoledata"] = true if (extra_blocks_orig & 0xa0000002 != 0)
        extra_blocks["trackerdatabase"] = true if (extra_blocks_orig & 0xa0000003 != 0)
        extra_blocks["consolefedata"] = true if (extra_blocks_orig & 0xa0000004 != 0)
        extra_blocks["specialfolderdata"] = true if (extra_blocks_orig & 0xa0000005 != 0)
        extra_blocks["darwindata"] = true if (extra_blocks_orig & 0xa0000006 != 0)
        extra_blocks["iconenvironmentdata"] = true if (extra_blocks_orig & 0xa0000007 != 0)
        extra_blocks["shimdata"] = true if (extra_blocks_orig & 0xa0000008 != 0)
        extra_blocks["propertystoredata"] = true if (extra_blocks_orig & 0xa0000009 != 0)
        extra_blocks["knownfolderdata"] = true if (extra_blocks_orig & 0xa000000b != 0)
        extra_blocks["vistaandaboveidlistdata"] = true if (extra_blocks_orig & 0xa000000c != 0)
        extra_blocks["damageddata"] = false # this is not defined in the documentation linked above

    elsif @source_type == "str"
        # set true/false flags for each bit in the mask
        extra_blocks["environmentvariabledata"] = true if (extra_blocks_orig.include? "environmentvariabledata")
        extra_blocks["consoledata"] = true if (extra_blocks_orig.include? "consoledata")
        extra_blocks["trackerdatabase"] = true if (extra_blocks_orig.include? "trackerdatabase")
        extra_blocks["consolefedata"] = true if (extra_blocks_orig.include? "consolefedata")
        extra_blocks["specialfolderdata"] = true if (extra_blocks_orig.include? "specialfolderdata")
        extra_blocks["darwindata"] = true if (extra_blocks_orig.include? "darwindata")
        extra_blocks["iconenvironmentdata"] = true if (extra_blocks_orig.include? "iconenvironmentdata")
        extra_blocks["shimdata"] = true if (extra_blocks_orig.include? "shimdata")
        extra_blocks["propertystoredata"] = true if (extra_blocks_orig.include? "propertystoredata")
        extra_blocks["knownfolderdata"] = true if (extra_blocks_orig.include? "knownfolderdata")
        extra_blocks["vistaandaboveidlistdata"] = true if (extra_blocks_orig.include? "vistaandaboveidlistdata")

    end

    event.set(@source_field, extra_blocks)

    return [event]
end
