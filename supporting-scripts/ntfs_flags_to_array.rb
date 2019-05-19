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
    file_perms_orig = event.get(@source_field)

    # set up the default fields
    file_perms = {
        "_rawvalue" => file_perms_orig,
        "readonly" => false,
        "hidden" => false,
        "system" => false,
        "archive" => false,
        "device" => false,
        "normal" => false,
        "temporary" => false,
        "sparsefile" => false,
        "reparsepoint" => false,
        "compressed" => false,
        "offline" => false,
        "notcontentindexed" => false,
        "encrypted" => false,
        "integritystream" => false,
        "virtual" => false,
        "noscrubdata" => false,
        "hasea" => false,
        "isdirectory" => false,
        "isindexview" => false
    }

    # set true/false flags for each bit in the mask
    file_perms["readonly"] = true if (file_perms_orig & 0x0001 != 0)
    file_perms["hidden"] = true if (file_perms_orig & 0x0002 != 0)
    file_perms["system"] = true if (file_perms_orig & 0x0004 != 0)
    file_perms["archive"] = true if (file_perms_orig & 0x0020 != 0)
    file_perms["device"] = true if (file_perms_orig & 0x0040 != 0)
    file_perms["normal"] = true if (file_perms_orig & 0x0080 != 0)
    file_perms["temporary"] = true if (file_perms_orig & 0x0100 != 0)
    file_perms["sparsefile"] = true if (file_perms_orig & 0x0200 != 0)
    file_perms["reparsepoint"] = true if (file_perms_orig & 0x0400 != 0)
    file_perms["compressed"] = true if (file_perms_orig & 0x0800 != 0)
    file_perms["offline"] = true if (file_perms_orig & 0x1000 != 0)
    file_perms["notcontentindexed"] = true if (file_perms_orig & 0x2000 != 0)
    file_perms["encrypted"] = true if (file_perms_orig & 0x4000 != 0)
    file_perms["integritystream"] = true if (file_perms_orig & 0x8000 != 0)
    file_perms["virtual"] = true if (file_perms_orig & 0x010000 != 0)
    file_perms["noscrubdata"] = true if (file_perms_orig & 0x020000 != 0)
    file_perms["hasea"] = true if (file_perms_orig & 0x040000 != 0)
    file_perms["isdirectory"] = true if (file_perms_orig & 0x10000000 != 0)
    file_perms["isindexview"] = true if (file_perms_orig & 0x20000000 != 0)

    # set a tag if there are any extraneous flags not addressed above
    event.tag("_siflagsparsefailure") if (file_perms_orig & 0x3007FFE7 != file_perms_orig)

    event.set(@source_field, file_perms)

    return [event]
end

#test "when field exists" do
#    parameters { { "source_field" => "SiFlags" } }
#    in_event { { "SiFlags" => 6  } }
#    expect("the flags are set in an array") {|events| events.first.get("[FilePerms][Hidden]" == true
#end
