from sof_elk.lib.ecs import ECSField

FIELDS = [
    ECSField(
        name="apache.error.module",
        description="from sof-elk grok patterns",
        labels_type="httpdlog",
        config_mapped="6100-httpd.conf",
        ecs_source="filebeat",
        ecs_reference="https://www.elastic.co/docs/reference/beats/filebeat/exported-fields-apache",
    ),
    ECSField(
        name="apache.proxy.error.code",
        description="from sof-elk grok patterns",
        labels_type="httpdlog",
        config_mapped="6100-httpd.conf",
        ecs_source="SOF-ELK",
    ),
    ECSField(
        name="apache.proxy.error.message",
        description="from sof-elk grok patterns",
        labels_type="httpdlog",
        config_mapped="6100-httpd.conf",
        ecs_source="SOF-ELK",
    ),
]
