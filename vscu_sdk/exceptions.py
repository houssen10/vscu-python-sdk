from typing import Optional, Any


class VscuException(Exception):
    """Exception raised when an error occurs while communicating with the VSCU API."""

    def __init__(self, message: str, status_code: Optional[int] = None, response_data: Optional[Any] = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.response_data = response_data

    def __str__(self) -> str:
        if self.status_code:
            return f"[Status {self.status_code}] {self.message}"
        return self.message
