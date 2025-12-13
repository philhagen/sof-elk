class SOFElkAPIError(Exception):
    """Base exception for SOF-ELK API errors."""

    pass


class SOFElkTimeOutError(SOFElkAPIError):
    """Raised when an API request times out."""

    pass


class SOFElkConnectionError(SOFElkAPIError):
    """Raised when connection to the API fails."""

    pass


class SOFElkResponseError(SOFElkAPIError):
    """Raised when the API returns a non-success status code."""

    def __init__(self, message: str, status_code: int | None = None, response_body: str | None = None):
        super().__init__(message)
        self.status_code = status_code
        self.response_body = response_body
