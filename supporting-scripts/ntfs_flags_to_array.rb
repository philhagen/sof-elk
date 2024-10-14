# SOF-ELK® Supporting script
# (C)2024 Lewes Technology Consulting, LLC
#
# This script will convert an integer or CSV string representing NTFS file
# attribute flags to array of boolean values - one per flag.
#
# source_type="int" converts "6277"
# source_type="str" converts "fileattributereadonly,fileattributedirectory"

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
    file_perms_orig = event.get(@source_field)
    file_perms_type = event.get(@source_type)

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
        "directory" => false,
        "indexview" => false
    }

    # create array of all flags, with boolean set as indicated in the original value
    if file_perms_type == "int"
        file_perms_orig = file_perms_orig.to_i

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
        file_perms["directory"] = true if (file_perms_orig & 0x10000000 != 0)
        file_perms["indexview"] = true if (file_perms_orig & 0x20000000 != 0)

        # set a tag if there are any extraneous flags not addressed above
        event.tag("_siflagsparsefailure") if (file_perms_orig & 0x3007FFE7 != file_perms_orig)

    elsif file_perms_type == "str"
        file_perms["readonly"] = true if (file_perms_orig.include? "readonly")
        file_perms["hidden"] = true if (file_perms_orig.include? "hidden")
        file_perms["system"] = true if (file_perms_orig.include? "system")
        file_perms["archive"] = true if (file_perms_orig.include? "archive")
        file_perms["device"] = true if (file_perms_orig.include? "device")
        file_perms["normal"] = true if (file_perms_orig.include? "normal")
        file_perms["temporary"] = true if (file_perms_orig.include? "temporary")
        file_perms["sparsefile"] = true if (file_perms_orig.include? "sparsefile")
        file_perms["reparsepoint"] = true if (file_perms_orig.include? "reparsepoint")
        file_perms["compressed"] = true if (file_perms_orig.include? "compressed")
        file_perms["offline"] = true if (file_perms_orig.include? "offline")
        file_perms["notcontentindexed"] = true if (file_perms_orig.include? "notcontentindexed")
        file_perms["encrypted"] = true if (file_perms_orig.include? "encrypted")
        file_perms["integritystream"] = true if (file_perms_orig.include? "integritystream")
        file_perms["virtual"] = true if (file_perms_orig.include? "virtual")
        file_perms["noscrubdata"] = true if (file_perms_orig.include? "noscrubdata")
        file_perms["hasea"] = true if (file_perms_orig.include? "hasea")
        file_perms["directory"] = true if (file_perms_orig.include? "directory")
        file_perms["indexview"] = true if (file_perms_orig.include? "indexview")

    end

    event.set(@source_field, file_perms)

    return [event]
end

#test "when field exists" do
#    parameters { { "source_field" => "SiFlags" } }
#    in_event { { "SiFlags" => 6  } }
#    expect("the flags are set in an array") {|events| events.first.get("[FilePerms][Hidden]" == true
#end
