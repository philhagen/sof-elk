from dataclasses import dataclass
from typing import Optional

@dataclass
class ECSField:
    """
    Represents a field in the Elastic Common Schema (ECS) definition.
    """
    name: str
    description: Optional[str] = None
    labels_type: Optional[str] = None
    field_type: Optional[str] = None
    config_mapped: Optional[str] = None
    ecs_source: Optional[str] = None
    ecs_reference: Optional[str] = None

    def to_csv_row(self) -> dict:
        """
        Converts the ECSField instance to a dictionary suitable for CSV writing.

        Returns:
            A dictionary where keys match the expected CSV headers.
        """
        return {
            "Field Name": self.name,
            "Description": self.description or "",
            "labels.type": self.labels_type or "",
            "Field Type": self.field_type or "",
            "Configuration File Where Mapped": self.config_mapped or "",
            "ECS Field Source": self.ecs_source or "",
            "ECS Reference": self.ecs_reference or "",
        }

def generate_csv(output_path: str) -> bool:
    """
    Generates the ECS fields CSV file from the internal Python definitions.
    """
    import csv
    from sof_elk.lib.ecs_defs import ALL_ECS_FIELDS

    fieldnames = [
        "Field Name", "Description", "labels.type", "Field Type", 
        "Configuration File Where Mapped", "ECS Field Source", "ECS Reference"
    ]

    try:
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            # Sort by name for consistency
            sorted_fields = sorted(ALL_ECS_FIELDS, key=lambda x: x.name)
            
            for field in sorted_fields:
                writer.writerow(field.to_csv_row())
        return True
    except Exception as e:
        print(f"Error generating CSV: {e}")
        return False
