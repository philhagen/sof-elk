# SOF-ELK® Supporting script
# (C)2025 Lewes Technology Consulting, LLC
#
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
        "forcenolinktrack" => false,
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
        headerdata_perms_orig = headerdata_perms_orig.to_i

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
        event.tag("_headerdataflagsparsefailure") if (headerdata_perms_orig & 0x78FFFFFF != headerdata_perms_orig)

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
        headerdata_perms["reserved0"] = true if (headerdata_perms_orig.include? "reserved0")
        headerdata_perms["hasdarwinid"] = true if (headerdata_perms_orig.include? "hasdarwinid")
        headerdata_perms["runasuser"] = true if (headerdata_perms_orig.include? "runasuser")
        headerdata_perms["hasexpicon"] = true if (headerdata_perms_orig.include? "hasexpicon")
        headerdata_perms["nopidlalias"] = true if (headerdata_perms_orig.include? "nopidlalias")
        headerdata_perms["reserved1"] = true if (headerdata_perms_orig.include? "reserved1")
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

## Validation tests

test "no flags in string" do
    parameters {{ "source_field" => "flags", "source_type" => "str" }}
    in_event {{ "flags" => "" }}
    expect("all false values") { |events| 
        newflags = events.first.get("flags")

        newflags["allowlinktolink"] == false &&
        newflags["disableknownfolderalias"] == false &&
        newflags["disableknownfoldertracking"] == false &&
        newflags["disablelinkpathtracking"] == false &&
        newflags["enabletargetmetadata"] == false &&
        newflags["forcenolinkinfo"] == false &&
        newflags["forcenolinktrack"] == false &&
        newflags["hasarguments"] == false &&
        newflags["hasdarwinid"] == false &&
        newflags["hasexpicon"] == false &&
        newflags["hasexpstring"] == false &&
        newflags["hasiconlocation"] == false &&
        newflags["haslinkinfo"] == false &&
        newflags["hasname"] == false &&
        newflags["hasrelativepath"] == false &&
        newflags["hastargetidlist"] == false &&
        newflags["hasworkingdir"] == false &&
        newflags["isunicode"] == false &&
        newflags["keeplocalidlistforunctarget"] == false &&
        newflags["nopidlalias"] == false &&
        newflags["preferenvironmentpath"] == false &&
        newflags["reserved0"] == false &&
        newflags["reserved1"] == false &&
        newflags["runasuser"] == false &&
        newflags["runinseparateprocess"] == false &&
        newflags["runwithshimlayer"] == false &&
        newflags["unaliasonsave"] == false
    }
end

test "no flags in integer" do
    parameters {{ "source_field" => "flags", "source_type" => "int" }}
    in_event {{ "flags" => 0 }}
    expect("all false values") { |events|
        newflags = events.first.get("flags")
        newtags = events.first.get("tags")

        newflags["allowlinktolink"] == false &&
        newflags["disableknownfolderalias"] == false &&
        newflags["disableknownfoldertracking"] == false &&
        newflags["disablelinkpathtracking"] == false &&
        newflags["enabletargetmetadata"] == false &&
        newflags["forcenolinkinfo"] == false &&
        newflags["forcenolinktrack"] == false &&
        newflags["hasarguments"] == false &&
        newflags["hasdarwinid"] == false &&
        newflags["hasexpicon"] == false &&
        newflags["hasexpstring"] == false &&
        newflags["hasiconlocation"] == false &&
        newflags["haslinkinfo"] == false &&
        newflags["hasname"] == false &&
        newflags["hasrelativepath"] == false &&
        newflags["hastargetidlist"] == false &&
        newflags["hasworkingdir"] == false &&
        newflags["isunicode"] == false &&
        newflags["keeplocalidlistforunctarget"] == false &&
        newflags["nopidlalias"] == false &&
        newflags["preferenvironmentpath"] == false &&
        newflags["reserved0"] == false &&
        newflags["reserved1"] == false &&
        newflags["runasuser"] == false &&
        newflags["runinseparateprocess"] == false &&
        newflags["runwithshimlayer"] == false &&
        newflags["unaliasonsave"] == false &&
        (newtags.nil? || newtags&.exclude?("_headerdataflagsparsefailure"))
    }
end

