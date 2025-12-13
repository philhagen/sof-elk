from typing import Any

from elasticsearch import Elasticsearch


def get_es_client(host: str = "localhost", port: int = 9200, timeout: int = 300) -> Elasticsearch:
    """
    Returns a configured Elasticsearch client.

    Args:
        host (str): Elasticsearch host. Defaults to "localhost".
        port (int): Elasticsearch port. Defaults to 9200.
        timeout (int): Request timeout in seconds. Defaults to 300.

    Returns:
        Elasticsearch: configured client instance.
    """
    return Elasticsearch([{"host": host, "port": port}], request_timeout=timeout)


class ElasticsearchManagement:
    """
    Handler for administrative Elasticsearch tasks such as index management and template maintenance.
    """

    def __init__(self, es_client: Elasticsearch | None = None, host: str = "localhost", port: int = 9200) -> None:
        if es_client:
            self.es: Elasticsearch = es_client
        else:
            self.es: Elasticsearch = get_es_client(host=host, port=port)

    def force_merge(self, index: str, only_expunge_deletes: bool = False) -> Any:
        """
        Perform a force merge on an index.

        Args:
            index (str): The index name or pattern to merge.
            only_expunge_deletes (bool): If True, only expunge deletes. Defaults to False.
        """
        return self.es.indices.forcemerge(index=index, only_expunge_deletes=only_expunge_deletes)

    def delete_index(self, index: str) -> Any:
        """
        Delete an index or pattern.

        Args:
            index (str): The index name or pattern to delete.
        """
        try:
            return self.es.indices.delete(index=index)
        except Exception:  # NotFoundError usually, but catching broadly for now or import it
            return None

    def list_indices(self, pattern: str = "*", format: str = "json") -> Any:
        """
        List indices matching a specific pattern (wrapper for _cat/indices).

        Args:
            pattern (str): Index pattern to search for. Defaults to "*".
            format (str): Output format (e.g., 'json', 'text'). Defaults to "json".

        Returns:
            Any: The list of indices in the requested format.
        """
        return self.es.cat.indices(index=pattern, format=format, v=True)

    def delete_template(self, name: str) -> Any:
        """
        Delete a legacy index template.

        Args:
            name (str): The name of the template to delete.
        """
        try:
            return self.es.indices.delete_template(name=name)
        except Exception:
            return None

    def get_template(self, name: str) -> Any:
        """
        Get a legacy index template.

        Args:
            name (str): The name of the template to retrieve.
        """
        return self.es.indices.get_template(name=name)
