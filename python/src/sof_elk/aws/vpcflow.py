import sys
from .common import AWSCommon
from typing import List

class VPCFlowProcessor(AWSCommon):
    """
    Process AWS VPC Flow Logs (CloudWatch Logs format).
    """

    @classmethod
    def process_file(cls, infile: str) -> List[str]:
        """
        Process a single VPC Flow Log file and return the raw message strings.
        Output is a list of strings (the flow records).
        """
        raw_json = cls.smart_open_json(infile)
        if raw_json is None:
            return []

        # CloudWatch Logs format usually has 'events' list
        if "events" not in raw_json: # type: ignore
            sys.stderr.write(
                f"- ERROR: Input file {infile} does not appear to contain VPC Flow Logs (CloudWatch format). Skipping file.\n"
            )
            return []

        messages: List[str] = []
        for event in raw_json["events"]: # type: ignore
            if "message" in event:
                messages.append(event["message"])
        
        return messages
