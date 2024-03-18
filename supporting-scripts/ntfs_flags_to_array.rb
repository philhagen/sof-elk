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

    # create array of all flags that are present, as indicated by each bit in the mask
    file_perms = Array.new()
    file_perms.push("readonly") if (file_perms_orig & 0x0001 != 0)
    file_perms.push("hidden") if (file_perms_orig & 0x0002 != 0)
    file_perms.push("system") if (file_perms_orig & 0x0004 != 0)
    file_perms.push("archive") if (file_perms_orig & 0x0020 != 0)
    file_perms.push("device") if (file_perms_orig & 0x0040 != 0)
    file_perms.push("normal") if (file_perms_orig & 0x0080 != 0)
    file_perms.push("temporary") if (file_perms_orig & 0x0100 != 0)
    file_perms.push("sparsefile") if (file_perms_orig & 0x0200 != 0)
    file_perms.push("reparsepoint") if (file_perms_orig & 0x0400 != 0)
    file_perms.push("compressed") if (file_perms_orig & 0x0800 != 0)
    file_perms.push("offline") if (file_perms_orig & 0x1000 != 0)
    file_perms.push("notcontentindexed") if (file_perms_orig & 0x2000 != 0)
    file_perms.push("encrypted") if (file_perms_orig & 0x4000 != 0)
    file_perms.push("integritystream") if (file_perms_orig & 0x8000 != 0)
    file_perms.push("virtual") if (file_perms_orig & 0x010000 != 0)
    file_perms.push("noscrubdata") if (file_perms_orig & 0x020000 != 0)
    file_perms.push("hasea") if (file_perms_orig & 0x040000 != 0)
    file_perms.push("directory") if (file_perms_orig & 0x10000000 != 0)
    file_perms.push("indexview") if (file_perms_orig & 0x20000000 != 0)

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
