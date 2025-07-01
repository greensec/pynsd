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
        "reload",
        "stop",
        "repattern",
        "write",
        "verbosity",
        "update_tsig",
        "add_tsig",
        "del_tsig",
        "assoc_tsig",
        "add_cookie_secret",
        "drop_cookie_secret",
        "activate_cookie_secret",
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
                data = data.decode("ascii")
            except UnicodeDecodeError:
                data = data.decode("ascii", errors="replace")

        # Strip any whitespace
        data = data.strip()

        # Route to appropriate parser based on command
        if cmd == "status":
            return cls._parse_status(data)
        elif cmd in ("stats", "stats_noreset"):
            return cls._parse_stats(data)
        elif cmd in ("transfer", "force_transfer"):
            return cls._parse_transfer(data)
        elif cmd == "zonestatus":
            return cls._parse_zonestatus(data)
        elif cmd == "print_tsig":
            return cls._parse_tsig_info(data)
        elif cmd == "print_cookie_secrets":
            return cls._parse_cookie_secrets(data)
        elif cmd in cls.OK_COMMANDS:
            return cls._parse_ok(data)

        # Default case for unknown commands
        return {"msg": data.split("\n") if data else [], "success": None}

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
            match = re.search(r"(\d+)\s+zones?\b", data, re.IGNORECASE)
            if match:
                try:
                    result["zones"] = int(match.group(1))
                except (ValueError, IndexError):
                    pass

        return result

    @classmethod
    def _parse_zonestatus(cls, data: str) -> Dict[str, Any]:
        """Parse the response from the 'zonestatus' command.

        Args:
            data: The response data as a string

        Returns:
            Dictionary containing the zone status information
        """
        result: Dict[str, Any] = {"success": False, "result": {}}
        current_zone = None

        for line in data.split("\n"):
            line = line.strip()
            if not line:
                continue

            # New zone section starts with zone name
            if ":" not in line and "=" not in line and not line.startswith("["):
                current_zone = line.strip()
                result["result"][current_zone] = {}
            elif current_zone and ":" in line:
                key, value = line.split(":", 1)
                result["result"][current_zone][key.strip()] = value.strip()

        result["success"] = bool(result["result"])
        return result

    @classmethod
    def _parse_tsig_info(cls, data: str) -> Dict[str, Any]:
        """Parse the response from the 'print_tsig' command.

        Args:
            data: The response data as a string

        Returns:
            Dictionary containing TSIG key information
        """
        result: Dict[str, Any] = {"success": True, "result": {}}
        current_key = None

        for line in data.split("\n"):
            line = line.strip()
            if not line:
                continue

            # New TSIG key section
            if ":" not in line:
                current_key = line.strip()
                result["result"][current_key] = {}
            elif current_key and ":" in line:
                key, value = line.split(":", 1)
                result["result"][current_key][key.strip()] = value.strip()

        return result

    @classmethod
    def _parse_cookie_secrets(cls, data: str) -> Dict[str, Any]:
        """Parse the response from the 'print_cookie_secrets' command.

        Args:
            data: The response data as a string

        Returns:
            Dictionary containing cookie secret information
        """
        result: Dict[str, Any] = {"success": True, "result": []}

        for line in data.split("\n"):
            line = line.strip()
            if not line or "=" not in line:
                continue

            secret, status = line.split("=", 1)
            result["result"].append({"secret": secret.strip(), "status": status.strip()})

        return result
