from sof_elk.lib.ecs import ECSField

FIELDS = [
    ECSField(
        name="host.boot.id",
        labels_type="appleul",
        config_mapped="6060-appleul.conf",
        ecs_source="ECS",
        ecs_reference="https://www.elastic.co/docs/reference/ecs/ecs-host#field-host-boot-id",
    ),
    ECSField(
        name="host.hostname",
        labels_type="aws",
        config_mapped="6901-aws.conf",
        ecs_source="ECS",
        ecs_reference="https://www.elastic.co/docs/reference/ecs/ecs-host#field-host-hostname",
    ),
    ECSField(
        name="host.hostname",
        labels_type="azure",
        config_mapped="6801-azure.conf",
        ecs_source="ECS",
        ecs_reference="https://www.elastic.co/docs/reference/ecs/ecs-host#field-host-hostname",
    ),
    ECSField(
        name="host.hostname",
        labels_type="httpdlog",
        config_mapped="6100-httpd.conf",
        ecs_source="ECS",
        ecs_reference="https://www.elastic.co/docs/reference/ecs/ecs-host#field-host-hostname",
    ),
    ECSField(
        name="host.hostname",
        description="copy of winlog.computer_name",
        labels_type="plaso",
        config_mapped="6601-plaso.conf",
        ecs_source="ECS",
        ecs_reference="https://www.elastic.co/docs/reference/ecs/ecs-host#field-host-hostname",
    ),
    ECSField(
        name="host.hostname",
        description="copy of winlog.computer_name",
        labels_type="syslog",
        config_mapped="6010-snare.conf",
        ecs_source="ECS",
        ecs_reference="https://www.elastic.co/docs/reference/ecs/ecs-host#field-host-hostname",
    ),
]
