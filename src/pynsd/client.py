import logging
import socket
import ssl
from pathlib import Path
from typing import Any, Callable, List, Optional, Tuple, Type, Union

from .exception import NSDCommandError, NSDConfigurationError, NSDConnectionError, NSDError, NSDTimeoutError

from .parser import Response, ResponseParser

# Set up logging
logger = logging.getLogger(__name__)

# NSD control protocol version
NSD_CONTROL_VERSION = 1

# Default buffer size for socket operations
BUFSIZE = 8192

# Default timeout for socket operations (seconds)
DEFAULT_TIMEOUT = 30.0


class Client:
    """Client for interacting with the NSD (Name Server Daemon) control interface.

    This class provides a high-level interface to communicate with NSD's control port
    using SSL/TLS for secure communication. It supports both synchronous operations
    and can be used as a context manager.

    Example:
        ```python
        with ControlClient('client.crt', 'client.key', 'nsd.example.com') as client:
            status = client.call('status')
            print(status)
        ```

    Args:
        client_cert: Path to the client certificate file (PEM format)
        client_key: Path to the client private key file (PEM format)
        host: NSD server hostname or IP address. Defaults to '127.0.0.1'
        port: NSD control port. Defaults to 8952
        bufsize: Buffer size for socket operations. Defaults to 8192
        timeout: Connection and operation timeout in seconds. Defaults to 30.0

    Raises:
        NSDConfigurationError: If certificate or key files are invalid or inaccessible
    """

    def __init__(
        self,
        client_cert: Union[str, Path],
        client_key: Union[str, Path],
        host: str = "127.0.0.1",
        port: int = 8952,
        bufsize: Optional[int] = None,
        timeout: Optional[float] = None,
        ssl_verify: bool = True,
    ) -> None:
        """Initialize the NSD control client.

        Args:
            client_cert: Path to the client certificate file (PEM format)
            client_key: Path to the client private key file (PEM format)
            host: NSD server hostname or IP address. Defaults to '127.0.0.1'
            port: NSD control port. Defaults to 8952
            bufsize: Buffer size for socket operations. Defaults to 8192
            timeout: Connection and operation timeout in seconds. Defaults to 30.0
            ssl_verify: Whether to verify the server's SSL certificate. Set to False to disable
                      certificate verification (useful for self-signed certificates). Defaults to True.
        """
        self.client_cert = Path(client_cert)
        self.client_key = Path(client_key)
        self.host = host
        self.port = port
        self._bufsize = bufsize or BUFSIZE
        self.timeout = timeout or DEFAULT_TIMEOUT
        self.ssl_verify = ssl_verify
        self.sock: Optional[ssl.SSLSocket] = None

        # Validate certificate and key files
        self._validate_cert_files()

        logger.debug("Initialized NSD client: %s:%d (cert: %s, key: %s)", self.host, self.port, self.client_cert, self.client_key)

    def _validate_cert_files(self) -> None:
        """Validate that certificate and key files exist and are accessible.

        Raises:
            NSDConfigurationError: If certificate or key files are invalid
        """
        try:
            if not self.client_cert.exists():
                raise NSDConfigurationError(f"Certificate file not found: {self.client_cert}")
            if not self.client_key.exists():
                raise NSDConfigurationError(f"Key file not found: {self.client_key}")
            # Try to read the files to verify permissions
            self.client_cert.read_bytes()
            self.client_key.read_bytes()
        except (IOError, OSError) as e:
            raise NSDConfigurationError(f"Failed to read certificate or key file: {e}") from e

    def __enter__(self) -> "Client":
        """Enter the runtime context related to this object.

        Returns:
            The ControlClient instance itself

        Example:
            ```python
            with pynsd.Client('client.crt', 'client.key') as client:
                result = client.call('status')
            ```
        """
        self.connect()
        return self

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],  # noqa: F841
        exc_val: Optional[BaseException],  # noqa: F841
        exc_tb: Any,  # noqa: F841
    ) -> None:
        """Exit the runtime context and close the connection.

        Args:
            exc_type: The exception type if an exception was raised
            exc_val: The exception value if an exception was raised
            exc_tb: The traceback if an exception was raised
        """
        self.close()

    def __del__(self) -> None:
        """Ensure the connection is closed when the object is garbage collected."""
        try:
            self.close()
        except Exception:
            # Prevent exceptions during garbage collection
            pass

    def close(self) -> None:
        """Close the connection if it's still open.

        This method is idempotent and can be called multiple times safely.
        It will attempt to gracefully shutdown the socket before closing it.
        """
        if self.sock is None:
            return

        sock = self.sock
        self.sock = None  # Clear reference first to prevent race conditions

        logger.debug("Closing connection to %s:%d", self.host, self.port)
        try:
            sock.shutdown(socket.SHUT_RDWR)
        except (OSError, socket.error) as e:
            # Ignore errors during shutdown (connection might already be closed)
            logger.debug("Error during socket shutdown: %s", e)
        finally:
            try:
                sock.close()
            except OSError as e:
                logger.debug("Error closing socket: %s", e)

    def connect(self, host: Optional[str] = None, port: Optional[int] = None) -> None:
        """Connect to the NSD control port.

        If host or port are not provided, the values from initialization are used.

        Args:
            host: Optional hostname or IP address of the NSD server
            port: Optional port number of the NSD control interface

        Raises:
            NSDConnectionError: If connection to the server fails
            NSDTimeoutError: If connection times out
            ssl.SSLError: If SSL handshake fails
            NSDError: For other connection-related errors

        Example:
            ```python
            client = pynsd.Client('client.crt', 'client.key')
            client.connect('nsd.example.com', 8953)
            ```
        """
        if host is not None:
            self.host = host
        if port is not None:
            self.port = port

        if self.sock is not None:
            logger.debug("Closing existing connection to %s:%d", self.host, self.port)
            self.close()

        logger.info("Connecting to NSD control at %s:%d", self.host, self.port)

        try:
            # Create SSL context
            context = ssl.create_default_context()
            context.load_cert_chain(certfile=str(self.client_cert), keyfile=str(self.client_key))

            # Configure SSL verification
            if not self.ssl_verify:
                logger.info("SSL certificate verification is disabled. This is not recommended for production use.")
                context.check_hostname = False
                context.verify_mode = ssl.CERT_NONE

            # Configure timeouts
            sock = socket.create_connection((self.host, self.port), timeout=self.timeout)

            # Wrap with SSL
            self.sock = context.wrap_socket(sock, server_hostname=self.host, server_side=False)

            # Set socket options
            self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
            self.sock.settimeout(self.timeout)

            logger.debug("Successfully connected to %s:%d", self.host, self.port)

        except socket.timeout as e:
            error_msg = f"Connection to {self.host}:{self.port} timed out after {self.timeout}s"
            logger.error(error_msg)
            raise NSDTimeoutError(error_msg) from e

        except (socket.gaierror, socket.herror) as e:
            error_msg = f"Failed to resolve hostname {self.host}: {e}"
            logger.error(error_msg)
            raise NSDConnectionError(error_msg) from e

        except ConnectionRefusedError as e:
            error_msg = f"Connection refused by {self.host}:{self.port} - is NSD running?"
            logger.error(error_msg)
            raise NSDConnectionError(error_msg) from e

        except ssl.SSLError as e:
            error_msg = f"SSL handshake failed: {e}"
            logger.error(error_msg)
            raise

        except OSError as e:
            error_msg = f"Failed to connect to {self.host}:{self.port}: {e}"
            logger.error(error_msg)
            raise NSDConnectionError(error_msg) from e

    def __getattr__(self, name: str) -> Callable[..., Any]:
        """Make NSD control commands callable as methods.

        This allows calling control commands as methods on the ControlClient instance,
        e.g., client.zone_status('example.com')

        Args:
            name: Name of the NSD control command

        Returns:
            A function that will call the named NSD control command

        Raises:
            AttributeError: If the attribute name is a special method name
        """
        if name.startswith("__") and name.endswith("__"):
            # Prevent infinite recursion for special methods
            raise AttributeError(name)

        def command_method(*args: Any, **kwargs: Any) -> Any:
            if kwargs:
                raise TypeError("ControlClient methods do not accept keyword arguments")
            return self.request(name, args)

        return command_method

    def _send_receive(self, command: str, args: Tuple[Any, ...] = ()) -> str:
        """Send a command to the NSD control port and return the response.

        Args:
            command: Command to send (e.g., 'status', 'reload')
            args: Optional command arguments

        Returns:
            The response from the server

        Raises:
            NSDCommandError: If the command fails on the server side
            NSDConnectionError: If connection is lost
            NSDTimeoutError: If the operation times out
            NSDError: For other errors
        """
        command_parts = [f"NSDCT{NSD_CONTROL_VERSION}", command] + [str(arg) for arg in args]
        logger.debug("Sending command: %s %s", command, command_parts)
        self._write(" ".join(command_parts) + "\n")

        # Get response
        response = self._fetch()

        return response

    def _write(self, data: Union[str, bytes]) -> None:
        """Send data to the NSD control socket.

        Args:
            data: Data to send (will be encoded to bytes if it's a string)

        Raises:
            socket.timeout: If the send operation times out
            ssl.SSLError: If an SSL error occurs
            socket.error: If a socket error occurs
        """
        if not self.sock:
            raise RuntimeError("Socket not connected")

        try:
            if isinstance(data, str):
                data = data.encode("utf-8")
            self.sock.sendall(data)
        except (socket.timeout, ssl.SSLError, socket.error):
            self.close()
            raise

    def _fetch(self) -> str:
        """Fetch the response from the NSD control socket.

        Returns:
            The response from the server as a string

        Raises:
            NSDConnectionError: If not connected or connection is lost
            NSDTimeoutError: If the operation times out
            NSDError: For other receive-related errors
        """
        if not self.sock:
            raise NSDConnectionError("Not connected to NSD control port")

        buffer: List[bytes] = []
        try:
            while True:
                try:
                    data = self.sock.recv(self._bufsize)
                    if not data:  # Connection closed by server
                        break
                    buffer.append(data)
                except socket.timeout as e:
                    error_msg = f"Read operation timed out after {self.timeout}s"
                    logger.error(error_msg)
                    raise NSDTimeoutError(error_msg) from e
                except (ConnectionResetError, BrokenPipeError) as e:
                    self.sock = None  # Mark connection as closed
                    error_msg = f"Connection lost while receiving data: {e}"
                    logger.error(error_msg)
                    raise NSDConnectionError(error_msg) from e
                except OSError as e:
                    error_msg = f"Error receiving data: {e}"
                    logger.error(error_msg)
                    raise NSDError(error_msg) from e

            # Combine all received data
            response = b"".join(buffer)
            logger.debug("Received %d bytes from %s:%d", len(response), self.host, self.port)

            # Decode to string with error handling
            try:
                return response.decode("utf-8")
            except UnicodeDecodeError as e:
                error_msg = f"Failed to decode response: {e}"
                logger.error(error_msg)
                # Return a best-effort decoded string with replacement characters
                return response.decode("utf-8", errors="replace")

        except Exception as e:
            if not isinstance(e, NSDError):
                logger.exception("Unexpected error in __fetch")
                raise NSDError(f"Failed to fetch data: {e}") from e
            raise

    def request(self, command: str, args: Tuple[Any, ...] = (), timeout: Optional[float] = None) -> Response:
        """Send a command to the NSD control port and return the response.

        Args:
            cmd: Command to send (e.g., 'status', 'reload')
            args: Optional command arguments
            timeout: Optional timeout in seconds (overrides instance timeout)

        Returns:
            Parsed response

        Raises:
            NSDCommandError: If the command fails on the server side
            NSDConnectionError: If connection is lost
            NSDTimeoutError: If the operation times out
            NSDError: For other errors
        """
        if not isinstance(command, str) or not command.strip():
            raise ValueError("Command must be a non-empty string")

        original_timeout = None
        try:
            # Ensure we're connected
            if self.sock is None:
                self.connect()

            # Set temporary timeout if specified
            if timeout is not None and self.sock is not None:
                original_timeout = self.sock.gettimeout()
                self.sock.settimeout(timeout)

            # Build and send command and get response
            response = self._send_receive(command, args)

            result = ResponseParser.parse(command, response)
            if not result.is_success():
                error_msg = f"Command '{command}' failed"
                if result.msg:
                    error_msg += f": {result.msg}"
                raise NSDCommandError(error_msg, result)
            return result

        except Exception as e:
            if not isinstance(e, NSDError):
                logger.exception("Unexpected error in call('%s')", command)
                raise NSDError(f"Failed to execute command '{command}': {e}") from e
            raise

        finally:
            # Restore original timeout if it was changed
            if original_timeout is not None and self.sock is not None:
                try:
                    self.sock.settimeout(original_timeout)
                except OSError:
                    pass  # Socket might be closed
