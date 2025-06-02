from pathlib import Path

from .client import ControlClient
from .parser import ControlResultParser

# Read version from VERSION file
version_file = Path(__file__).parent.parent.parent / "VERSION"
__version__ = version_file.read_text().strip()

# For backward compatibility
__all__ = ["ControlClient", "ControlResultParser"]
