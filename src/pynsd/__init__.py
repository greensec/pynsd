from pathlib import Path

from .client import Client
from .parser import ResponseParser, Response
from .exception import NSDCommandError, NSDConfigurationError, NSDConnectionError, NSDError, NSDTimeoutError

# Read version from VERSION file
version_file = Path(__file__).parent / "VERSION"
__version__ = version_file.read_text().strip()
