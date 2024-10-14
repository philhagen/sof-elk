# This script will convert an integer or CSV string representing NTFS data
# flags to an array of boolean values - one per flag.
#
# source_type="int" converts "4163"
# source_type="str" converts "hastargetidlist,isunicode,disableknownfoldertracking"

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
    headerdata_perms_orig = event.get(@source_field)

    # set up the default fields
    headerdata_perms = {
        "_rawvalue" => headerdata_perms_orig,
        "hastargetidlist" => false,
        "haslinkinfo" => false,
        "hasname" => false,
        "hasrelativepath" => false,
        "hasworkingdir" => false,
        "hasarguments" => false,
        "hasiconlocation" => false,
        "isunicode" => false,
        "forcenolinkinfo" => false,
        "hasexpstring" => false,
        "runinseparateprocess" => false,
        "reserved0" => false,
        "hasdarwinid" => false,
        "runasuser" => false,
        "hasexpicon" => false,
        "nopidlalias" => false,
        "reserved1" => false,
        "runwithshimlayer" => false,
        "forcenolintrack" => false,
        "enabletargetmetadata" => false,
        "disablelinkpathtracking" => false,
        "disableknownfoldertracking" => false,
        "disableknownfolderalias" => false,
        "allowlinktolink" => false,
        "unaliasonsave" => false,
        "preferenvironmentpath" => false,
        "keeplocalidlistforunctarget" => false
    }

    # see https://github.com/libyal/liblnk/blob/main/documentation/Windows%20Shortcut%20File%20(LNK)%20format.asciidoc#21-data-flags
    if @source_type == "int"
        # set true/false flags for each bit in the mask
        headerdata_perms["hastargetidlist"] = true if (headerdata_perms_orig & 0x0001 != 0)
        headerdata_perms["haslinkinfo"] = true if (headerdata_perms_orig & 0x0002 != 0)
        headerdata_perms["hasname"] = true if (headerdata_perms_orig & 0x0004 != 0)
        headerdata_perms["hasrelativepath"] = true if (headerdata_perms_orig & 0x008 != 0)
        headerdata_perms["hasworkingdir"] = true if (headerdata_perms_orig & 0x0010 != 0)
        headerdata_perms["hasarguments"] = true if (headerdata_perms_orig & 0x0020 != 0)
        headerdata_perms["hasiconlocation"] = true if (headerdata_perms_orig & 0x0040 != 0)
        headerdata_perms["isunicode"] = true if (headerdata_perms_orig & 0x0080 != 0)
        headerdata_perms["forcenolinkinfo"] = true if (headerdata_perms_orig & 0x0100 != 0)
        headerdata_perms["hasexpstring"] = true if (headerdata_perms_orig & 0x0200 != 0)
        headerdata_perms["runinseparateprocess"] = true if (headerdata_perms_orig & 0x0400 != 0)
        headerdata_perms["reserved0"] = true if (headerdata_perms_orig & 0x0800 != 0)
        headerdata_perms["hasdarwinid"] = true if (headerdata_perms_orig & 0x1000 != 0)
        headerdata_perms["runasuser"] = true if (headerdata_perms_orig & 0x2000 != 0)
        headerdata_perms["hasexpicon"] = true if (headerdata_perms_orig & 0x4000 != 0)
        headerdata_perms["nopidlalias"] = true if (headerdata_perms_orig & 0x8000 != 0)
        headerdata_perms["reserved1"] = true if (headerdata_perms_orig & 0x010000 != 0)
        headerdata_perms["runwithshimlayer"] = true if (headerdata_perms_orig & 0x020000 != 0)
        headerdata_perms["forcenolinktrack"] = true if (headerdata_perms_orig & 0x040000 != 0)
        headerdata_perms["enabletargetmetadata"] = true if (headerdata_perms_orig & 0x080000 != 0)
        headerdata_perms["disablelinkpathtracking"] = true if (headerdata_perms_orig & 0x100000 != 0)
        headerdata_perms["disableknownfoldertracking"] = true if (headerdata_perms_orig & 0x200000 != 0)
        headerdata_perms["disableknownfolderalias"] = true if (headerdata_perms_orig & 0x400000 != 0)
        headerdata_perms["allowlinktolink"] = true if (headerdata_perms_orig & 0x8000000 != 0)
        headerdata_perms["unaliasonsave"] = true if (headerdata_perms_orig & 0x10000000 != 0)
        headerdata_perms["preferenvironmentpath"] = true if (headerdata_perms_orig & 0x20000000 != 0)
        headerdata_perms["keeplocalidlistforunctarget"] = true if (headerdata_perms_orig & 0x40000000 != 0)

        # set a tag if there are any extraneous flags not addressed above
        event.tag("_headerdataflagsparsefailure") if (headerdata_perms_orig & 0x70FFFFFF != headerdata_perms_orig)

    elsif @source_type == "str"
        # set true/false flags for each bit in the mask
        headerdata_perms["hastargetidlist"] = true if (headerdata_perms_orig.include? "hastargetidlist")
        headerdata_perms["haslinkinfo"] = true if (headerdata_perms_orig.include? "haslinkinfo")
        headerdata_perms["hasname"] = true if (headerdata_perms_orig.include? "hasname")
        headerdata_perms["hasrelativepath"] = true if (headerdata_perms_orig.include? "hasrelativepath")
        headerdata_perms["hasworkingdir"] = true if (headerdata_perms_orig.include? "hasworkingdir")
        headerdata_perms["hasarguments"] = true if (headerdata_perms_orig.include? "hasarguments")
        headerdata_perms["hasiconlocation"] = true if (headerdata_perms_orig.include? "hasiconlocation")
        headerdata_perms["isunicode"] = true if (headerdata_perms_orig.include? "isunicode")
        headerdata_perms["forcenolinkinfo"] = true if (headerdata_perms_orig.include? "forcenolinkinfo")
        headerdata_perms["hasexpstring"] = true if (headerdata_perms_orig.include? "hasexpstring")
        headerdata_perms["runinseparateprocess"] = true if (headerdata_perms_orig.include? "runinseparateprocess")
        headerdata_perms["hasdarwinid"] = true if (headerdata_perms_orig.include? "hasdarwinid")
        headerdata_perms["runasuser"] = true if (headerdata_perms_orig.include? "runasuser")
        headerdata_perms["hasexpicon"] = true if (headerdata_perms_orig.include? "hasexpicon")
        headerdata_perms["nopidlalias"] = true if (headerdata_perms_orig.include? "nopidlalias")
        headerdata_perms["runwithshimlayer"] = true if (headerdata_perms_orig.include? "runwithshimlayer")
        headerdata_perms["forcenolinktrack"] = true if (headerdata_perms_orig.include? "forcenolinktrack")
        headerdata_perms["enabletargetmetadata"] = true if (headerdata_perms_orig.include? "enabletargetmetadata")
        headerdata_perms["disablelinkpathtracking"] = true if (headerdata_perms_orig.include? "disablelinkpathtracking")
        headerdata_perms["disableknownfoldertracking"] = true if (headerdata_perms_orig.include? "disableknownfoldertracking")
        headerdata_perms["disableknownfolderalias"] = true if (headerdata_perms_orig.include? "disableknownfolderalias")
        headerdata_perms["allowlinktolink"] = true if (headerdata_perms_orig.include? "allowlinktolink")
        headerdata_perms["unaliasonsave"] = true if (headerdata_perms_orig.include? "unaliasonsave")
        headerdata_perms["preferenvironmentpath"] = true if (headerdata_perms_orig.include? "preferenvironmentpath")
        headerdata_perms["keeplocalidlistforunctarget"] = true if (headerdata_perms_orig.include? "keeplocalidlistforunctarget")

    end

    event.set(@source_field, headerdata_perms)

    return [event]
end
