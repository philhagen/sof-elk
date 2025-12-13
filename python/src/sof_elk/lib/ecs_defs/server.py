from sof_elk.lib.ecs import ECSField

FIELDS = [
    ECSField(
        name="server.user.name",
        labels_type="httpdlog",
        config_mapped="6100-httpd.conf",
        ecs_source="SOF-ELK",
    ),
    ECSField(
        name="server.user.name",
        labels_type="zeek_http",
        config_mapped="6201-zeek_http.conf",
        ecs_source="SOF-ELK",
    ),
]
