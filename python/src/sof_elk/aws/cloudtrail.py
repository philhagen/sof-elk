import os
import re
import sys
from .common import AWSCommon
from typing import List, Any, Optional

class CloudTrailProcessor(AWSCommon):
    """
    Process AWS CloudTrail logs.
    """
    
    FILENAME_REGEX = re.compile(
        r"(?P<account_id>\d{12})_CloudTrail_(?P<region_name>[A-Za-z0-9-]+)_(?P<year>\d{4})(?P<month>\d{2})(?P<day>\d{2})T(?P<time>\d{4})Z_.*"
    )

    @classmethod
    def process_file(cls, infile: str, reduce_noise: bool = False) -> List[Any]:
        """
        Process a single CloudTrail log file and return its records.
        """
        raw_json = cls.smart_open_json(infile)
        if raw_json is None:
            return []

        if "Records" not in raw_json: # type: ignore
            sys.stderr.write(
                f"- ERROR: Input file {infile} does not appear to contain AWS CloudTrail records. Skipping file.\n"
            )
            return []

        records: List[Any] = raw_json["Records"] # type: ignore
        if reduce_noise:
            return cls.remove_noise(records)
        
        return records

    @staticmethod
    def remove_noise(records: List[Any]) -> List[Any]:
        """
        Filter out noisy records (e.g. for509trails bucket usage) matching cloudtrail-reduce.sh behavior.
        """
        filtered: List[Any] = []
        for record in records:
            # Logic: .requestParameters.bucketName == null or != "for509trails"
            # In Python: keep if bucketName is None OR bucketName != "for509trails"
            
            rp: Any = record.get("requestParameters")
            if rp is None:
                filtered.append(record)
                continue
            
            # If rp is not None, check bucketName
            # Note: requestParameters can be a dict or potentially other types in malformed logs, but usually dict.
            if isinstance(rp, dict):
                bucket_name: Optional[Any] = rp.get("bucketName")
                if bucket_name != "for509trails":
                    filtered.append(record)
            else:
                # If structure is weird, keep it to be safe? Or drop? 
                # jq 'select(.rp.bn == null)' would match if rp is null OR rp.bn is null.
                # If rp exists but isn't a dict, get("bucketName") fails. 
                # Let's assume standard behavior: if we can't find the specific noise signal, keep existing.
                filtered.append(record)
                
        return filtered

    @classmethod
    def derive_output_file(cls, infile: str, output_base: str = "processed-logs-json") -> str:
        """
        Derive the output directory path based on the input directory structure.
        """
        filename = os.path.basename(infile)
        filename_match = cls.FILENAME_REGEX.match(filename)

        if filename_match:
            filename_parts = filename_match.groupdict()
            output_file = os.path.join(
                output_base,
                filename_parts["account_id"],
                filename_parts["region_name"],
                filename_parts["year"],
                filename_parts["month"],
                f"cloudtrail_{filename_parts['year']}-{filename_parts['month']}-{filename_parts['day']}.json",
            )
        else:
            sys.stderr.write(
                f"WARNING: {infile} does not have a standard file naming structure. Placing records into undated output file.\n"
            )
            output_file = os.path.join(output_base, "cloudtrail_undated.json")

        return output_file
