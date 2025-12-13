from sof_elk.lib.ecs import ECSField

FIELDS = [
    ECSField(
        name="threat.software.name",
        labels_type="plaso",
        config_mapped="6601-plaso.conf",
        ecs_source="ECS",
        ecs_reference="https://www.elastic.co/docs/reference/ecs/ecs-threat#field-threat-software-name",
    ),
]