test "all flags in string" do
    parameters {{ "source_field" => "flags", "source_type" => "str" }}
    in_event {{ "flags" => "hastargetidlist,haslinkinfo,hasname,hasrelativepath,hasworkingdir,hasarguments,hasiconlocation,isunicode,forcenolinkinfo,hasexpstring,runinseparateprocess,reserved0,hasdarwinid,runasuser,hasexpicon,nopidlalias,reserved1,runwithshimlayer,forcenolinktrack,enabletargetmetadata,disablelinkpathtracking,disableknownfoldertracking,disableknownfolderalias,allowlinktolink,unaliasonsave,preferenvironmentpath,keeplocalidlistforunctarget" }}
    expect("all true values") { |events|
        newflags = events.first.get("flags")

        newflags["allowlinktolink"] == true &&
        newflags["disableknownfolderalias"] == true &&
        newflags["disableknownfoldertracking"] == true &&
        newflags["disablelinkpathtracking"] == true &&
        newflags["enabletargetmetadata"] == true &&
        newflags["forcenolinkinfo"] == true &&
        newflags["forcenolinktrack"] == true &&
        newflags["hasarguments"] == true &&
        newflags["hasdarwinid"] == true &&
        newflags["hasexpicon"] == true &&
        newflags["hasexpstring"] == true &&
        newflags["hasiconlocation"] == true &&
        newflags["haslinkinfo"] == true &&
        newflags["hasname"] == true &&
        newflags["hasrelativepath"] == true &&
        newflags["hastargetidlist"] == true &&
        newflags["hasworkingdir"] == true &&
        newflags["isunicode"] == true &&
        newflags["keeplocalidlistforunctarget"] == true &&
        newflags["nopidlalias"] == true &&
        newflags["preferenvironmentpath"] == true &&
        newflags["reserved0"] == true &&
        newflags["reserved1"] == true &&
        newflags["runasuser"] == true &&
        newflags["runinseparateprocess"] == true &&
        newflags["runwithshimlayer"] == true &&
        newflags["unaliasonsave"] == true
    }
end

test "all flags in integer" do
    parameters {{ "source_field" => "flags", "source_type" => "int" }}
    in_event {{ "flags" => 2030043135 }}
    expect("all true values") { |events|
        newflags = events.first.get("flags")
        newtags = events.first.get("tags")

        newflags["allowlinktolink"] == true &&
        newflags["disableknownfolderalias"] == true &&
        newflags["disableknownfoldertracking"] == true &&
        newflags["disablelinkpathtracking"] == true &&
        newflags["enabletargetmetadata"] == true &&
        newflags["forcenolinkinfo"] == true &&
        newflags["forcenolinktrack"] == true &&
        newflags["hasarguments"] == true &&
        newflags["hasdarwinid"] == true &&
        newflags["hasexpicon"] == true &&
        newflags["hasexpstring"] == true &&
        newflags["hasiconlocation"] == true &&
        newflags["haslinkinfo"] == true &&
        newflags["hasname"] == true &&
        newflags["hasrelativepath"] == true &&
        newflags["hastargetidlist"] == true &&
        newflags["hasworkingdir"] == true &&
        newflags["isunicode"] == true &&
        newflags["keeplocalidlistforunctarget"] == true &&
        newflags["nopidlalias"] == true &&
        newflags["preferenvironmentpath"] == true &&
        newflags["reserved0"] == true &&
        newflags["reserved1"] == true &&
        newflags["runasuser"] == true &&
        newflags["runinseparateprocess"] == true &&
        newflags["runwithshimlayer"] == true &&
        newflags["unaliasonsave"] == true &&
        (newtags.nil? || newtags&.exclude?("_headerdataflagsparsefailure"))
    }
end

test "some flags in string" do
    parameters {{ "source_field" => "flags", "source_type" => "str" }}
    in_event {{ "flags" => "hastargetidlist,hasname,hasworkingdir,hasarguments,isunicode,forcenolinkinfo,hasexpstring,runinseparateprocess,reserved0,hasdarwinid,runasuser,hasexpicon,nopidlalias,reserved1,runwithshimlayer,forcenolinktrack,enabletargetmetadata,disableknownfoldertracking,allowlinktolink,unaliasonsave" }}
    expect("proper output array") { |events| 
        newflags = events.first.get("flags")

        newflags["allowlinktolink"] == true &&
        newflags["disableknownfolderalias"] == false &&
        newflags["disableknownfoldertracking"] == true &&
        newflags["disablelinkpathtracking"] == false &&
        newflags["enabletargetmetadata"] == true &&
        newflags["forcenolinkinfo"] == true &&
        newflags["forcenolinktrack"] == true &&
        newflags["hasarguments"] == true &&
        newflags["hasdarwinid"] == true &&
        newflags["hasexpicon"] == true &&
        newflags["hasexpstring"] == true &&
        newflags["hasiconlocation"] == false &&
        newflags["haslinkinfo"] == false &&
        newflags["hasname"] == true &&
        newflags["hasrelativepath"] == false &&
        newflags["hastargetidlist"] == true &&
        newflags["hasworkingdir"] == true &&
        newflags["isunicode"] == true &&
        newflags["keeplocalidlistforunctarget"] == false &&
        newflags["nopidlalias"] == true &&
        newflags["preferenvironmentpath"] == false &&
        newflags["reserved0"] == true &&
        newflags["reserved1"] == true &&
        newflags["runasuser"] == true &&
        newflags["runinseparateprocess"] == true &&
        newflags["runwithshimlayer"] == true &&
        newflags["unaliasonsave"] == true
    }
end

