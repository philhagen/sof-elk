
import os
from sof_elk.api.client import SOFElkSession, SOFElkHTTPClient
from typing import Optional, List, Any, Dict

class KibanaClient:
    def __init__(self, host: str = "localhost", port: int = 5601, protocol: str = "http") -> None:
        self.base_url: str = f"{protocol}://{host}:{port}"
        self.client: SOFElkHTTPClient = SOFElkSession.get_session()
        # Common header required for Kibana 4+ (and OpenSearch Dashboards)
        self.client._session.headers.update({"kbn-xsrf": "true"})

    def _get_url(self, endpoint: str) -> str:
        return f"{self.base_url}{endpoint}"

    def find_objects(self, obj_type: str, fields: Optional[List[str]] = None, per_page: int = 10000) -> Any:
        """
        Find saved objects of a specific type.

        Args:
            obj_type (str): The type of saved object (e.g., 'index-pattern', 'visualization').
            fields (Optional[List[str]]): Specific fields to retrieve. Defaults to None (all fields).
            per_page (int): Number of results to return per page. Defaults to 10000.

        Returns:
            Any: The JSON response containing the found objects.
        """
        params: Dict[str, Any] = {
            "type": obj_type,
            "per_page": per_page
        }
        if fields:
            # multiple fields can be passed as list but requests params handles lists?
            # Kibana API expects repeated keys: fields=id&fields=title
            params["fields"] = fields

        url = self._get_url("/api/saved_objects/_find")
        response = self.client.get(url, params=params)
        return response.json()

    def get_object(self, obj_type: str, obj_id: str) -> Any:
        """
        Get a specific saved object.

        Args:
            obj_type (str): The type of saved object.
            obj_id (str): The ID of the saved object.

        Returns:
            Any: The JSON representation of the object.
        """
        url = self._get_url(f"/api/saved_objects/{obj_type}/{obj_id}")
        response = self.client.get(url)
        return response.json()

    def delete_object(self, obj_type: str, obj_id: str) -> Any:
        """
        Delete a specific saved object.

        Args:
            obj_type (str): The type of saved object.
            obj_id (str): The ID of the saved object.

        Returns:
            Any: The JSON response.
        """
        url = self._get_url(f"/api/saved_objects/{obj_type}/{obj_id}")
        response = self.client.delete(url)
        return response.json()

    def import_objects(self, file_path: str, overwrite: bool = True) -> Any:
        """
        Import saved objects from an ndjson file.

        Args:
            file_path (str): Local path to the ndjson file.
            overwrite (bool): Whether to overwrite existing objects. Defaults to True.

        Returns:
            Any: The JSON response from the import API.
        """
        url = self._get_url("/api/saved_objects/_import")
        params = {"overwrite": str(overwrite).lower()}
        
        with open(file_path, 'rb') as f:
            files = {'file': (os.path.basename(file_path), f, 'application/ndjson')}
            response = self.client.post(url, files=files, params=params)
        return response.json()

    def get_data_views(self) -> Any:
        """
        Get all data views (index patterns).

        Returns:
            Any: The JSON response containing all data views.
        """
        url = self._get_url("/api/data_views") # Check endpoint version/compatibility?
        # The script used /api/data_views?per_page=10000
        response = self.client.get(url, params={"per_page": 10000})
        return response.json()

    def __repr__(self) -> str:
        return f"<KibanaClient {self.base_url}>"
