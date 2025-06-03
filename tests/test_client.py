"""Unit tests for the NSD control client."""
import os
import socket
import ssl
import tempfile
import unittest
from unittest.mock import MagicMock, patch

from pynsd.client import Client, NSD_CONTROL_VERSION
from pynsd.exception import (
    NSDCommandError,
    NSDConfigurationError,
    NSDConnectionError,
    NSDTimeoutError,
)


class TestControlClient(unittest.TestCase):
    """Test cases for the ControlClient class."""

    def setUp(self):
        """Set up test fixtures."""
        # Create temporary certificate and key files
        self.cert_file = tempfile.NamedTemporaryFile(delete=False)
        self.key_file = tempfile.NamedTemporaryFile(delete=False)
        self.cert_file.write("""-----BEGIN CERTIFICATE-----
MIICyjCCAbKgAwIBAgIURsQgm3LbroeyLy4W/PmuOZYAuJkwDQYJKoZIhvcNAQEL
BQAwDzENMAsGA1UEAwwEbWludDAeFw0yMTA2MTkxNjU3MDFaFw0zMTA2MTcxNjU3
MDFaMA8xDTALBgNVBAMMBG1pbnQwggEiMA0GCSqGSIb3DQEBAQUAA4IBDwAwggEK
AoIBAQDPlm2U54OoXxjCdAxPmKBLpqnRznBPlzw8syp99ni5QSfa5u3XcIhZQMmq
n9umHbSfubt4pYc4dmfO+3tGtFrpB5QuseFDMnJUuc995Cr9tpKGR7B2fdvdIiFi
33wLUYmSLZEqmkkggn3FtHoIJOUYxGMONbk7QLOEmcOE6J+bcVyeAlLWi/0i9U8i
1yvpAyTuXDpepy/Kq2Ux46W3FYUSVjy4Atc0gylsl1C2cocSK8nTYRc8sPh+uku6
jWP9BwEM8LQQ+A3Hu2tkDApTgcQLrGLXysi97dJ0tf6v0jxDcbbVKlHSXLFVjRiR
s3NB0vciI7LcOng43x5m253C+FhlAgMBAAGjHjAcMAkGA1UdEwQCMAAwDwYDVR0R
BAgwBoIEbWludDANBgkqhkiG9w0BAQsFAAOCAQEAgJXPgdLtcZDzPRWEC4gG8wAQ
Grj6VYhklZauB5F9SVHHBJGAftOTGyAg/Dv1GqkYz6rZogClAUQHgDE2oH8Rq/J0
4rFQi8yl0plArxPeGacuQsP46zKrkWQE5s/+BjvztA7egB08kZm4zAUaaHijsTaJ
n6fASGLdsBfBhIUVuph2SMQksfM3Fs6JZp7Kx44D/JZGslK6DN+WyettyK9DjJzc
EV19vFM+MwR62dNqZKgEY3gLJmAaSf/z++x0I52OK+JA/dPPDgyOBlOsZ6E2+hpq
5e1QKCsAL/ZfiXSoVoNHDvH9jTGZkIWyGznYkEktTL/wJeLl30bT1IJIbwQUQQ==
-----END CERTIFICATE-----
""".encode('ascii'))
        self.key_file.write("""-----BEGIN PRIVATE KEY-----
MIIEvwIBADANBgkqhkiG9w0BAQEFAASCBKkwggSlAgEAAoIBAQDPlm2U54OoXxjC
dAxPmKBLpqnRznBPlzw8syp99ni5QSfa5u3XcIhZQMmqn9umHbSfubt4pYc4dmfO
+3tGtFrpB5QuseFDMnJUuc995Cr9tpKGR7B2fdvdIiFi33wLUYmSLZEqmkkggn3F
tHoIJOUYxGMONbk7QLOEmcOE6J+bcVyeAlLWi/0i9U8i1yvpAyTuXDpepy/Kq2Ux
46W3FYUSVjy4Atc0gylsl1C2cocSK8nTYRc8sPh+uku6jWP9BwEM8LQQ+A3Hu2tk
DApTgcQLrGLXysi97dJ0tf6v0jxDcbbVKlHSXLFVjRiRs3NB0vciI7LcOng43x5m
253C+FhlAgMBAAECggEBAMgx135qA2OGSpeFWTYOCFDM6ytGPrPTMymK1CjkYKqw
NmJ6oNdLVINW4uXlAuxh64a6lRyV7iE6t4Q6rTmTx7TCNVsO+yJV7ULea0eKmxdR
Ul+jlX/Agx/wwWfcBYHY4aaSwVPntSxgDDF1itZ91l8bTjgvAXMuQ7JWo+NygDJj
1XnwI5k0QHTvfi6J4V78ljYhCAka524jn7ESKnLI90GzomLyYJLHyn9+sJu8L3RR
A/6IaJwJ2xu+Uoh1lG2OYtmOnzGX4xTG4WeugmdGoG9MPO2XYqrFZRAg6DoTIT9g
gArvMpc571RESnAmip9pRnHD4btWHDyBMNzuuU7IUCUCgYEA6E6fnBs/wFW+8c+F
JAEFKiLpCnYnaM8c3OPNhFnXaVXt4cRWOI19KSGdU+FaoiGS9f05/bQAm5ECeT3Z
cQ2gS8M84Z9Ufc2M+DNtgYaIHsoS4S7oqZqDqdq7gEJ9/NqO5rHUygs0sHm7Qggd
3jXe7ZJXRFudZ60qovFN7sgVIqsCgYEA5MJlNvzJMvM/BykKq6uNNeZgVOiOW1BL
uq1zWmksbIgNVVsYW/5iy60ux9jL2LSZlnQ1F+uIs1N7z0zhAKIZa4idsxWjCo2V
0g2SN3XqNeGvwCaNDaCtqOzoRw/Jadorc7J1oc3rGkx1vYUnOITEJDeuDi2QXkRj
HZLS2ARc8S8CgYEA16ILk9rTTVQKXujS3D26LoejK5vLLwV49CzcWusOAe/KVNNr
eSkUsbZLFE5NU8u4X2/DgZSxL7Xlxua7TK5qSYkbnQ7JXdEL9mO+VQmslm/aIH3r
Z2tOpb6sZvzRd4DkPo15SGYobVtBj6R7HQWCPaGmMYSc0lyyA/fa8Dd3LusCgYEA
2DX74ArwR12stqHN2g+cudLyPY5H7npn+RqzKkK5oCK/J2ugDGLVEdivnGeF015u
w8s121PcslE3dekdyLFtATvwgTD0FqdXcV8uUYj7Qs36hMxrCPRS7pRrva5oGcoA
w6tqjvHHQeX+apANT9f8YpbVxcS+7LoKTAtXiKAnEDUCgYBCNgKgSeuvXkoDkA9j
W0YDvs43aehPbzcSxM/criXSRNe43+uypDlq09tRbb24YsyT8bIA8R7jjm65LJEj
uSMFknZXtGmLVOhe5X5QAlU3Kcg9UglCLsw6hTSrYazsXdyIZbvl7Flvc/foIUw1
qwaypVfkTx0BLFSyO1fFxtfObA==
-----END PRIVATE KEY-----
""".encode('ascii'))
        self.cert_file.close()
        self.key_file.close()

        # Default client parameters
        self.host = "test.example.com"
        self.port = 12345

    def tearDown(self):
        """Clean up test fixtures."""
        # Remove temporary files
        os.unlink(self.cert_file.name)
        os.unlink(self.key_file.name)

    def create_client(self, **kwargs):
        """Create a ControlClient instance with test defaults."""
        params = {
            "client_cert": self.cert_file.name,
            "client_key": self.key_file.name,
            "host": self.host,
            "port": self.port,
        }
        params.update(kwargs)
        return Client(**params)

    @patch('ssl.create_default_context')
    def test_connect_with_ssl_verify_false(self, mock_ssl_context):
        """Test connection with SSL verification disabled."""
        # Setup mocks
        mock_context = MagicMock()
        mock_ssl_context.return_value = mock_context
        
        # Create client with ssl_verify=False
        client = self.create_client(ssl_verify=False)
        
        # Mock the socket connection
        mock_socket = MagicMock()
        mock_connect = MagicMock(return_value=mock_socket)
        
        with patch('socket.create_connection', mock_connect):
            # Configure the wrap_socket mock
            mock_ssl_socket = MagicMock()
            mock_context.wrap_socket.return_value = mock_ssl_socket
            
            # Test connection
            client.connect()
            
            # Verify SSL context was configured to skip verification
            mock_ssl_context.assert_called_once()
            self.assertFalse(mock_context.check_hostname)
            self.assertEqual(mock_context.verify_mode, ssl.CERT_NONE)
            
            # Verify the rest of the connection process
            mock_connect.assert_called_once_with((self.host, self.port), timeout=client.timeout)
            mock_context.wrap_socket.assert_called_once_with(
                mock_socket, server_hostname=self.host, server_side=False
            )
            mock_ssl_socket.setsockopt.assert_any_call(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
            mock_ssl_socket.settimeout.assert_called_with(client.timeout)
            self.assertEqual(client.sock, mock_ssl_socket)

    @patch("ssl.SSLContext.wrap_socket")
    @patch("socket.create_connection")
    def test_connect_success(self, mock_connect, mock_wrap_socket):
        """Test successful connection to the NSD server."""
        # Setup mocks
        mock_socket = MagicMock()
        mock_connect.return_value = mock_socket
        mock_ssl_socket = MagicMock()
        mock_wrap_socket.return_value = mock_ssl_socket

        # Test
        client = self.create_client()
        client.connect()

        # Verify
        mock_connect.assert_called_once_with(
            (self.host, self.port), timeout=client.timeout
        )
        self.assertEqual(client.sock, mock_ssl_socket)

    @patch("ssl.SSLContext.wrap_socket")
    @patch("socket.create_connection")
    @patch('ssl.SSLContext')
    def test_connect_timeout(self, mock_ssl_ctx, mock_connect, mock_wrap_socket):
        """Test connection timeout handling."""
        mock_ssl_ctx.return_value = MagicMock()
        mock_connect.side_effect = socket.timeout("Connection timed out")
        client = self.create_client()

        with self.assertRaises(NSDTimeoutError):
            client.connect()

    def test_validate_cert_files_missing_cert(self):
        """Test validation fails when certificate file is missing."""
        with tempfile.NamedTemporaryFile() as temp_file:
            # Use a non-existent cert file
            with self.assertRaises(NSDConfigurationError):
                client = Client(
                    client_cert="/nonexistent/cert.pem",
                    client_key=temp_file.name,
                )
                client._validate_cert_files()

    def test_validate_cert_files_missing_key(self):
        """Test validation fails when key file is missing."""
        with tempfile.NamedTemporaryFile() as temp_file:
            with self.assertRaises(NSDConfigurationError):
                # Use a non-existent key file
                client = Client(
                    client_cert=temp_file.name,
                    client_key="/nonexistent/key.pem",
                )
                client._validate_cert_files()

    @patch("ssl.SSLContext.wrap_socket")
    @patch("socket.create_connection")
    def test_context_manager(self, mock_connect, mock_wrap_socket):
        """Test using ControlClient as a context manager."""
        mock_socket = MagicMock()
        mock_connect.return_value = mock_socket
        mock_ssl_socket = MagicMock()
        mock_wrap_socket.return_value = mock_ssl_socket

        with self.create_client() as client:
            self.assertIsNotNone(client.sock)

        # Should call close() when exiting the context
        mock_ssl_socket.shutdown.assert_called_once_with(socket.SHUT_RDWR)
        mock_ssl_socket.close.assert_called_once()

    @patch("ssl.SSLContext.wrap_socket")
    @patch("socket.create_connection")
    def test_close(self, mock_connect, mock_wrap_socket):
        """Test closing the connection."""
        mock_socket = MagicMock()
        mock_connect.return_value = mock_socket
        mock_ssl_socket = MagicMock()
        mock_wrap_socket.return_value = mock_ssl_socket

        client = self.create_client()
        client.connect()
        client.close()

        mock_ssl_socket.shutdown.assert_called_once_with(socket.SHUT_RDWR)
        mock_ssl_socket.close.assert_called_once()
        self.assertIsNone(client.sock)

    @patch("ssl.SSLContext.wrap_socket")
    @patch("socket.create_connection")
    def test_request_success(self, mock_connect, mock_wrap_socket):
        """Test successful command request."""
        # Setup mocks
        mock_socket = MagicMock()
        mock_connect.return_value = mock_socket
        mock_ssl_socket = MagicMock()
        mock_wrap_socket.return_value = mock_ssl_socket
        mock_ssl_socket.recv.side_effect = [b"ok\n", b""]

        # Test
        client = self.create_client()
        response = client.request("notify", ("example.com",))

        # Verify
        expected_command = f"NSDCT{NSD_CONTROL_VERSION} notify example.com\n"
        mock_ssl_socket.sendall.assert_called_once_with(expected_command.encode("utf-8"))
        self.assertEqual(response.is_success(), True)
        self.assertEqual(response.msg, ["ok"])
        self.assertIsNone(response.data)

    @patch("ssl.SSLContext.wrap_socket")
    @patch("socket.create_connection")
    def test_request_with_args(self, mock_connect, mock_wrap_socket):
        """Test command request with arguments."""
        # Setup mocks
        mock_socket = MagicMock()
        mock_connect.return_value = mock_socket
        mock_ssl_socket = MagicMock()
        mock_wrap_socket.return_value = mock_ssl_socket
        mock_ssl_socket.recv.side_effect = [b"ok\n", b""]

        # Test
        client = self.create_client()
        response = client.request("addzone", ("example.com", "example.zone"))

        # Verify
        expected_command = f"NSDCT{NSD_CONTROL_VERSION} addzone example.com example.zone\n"
        mock_ssl_socket.sendall.assert_called_once_with(expected_command.encode("utf-8"))

    @patch("ssl.SSLContext.wrap_socket")
    @patch("socket.create_connection")
    def test_request_connection_error(self, mock_connect, mock_wrap_socket):
        """Test request with connection error."""
        mock_connect.side_effect = ConnectionRefusedError("Connection refused")
        client = self.create_client()

        with self.assertRaises(NSDConnectionError):
            client.request("status")

    @patch("ssl.SSLContext.wrap_socket")
    @patch("socket.create_connection")
    def test_request_timeout(self, mock_connect, mock_wrap_socket):
        """Test request timeout handling."""
        # Setup mocks
        mock_socket = MagicMock()
        mock_connect.return_value = mock_socket
        mock_ssl_socket = MagicMock()
        mock_wrap_socket.return_value = mock_ssl_socket
        mock_ssl_socket.recv.side_effect = socket.timeout("Read timed out")

        # Test
        client = self.create_client()
        with self.assertRaises(NSDTimeoutError):
            client.request("status")

    @patch("ssl.SSLContext.wrap_socket")
    @patch("socket.create_connection")
    def test_dynamic_methods(self, mock_connect, mock_wrap_socket):
        """Test dynamic method generation for NSD commands."""
        # Setup mocks
        mock_socket = MagicMock()
        mock_connect.return_value = mock_socket
        mock_ssl_socket = MagicMock()
        mock_wrap_socket.return_value = mock_ssl_socket
        mock_ssl_socket.recv.side_effect = [b"ok\n", b""]

        # Test dynamic method call
        client = self.create_client()
        response = client.notify("example.com")  # This should call request("notify", ("example.com"))
        # Verify
        expected_command = f"NSDCT{NSD_CONTROL_VERSION} notify example.com\n"
        mock_ssl_socket.sendall.assert_called_once_with(expected_command.encode("utf-8"))
        self.assertEqual(response.is_success(), True)
        self.assertEqual(response.msg, ["ok"])
        self.assertIsNone(response.data)

    @patch("ssl.SSLContext.wrap_socket")
    @patch("socket.create_connection")
    def test_command_error(self, mock_connect, mock_wrap_socket):
        """Test handling of command errors."""
        # Setup mocks
        mock_socket = MagicMock()
        mock_connect.return_value = mock_socket
        mock_ssl_socket = MagicMock()
        mock_wrap_socket.return_value = mock_ssl_socket
        mock_ssl_socket.recv.side_effect = [b"error: invalid command\n", b""]

        # Test
        client = self.create_client()
        with self.assertRaises(NSDCommandError) as cm:
            client.request("invalid")
        self.assertIn("invalid command", str(cm.exception))


if __name__ == "__main__":
    unittest.main()
