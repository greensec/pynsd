import re
from typing import Any, Dict, List, Optional, Pattern, Tuple, Union


class Response:
    """Generic result class for NSD control command responses."""

    success: Optional[bool] = None
    msg: Optional[List[str]] = None
    data: Optional[Dict[str, Any]] = None

    def __init__(self, data: Dict[str, Any]) -> None:
        """Initialize with response data.

        Args:
            data: Dictionary containing response data with keys:
                - success: Boolean indicating success
                - msg: Optional message
                - result: Optional result data
        """

        if "success" in data:
            self.success = data["success"]
        if "msg" in data:
            self.msg = data["msg"]
        if "result" in data:
            self.data = data["result"]

    def is_success(self) -> bool:
        """Check if the command was successful.

        Returns:
            bool: True if the command was successful, False otherwise
        """
        return bool(self.success)

    def get_message(self) -> Optional[List[str]]:
        """Get the message from the command response.

        Returns:
            Optional list of message lines, or None if no message
        """
        return self.msg

    def get_data(self) -> Optional[Dict[str, Any]]:
        """Get the data from the command response.

        Returns:
            Optional dictionary containing the result data, or None if no data
        """
        return self.data

    def to_dict(self) -> Dict[str, Any]:
        """Convert the result to a dictionary.

        Returns:
            Dictionary containing the result data
        """
        return {"msg": self.msg, "success": self.success, "data": self.data}

    def __repr__(self) -> str:
        return f"ControlResult({self.to_dict()!r})"

    def __str__(self) -> str:
        return str(self.to_dict())


class ResponseParser:
    """Parser for NSD control protocol responses."""

    # Regular expressions for parsing key-value pairs
    KEY_VALUE_RE: Pattern = re.compile(r"^([^:]+):\s*(.+)$", re.MULTILINE)
    KEY_VALUE_V2_RE: Pattern = re.compile(r"^([^=]+)=\s*(.+)$", re.MULTILINE)

    # Commands that typically just return "ok"
    OK_COMMANDS: Tuple[str, ...] = (
        "addzone",
        "delzone",
        "reconfig",
        "log_reopen",
        "notify",
    )

    @classmethod
    def parse(cls, cmd: str, data: Union[bytes, str]) -> Response:
        """Parse the response from an NSD control command.

        Args:
            cmd: The command that was executed
            data: The response data (as bytes or string)

        Returns:
            Response: Parsed result object
        """
        return Response(cls._parse(cmd, data))

    @classmethod
    def _parse(cls, cmd: str, data: Union[bytes, str]) -> Dict[str, Any]:
        """Internal method to parse command response data.

        Args:
            cmd: The command that was executed
            data: The response data (as bytes or string)

        Returns:
            Dictionary containing the parsed response
        """
        if not data or not cmd:
            return {"success": False, "msg": ["No data or command provided"]}

        # Convert bytes to string if needed
        if isinstance(data, bytes):
            try:
                data = data.decode("utf-8")
            except UnicodeDecodeError:
                data = data.decode("utf-8", errors="replace")

        if cmd == "status":
            return cls._parse_status(data)
        elif cmd in ("stats", "stats_noreset"):
            return cls._parse_stats(data)
        elif cmd in ("transfer", "force_transfer"):
            return cls._parse_transfer(data)
        elif cmd in cls.OK_COMMANDS:
            return cls._parse_ok(data)

        return {"msg": data.strip().split("\n"), "success": None}

    @classmethod
    def _parse_status(cls, data: str) -> Dict[str, Any]:
        """Parse the response from the 'status' command.

        Args:
            data: The response data as a string

        Returns:
            Dictionary containing the parsed status
        """
        result: Dict[str, Any] = {"success": False, "result": {}}

        for key, value in cls.KEY_VALUE_RE.findall(data):
            result["result"][key] = value

        if "version" in result["result"]:
            result["success"] = True

        return result

    @classmethod
    def _parse_stats(cls, data: str) -> Dict[str, Any]:
        """Parse the response from the 'stats' or 'stats_noreset' command.

        Args:
            data: The response data as a string

        Returns:
            Dictionary containing the parsed statistics
        """
        result: Dict[str, Any] = {"success": False, "result": {}}

        for key, value in cls.KEY_VALUE_V2_RE.findall(data):
            result["result"][key] = value

        if "time.elapsed" in result["result"]:
            result["success"] = True

        return result

    @staticmethod
    def _parse_ok(data: str) -> Dict[str, Any]:
        """Parse a simple 'ok' response.

        Args:
            data: The response data as a string

        Returns:
            Dictionary with success status and message
        """
        lines = [line.strip() for line in data.strip().split("\n") if line.strip()]
        is_ok = any(line == "ok" or line.startswith("ok,") for line in lines)

        return {"msg": lines, "success": is_ok}

    @classmethod
    def _parse_transfer(cls, data: str) -> Dict[str, Any]:
        """Parse the response from the 'transfer' or 'force_transfer' command.

        Args:
            data: The response data as a string

        Returns:
            Dictionary containing the transfer result
        """
        result = cls._parse_ok(data)
        result["zones"] = None

        if result["success"]:
            match = re.search(r"(\d+)\s+zones", data, re.IGNORECASE)
            if match:
                try:
                    result["zones"] = int(match.group(1))
                except (ValueError, IndexError):
                    pass

        return result
