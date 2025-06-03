# pynsd

[![PyPI](https://img.shields.io/pypi/v/pynsd)](https://pypi.org/project/pynsd/)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Python Version](https://img.shields.io/pypi/pyversions/pynsd)](https://pypi.org/project/pynsd/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

A modern Python client for the NSD (Name Server Daemon) control interface, providing type-safe access to NSD's control API.

## Features

- Full support for NSD 4.x control protocol
- Type hints for better IDE support and code quality
- Context manager support for safe resource handling
- Comprehensive error handling with custom exceptions
- Support for both synchronous and asynchronous operations
- Parsed response objects with easy access to response data

## Installation

```bash
pip install pynsd
```

## Basic Usage

### Connecting to NSD

```python
import pynsd

# Basic connection with default settings (localhost:8953)
with pynsd.Client(
    client_cert='/etc/nsd/nsd_control.pem',
    client_key='/etc/nsd/nsd_control.key',
    host='127.0.0.1',
    port=8953
) as client:
    # ...

# For self-signed certificates without hostname verification
with pynsd.Client(
    client_cert='/etc/nsd/nsd_control.pem',
    client_key='/etc/nsd/nsd_control.key',
    host='nsd.example.com',
    port=8953,
    ssl_verify=False  # Disable SSL certificate verification
) as client:
    # Get server status
    status = client.status()
    print(f"NSD is running with {status.data.get('num_zones', 0)} zones")
```

### Common Operations

```python
# Add a zone
result = client.add_zone('example.com.', 'example.com.zone')
print(f"Added zone: {result.msg}")

# Get zone status
status = client.zonestatus('example.com.')
print(f"Zone status: {status.data}")

# Reload configuration
client.reload()

# Get server statistics
stats = client.stats_noreset()
print(f"Queries: {stats.data.get('num_query', 0)}")
```

### Error Handling

```python
from pynsd import NSDCommandError, NSDConnectionError

try:
    client.add_zone('invalid.zone', 'nonexistent.zone')
except NSDCommandError as e:
    print(f"Command failed: {e}")
except NSDConnectionError as e:
    print(f"Connection error: {e}")
```

## Advanced Usage

### Using Raw Commands

```python
# Using raw command API
response = client.request('addzone', ('example.org.', 'example.org.zone'))
if response.is_success():
    print("Zone added successfully")
```

### Custom Timeout

```python
# Set custom timeout for operations (in seconds)
client = pynsd.Client(
    client_cert='cert.pem',
    client_key='key.pem',
    timeout=10.0
)
```

## Development

### Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/greensec/pynsd.git
   cd pynsd
   ```

2. Install development dependencies:
   ```bash
   pip install -e .[dev]
   ```

### Running Tests

```bash
make test
```

### Code Quality

```bash
make validate  # Runs formatting, linting, and type checking
```

## Contributing

Contributions are welcome! Please open an issue or submit a pull request.

## See Also

- [NSD Documentation](https://www.nlnetlabs.nl/documentation/nsd/)
- [NSD Control Protocol](https://www.nlnetlabs.nl/documentation/nsd/nsd-control/)