test "some flags in integer" do
    parameters {{ "source_field" => "flags", "source_type" => "int" }}
    in_event {{ "flags" => 1354050422 }}
    expect("proper output array") { |events|
        newflags = events.first.get("flags")
        newtags = events.first.get("tags")

        newflags["allowlinktolink"] == false &&
        newflags["disableknownfolderalias"] == false &&
        newflags["disableknownfoldertracking"] == true &&
        newflags["disablelinkpathtracking"] == true &&
        newflags["enabletargetmetadata"] == false &&
        newflags["forcenolinkinfo"] == true &&
        newflags["forcenolinktrack"] == true &&
        newflags["hasarguments"] == true &&
        newflags["hasdarwinid"] == false &&
        newflags["hasexpicon"] == false &&
        newflags["hasexpstring"] == true &&
        newflags["hasiconlocation"] == true &&
        newflags["haslinkinfo"] == true &&
        newflags["hasname"] == true &&
        newflags["hasrelativepath"] == false &&
        newflags["hastargetidlist"] == false &&
        newflags["hasworkingdir"] == true &&
        newflags["isunicode"] == false &&
        newflags["keeplocalidlistforunctarget"] == true &&
        newflags["nopidlalias"] == false &&
        newflags["preferenvironmentpath"] == false &&
        newflags["reserved0"] == true &&
        newflags["reserved1"] == true &&
        newflags["runasuser"] == true &&
        newflags["runinseparateprocess"] == false &&
        newflags["runwithshimlayer"] == false &&
        newflags["unaliasonsave"] == true &&
        (newtags.nil? || newtags&.exclude?("_headerdataflagsparsefailure"))
    }
end

test "some invalid flags in integer" do
    parameters {{ "source_field" => "flags", "source_type" => "int" }}
    in_event {{ "flags" => 638093384 }}
    expect("proper output array and tag added") { |events|
        newflags = events.first.get("flags")
        newtags = events.first.get("tags")

        newflags["allowlinktolink"] == false &&
        newflags["disableknownfolderalias"] == false &&
        newflags["disableknownfoldertracking"] == false &&
        newflags["disablelinkpathtracking"] == false &&
        newflags["enabletargetmetadata"] == true &&
        newflags["forcenolinkinfo"] == false &&
        newflags["forcenolinktrack"] == false &&
        newflags["hasarguments"] == false &&
        newflags["hasdarwinid"] == false &&
        newflags["hasexpicon"] == false &&
        newflags["hasexpstring"] == false &&
        newflags["hasiconlocation"] == true &&
        newflags["haslinkinfo"] == false &&
        newflags["hasname"] == false &&
        newflags["hasrelativepath"] == true &&
        newflags["hastargetidlist"] == false &&
        newflags["hasworkingdir"] == false &&
        newflags["isunicode"] == false &&
        newflags["keeplocalidlistforunctarget"] == false &&
        newflags["nopidlalias"] == true &&
        newflags["preferenvironmentpath"] == true &&
        newflags["reserved0"] == true &&
        newflags["reserved1"] == false &&
        newflags["runasuser"] == false &&
        newflags["runinseparateprocess"] == false &&
        newflags["runwithshimlayer"] == false &&
        newflags["unaliasonsave"] == false &&
        newtags&.include?("_headerdataflagsparsefailure")
    }
end

test "only invalid flags in integer" do
    parameters {{ "source_field" => "flags", "source_type" => "int" }}
    in_event {{ "flags" => 83886080 }}
    expect("all false values and tag added") { |events|
        newflags = events.first.get("flags")
        newtags = events.first.get("tags")

        newflags["allowlinktolink"] == false &&
        newflags["disableknownfolderalias"] == false &&
        newflags["disableknownfoldertracking"] == false &&
        newflags["disablelinkpathtracking"] == false &&
        newflags["enabletargetmetadata"] == false &&
        newflags["forcenolinkinfo"] == false &&
        newflags["forcenolinktrack"] == false &&
        newflags["hasarguments"] == false &&
        newflags["hasdarwinid"] == false &&
        newflags["hasexpicon"] == false &&
        newflags["hasexpstring"] == false &&
        newflags["hasiconlocation"] == false &&
        newflags["haslinkinfo"] == false &&
        newflags["hasname"] == false &&
        newflags["hasrelativepath"] == false &&
        newflags["hastargetidlist"] == false &&
        newflags["hasworkingdir"] == false &&
        newflags["isunicode"] == false &&
        newflags["keeplocalidlistforunctarget"] == false &&
        newflags["nopidlalias"] == false &&
        newflags["preferenvironmentpath"] == false &&
        newflags["reserved0"] == false &&
        newflags["reserved1"] == false &&
        newflags["runasuser"] == false &&
        newflags["runinseparateprocess"] == false &&
        newflags["runwithshimlayer"] == false &&
        newflags["unaliasonsave"] == false &&
        newtags&.include?("_headerdataflagsparsefailure")
    }
end
