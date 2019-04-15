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
    headerdata_perms_orig = event.get(@source_field)

    # set up the default fields
    headerdata_perms = {
        "_RawValue" => headerdata_perms_orig,
        "HasTargetIdList" => false,
        "HasLinkInfo" => false,
        "HasName" => false,
        "HasRelativePath" => false,
        "HasWorkingDir" => false,
        "HasArguments" => false,
        "HasIconLocation" => false,
        "IsUnicode" => false,
        "ForceNoLinkInfo" => false,
        "HasExpString" => false,
        "RunInSeparateProcess" => false,
        "Reserved0" => false,
        "HasDarwinId" => false,
        "RunAsUser" => false,
        "HasExpIcon" => false,
        "NoPidlAlias" => false,
        "Reserved1" => false,
        "RunWithShimLayer" => false,
        "ForceNoLinkTrack" => false,
        "EnableTargetMetadata" => false,
        "DisableLinkPathTracking" => false,
        "DisableKnownFolderTracking" => false,
        "DisableKnownFolderAlias" => false,
        "AllowLinkToLink" => false,
        "UnaliasOnSave" => false,
        "PreferEnvironmentPath" => false,
        "KeepLocalIdListForUncTarget" => false
    }

    # set true/false flags for each bit in the mask
    headerdata_perms["HasTargetIdList"] = true if (headerdata_perms_orig & 0x0001 != 0)
    headerdata_perms["HasLinkInfo"] = true if (headerdata_perms_orig & 0x0002 != 0)
    headerdata_perms["HasName"] = true if (headerdata_perms_orig & 0x0004 != 0)
    headerdata_perms["HasRelativePath"] = true if (headerdata_perms_orig & 0x008 != 0)
    headerdata_perms["HasWorkingDir"] = true if (headerdata_perms_orig & 0x0010 != 0)
    headerdata_perms["HasArguments"] = true if (headerdata_perms_orig & 0x0020 != 0)
    headerdata_perms["HasIconLocation"] = true if (headerdata_perms_orig & 0x0040 != 0)
    headerdata_perms["IsUnicode"] = true if (headerdata_perms_orig & 0x0080 != 0)
    headerdata_perms["ForceNoLinkInfo"] = true if (headerdata_perms_orig & 0x0100 != 0)
    headerdata_perms["HasExpString"] = true if (headerdata_perms_orig & 0x0200 != 0)
    headerdata_perms["RunInSeparateProcess"] = true if (headerdata_perms_orig & 0x0400 != 0)
    headerdata_perms["Reserved0"] = true if (headerdata_perms_orig & 0x0800 != 0)
    headerdata_perms["HasDarwinId"] = true if (headerdata_perms_orig & 0x1000 != 0)
    headerdata_perms["RunAsUser"] = true if (headerdata_perms_orig & 0x2000 != 0)
    headerdata_perms["HasExpIcon"] = true if (headerdata_perms_orig & 0x4000 != 0)
    headerdata_perms["NoPidlAlias"] = true if (headerdata_perms_orig & 0x8000 != 0)
    headerdata_perms["Reserved1"] = true if (headerdata_perms_orig & 0x010000 != 0)
    headerdata_perms["RunWithShimLayer"] = true if (headerdata_perms_orig & 0x020000 != 0)
    headerdata_perms["ForceNoLinkTrack"] = true if (headerdata_perms_orig & 0x040000 != 0)
    headerdata_perms["EnableTargetMetadata"] = true if (headerdata_perms_orig & 0x080000 != 0)
    headerdata_perms["DisableLinkPathTracking"] = true if (headerdata_perms_orig & 0x100000 != 0)
    headerdata_perms["DisableKnownFolderTracking"] = true if (headerdata_perms_orig & 0x200000 != 0)
    headerdata_perms["DisableKnownFolderAlias"] = true if (headerdata_perms_orig & 0x400000 != 0)
    headerdata_perms["AllowLinkToLink"] = true if (headerdata_perms_orig & 0x8000000 != 0)
    headerdata_perms["UnaliasOnSave"] = true if (headerdata_perms_orig & 0x10000000 != 0)
    headerdata_perms["PreferEnvironmentPath"] = true if (headerdata_perms_orig & 0x20000000 != 0)
    headerdata_perms["KeepLocalIdListForUncTarget"] = true if (headerdata_perms_orig & 0x40000000 != 0)

    # set a tag if there are any extraneous flags not addressed above
    event.tag("_HeaderDataFlagsParseFailure") if (headerdata_perms_orig & 0x70FFFFFF != headerdata_perms_orig)

    event.set(@source_field, headerdata_perms)

    return [event]
end