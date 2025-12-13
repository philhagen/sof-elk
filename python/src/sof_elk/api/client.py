from typing import Any

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from sof_elk.api.custom_exceptions import SOFElkConnectionError, SOFElkResponseError, SOFElkTimeOutError

DEFAULT_TIMEOUT = 30  # seconds


class SOFElkSession:
    """
    Factory for creating a `requests.Session` with resilient defaults for API interactions.
    """

    @staticmethod
    def get_session(
        retries: int = 3, backoff_factor: float = 0.3, status_forcelist: tuple[int, ...] = (500, 502, 503, 504)
    ) -> "SOFElkHTTPClient":
        """
        Returns a configured `SOFElkHTTPClient` wrapper around `requests.Session`.

        Args:
            retries (int): Total number of retries to allow. Defaults to 3.
            backoff_factor (float): A backoff factor to apply between attempts. Defaults to 0.3.
            status_forcelist (Tuple[int, ...]): A set of HTTP status codes that we should force a retry on.

        Returns:
            SOFElkHTTPClient: A client instance with valid retry and timeout logic.
        """
        session = requests.Session()

        retry = Retry(
            total=retries,
            read=retries,
            connect=retries,
            backoff_factor=backoff_factor,  # type: ignore
            status_forcelist=status_forcelist,
        )

        adapter = HTTPAdapter(max_retries=retry)
        session.mount("http://", adapter)
        session.mount("https://", adapter)

        # Hook to enforce timeout if not provided per request
        # requests.Session() doesn't have a global timeout property, so we hook request()
        # simplified: We can wrap the session or just expect usage of this client helper.
        # Better: Create a wrapper class that behaves like a session but enforces timeout.

        return SOFElkHTTPClient(session)


class SOFElkHTTPClient:
    """
    Wrapper around `requests.Session` to enforce application-specific logic like timeouts and custom exception handling.

    Args:
        session (requests.Session): The underlying requests session.
    """

    def __init__(self, session: requests.Session) -> None:
        self._session: requests.Session = session
        self._timeout: int = DEFAULT_TIMEOUT

    def request(self, method: str, url: str, **kwargs: Any) -> requests.Response:
        """
        Wraps `session.request` with default timeout and centralized error handling.

        Args:
            method (str): HTTP method (e.g., 'GET', 'POST').
            url (str): Target URL.
            **kwargs: Additional arguments passed to `requests.Session.request`.

        Returns:
            requests.Response: The HTTP response.

        Raises:
            SOFElkResponseError: If the server returns a 4xx/5xx status code.
            SOFElkTimeOutError: If the request times out.
            SOFElkConnectionError: If the connection fails.
        """
        kwargs.setdefault("timeout", self._timeout)

        try:
            response = self._session.request(method, url, **kwargs)
            try:
                response.raise_for_status()
            except requests.exceptions.HTTPError as e:
                raise SOFElkResponseError(
                    f"HTTP Error: {e}", status_code=response.status_code, response_body=response.text
                ) from e
            return response
        except requests.exceptions.Timeout as e:
            raise SOFElkTimeOutError(f"Request timed out contacting {url}") from e
        except requests.exceptions.ConnectionError as e:
            raise SOFElkConnectionError(f"Failed to connect to {url}") from e
        except requests.exceptions.RequestException as e:
            raise SOFElkResponseError(f"An unexpected error occurred: {e}") from e

    def get(self, url: str, **kwargs: Any) -> requests.Response:
        return self.request("GET", url, **kwargs)

    def post(self, url: str, **kwargs: Any) -> requests.Response:
        return self.request("POST", url, **kwargs)

    def put(self, url: str, **kwargs: Any) -> requests.Response:
        return self.request("PUT", url, **kwargs)

    def delete(self, url: str, **kwargs: Any) -> requests.Response:
        return self.request("DELETE", url, **kwargs)

    def head(self, url: str, **kwargs: Any) -> requests.Response:
        return self.request("HEAD", url, **kwargs)

    def download_file(self, url: str, target_path: str, chunk_size: int = 8192) -> bool:
        """
        Downloads a file from a URL to a local path, streaming in chunks.

        Creates the target directory if it does not exist.

        Args:
            url (str): The source URL.
            target_path (str): The local destination path.
            chunk_size (int): Size of chunks to read. Defaults to 8192.

        Returns:
            bool: True if successful.

        Raises:
            SOFElkResponseError: If download fails.
        """
        # Ensure directory exists
        import os

        os.makedirs(os.path.dirname(os.path.abspath(target_path)), exist_ok=True)

        try:
            with self._session.get(url, stream=True, timeout=self._timeout) as r:
                r.raise_for_status()
                with open(target_path, "wb") as f:
                    for chunk in r.iter_content(chunk_size=chunk_size):
                        if chunk:  # filter out keep-alive new chunks
                            f.write(chunk)
            return True
        except Exception as e:
            # Wrap in our exception or re-raise
            raise SOFElkResponseError(f"Failed to download {url}: {e}") from e
