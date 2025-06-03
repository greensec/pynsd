# Custom Exceptions
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .parser import Response


class NSDError(Exception):
    """Base exception for all NSD-related errors."""


class NSDConnectionError(NSDError):
    """Raised when a connection to the NSD server fails."""


class NSDTimeoutError(NSDError):
    """Raised when a connection or operation times out."""


class NSDCommandError(NSDError):
    """Raised when an NSD command fails."""

    def __init__(self, message: str, response: Optional["Response"] = None):
        self.response = response
        super().__init__(message)


class NSDConfigurationError(NSDError):
    """Raised when there's an error in the client configuration."""
