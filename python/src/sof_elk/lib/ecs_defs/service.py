from sof_elk.lib.ecs import ECSField

FIELDS = [
    ECSField(
        name="service.name",
        labels_type="httpdlog",
        config_mapped="6100-httpd.conf",
        ecs_source="ECS",
        ecs_reference="https://www.elastic.co/docs/reference/ecs/ecs-service#field-service-name",
    ),
]
