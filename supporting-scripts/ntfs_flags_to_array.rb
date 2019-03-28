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
        "_RawValue" => file_perms_orig,
        "ReadOnly" => false,
        "Hidden" => false,
        "System" => false,
        "Archive" => false,
        "Device" => false,
        "Normal" => false,
        "Temporary" => false,
        "SparseFile" => false,
        "ReparsePoint" => false,
        "Compressed" => false,
        "Offline" => false,
        "NotContentIndexed" => false,
        "Encrypted" => false,
        "IntegrityStream" => false,
        "Virtual" => false,
        "NoScrubData" => false,
        "HasEa" => false,
        "IsDirectory" => false,
        "IsIndexView" => false
    }

    # set true/false flags for each bit in the mask
    file_perms["ReadOnly"] = true if (file_perms_orig & 0x0001 != 0)
    file_perms["Hidden"] = true if (file_perms_orig & 0x0002 != 0)
    file_perms["System"] = true if (file_perms_orig & 0x0004 != 0)
    file_perms["Archive"] = true if (file_perms_orig & 0x0020 != 0)
    file_perms["Device"] = true if (file_perms_orig & 0x0040 != 0)
    file_perms["Normal"] = true if (file_perms_orig & 0x0080 != 0)
    file_perms["Temporary"] = true if (file_perms_orig & 0x0100 != 0)
    file_perms["SparseFile"] = true if (file_perms_orig & 0x0200 != 0)
    file_perms["ReparsePoint"] = true if (file_perms_orig & 0x0400 != 0)
    file_perms["Compressed"] = true if (file_perms_orig & 0x0800 != 0)
    file_perms["Offline"] = true if (file_perms_orig & 0x1000 != 0)
    file_perms["NotContentIndexed"] = true if (file_perms_orig & 0x2000 != 0)
    file_perms["Encrypted"] = true if (file_perms_orig & 0x4000 != 0)
    file_perms["IntegrityStream"] = true if (file_perms_orig & 0x8000 != 0)
    file_perms["Virtual"] = true if (file_perms_orig & 0x010000 != 0)
    file_perms["NoScrubData"] = true if (file_perms_orig & 0x020000 != 0)
    file_perms["HasEa"] = true if (file_perms_orig & 0x040000 != 0)
    file_perms["IsDirectory"] = true if (file_perms_orig & 0x10000000 != 0)
    file_perms["IsIndexView"] = true if (file_perms_orig & 0x20000000 != 0)

    # set a tag if there are any extraneous flags not addressed above
    event.tag("_SiFlagsParseFailure") if (file_perms_orig & 0x3007FFE7 != file_perms_orig)

    event.set(@source_field, file_perms)

    return [event]
end

#test "when field exists" do
#    parameters { { "source_field" => "SiFlags" } }
#    in_event { { "SiFlags" => 6  } }
#    expect("the flags are set in an array") {|events| events.first.get("[FilePerms][Hidden]" == true
#end