# SOF-ELK® Processor: NTFS Flags
# (C)2025 Lewes Technology Consulting, LLC
#
# Ported from ntfs_flags_to_array.rb and data_flags_to_array.rb


class NTFS:
    # See https://github.com/libyal/liblnk/blob/main/documentation/Windows%20Shortcut%20File%20(LNK)%20format.asciidoc#21-data-flags
    DATA_FLAGS_MAP = {
        "hastargetidlist": 0x0001,
        "haslinkinfo": 0x0002,
        "hasname": 0x0004,
        "hasrelativepath": 0x0008,
        "hasworkingdir": 0x0010,
        "hasarguments": 0x0020,
        "hasiconlocation": 0x0040,
        "isunicode": 0x0080,
        "forcenolinkinfo": 0x0100,
        "hasexpstring": 0x0200,
        "runinseparateprocess": 0x0400,
        "reserved0": 0x0800,
        "hasdarwinid": 0x1000,
        "runasuser": 0x2000,
        "hasexpicon": 0x4000,
        "nopidlalias": 0x8000,
        "reserved1": 0x010000,
        "runwithshimlayer": 0x020000,
        "forcenolinktrack": 0x040000,
        "enabletargetmetadata": 0x080000,
        "disablelinkpathtracking": 0x100000,
        "disableknownfoldertracking": 0x200000,
        "disableknownfolderalias": 0x400000,
        "allowlinktolink": 0x04000000,  # Note: Ruby script had 0x8000000? Let's verify.
        "unaliasonsave": 0x08000000,  # Note: Ruby script had 0x10000000?
        "preferenvironmentpath": 0x10000000,  # Ruby had 0x20000000
        "keeplocalidlistforunctarget": 0x20000000,  # Ruby had 0x40000000
    }
    # Wait, let me double check the Ruby script content from history step 14 to be safe.
    # Ruby script said:
    # "allowlinktolink" => true if (headerdata_perms_orig & 0x8000000 != 0)
    # "unaliasonsave" => true if (headerdata_perms_orig & 0x10000000 != 0)
    # "preferenvironmentpath" => true if (headerdata_perms_orig & 0x20000000 != 0)
    # "keeplocalidlistforunctarget" => true if (headerdata_perms_orig & 0x40000000 != 0)
    # Correcting below to match Ruby script exactly.

    DATA_FLAGS_MAP_CORRECTED = {
        "hastargetidlist": 0x0001,
        "haslinkinfo": 0x0002,
        "hasname": 0x0004,
        "hasrelativepath": 0x0008,
        "hasworkingdir": 0x0010,
        "hasarguments": 0x0020,
        "hasiconlocation": 0x0040,
        "isunicode": 0x0080,
        "forcenolinkinfo": 0x0100,
        "hasexpstring": 0x0200,
        "runinseparateprocess": 0x0400,
        "reserved0": 0x0800,
        "hasdarwinid": 0x1000,
        "runasuser": 0x2000,
        "hasexpicon": 0x4000,
        "nopidlalias": 0x8000,
        "reserved1": 0x010000,
        "runwithshimlayer": 0x020000,
        "forcenolinktrack": 0x040000,
        "enabletargetmetadata": 0x080000,
        "disablelinkpathtracking": 0x100000,
        "disableknownfoldertracking": 0x200000,
        "disableknownfolderalias": 0x400000,
        "allowlinktolink": 0x08000000,
        "unaliasonsave": 0x10000000,
        "preferenvironmentpath": 0x20000000,
        "keeplocalidlistforunctarget": 0x40000000,
    }

    FILE_ATTRS_MAP = {
        "readonly": 0x0001,
        "hidden": 0x0002,
        "system": 0x0004,
        "archive": 0x0020,
        "device": 0x0040,
        "normal": 0x0080,
        "temporary": 0x0100,
        "sparsefile": 0x0200,
        "reparsepoint": 0x0400,
        "compressed": 0x0800,
        "offline": 0x1000,
        "notcontentindexed": 0x2000,
        "encrypted": 0x4000,
        "integritystream": 0x8000,
        "virtual": 0x010000,
        "noscrubdata": 0x020000,
        "hasea": 0x040000,
        "directory": 0x10000000,
        "indexview": 0x20000000,
    }

    @staticmethod
    def parse_data_flags(value: int | str, source_type: str = "int") -> dict[str, bool]:
        """
        Parse NTFS data flags.

        Args:
            value: Integer or String representation of flags.
            source_type (str): 'int' or 'str'

        Returns:
            dict: {flag_name: boolean}
        """
        result = {k: False for k in NTFS.DATA_FLAGS_MAP_CORRECTED.keys()}

        if source_type == "int":
            try:
                int_val = int(value)
                for k, mask in NTFS.DATA_FLAGS_MAP_CORRECTED.items():
                    if (int_val & mask) != 0:
                        result[k] = True
            except ValueError:
                pass  # Return all false

        elif source_type == "str":
            if not value:
                return result
            val_str = str(value).lower()
            for k in NTFS.DATA_FLAGS_MAP_CORRECTED.keys():
                if k in val_str:
                    result[k] = True

        return result

    @staticmethod
    def parse_file_attributes(value: int | str, source_type: str = "int") -> dict[str, bool]:
        """
        Parse NTFS file attribute flags.

        Args:
            value: Integer or String representation of flags.
            source_type (str): 'int' or 'str'

        Returns:
            dict: {flag_name: boolean}
        """
        result = {k: False for k in NTFS.FILE_ATTRS_MAP.keys()}

        if source_type == "int":
            try:
                int_val = int(value)
                for k, mask in NTFS.FILE_ATTRS_MAP.items():
                    if (int_val & mask) != 0:
                        result[k] = True
            except ValueError:
                pass

        elif source_type == "str":
            if not value:
                return result
            val_str = str(value).lower()
            for k in NTFS.FILE_ATTRS_MAP.keys():
                if k in val_str:
                    result[k] = True

        return result
