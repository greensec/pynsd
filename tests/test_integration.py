import subprocess
import time
import uuid
import os
from pathlib import Path
from typing import Dict, Iterator, List

import pytest

from pynsd.client import Client


pytestmark = pytest.mark.integration

REPO_ROOT = Path(__file__).resolve().parent.parent
COMPOSE_FILE = REPO_ROOT / "docker-compose.integration.yml"
RUNTIME_DIR = REPO_ROOT / "tests" / "integration" / "runtime"
RUNTIME_CERTS_DIR = RUNTIME_DIR / "certs"
RUNTIME_DYNAMIC_ZONE_DIR = RUNTIME_DIR / "zones" / "dynamic"
CONTROL_PORT = int(os.environ.get("PYNSD_TEST_CONTROL_PORT", "8952"))


def _compose_cmd(*args: str) -> List[str]:
    return ["docker", "compose", "-f", str(COMPOSE_FILE), *args]


def _nsd_control(*args: str, check: bool = True) -> subprocess.CompletedProcess:
    command = _compose_cmd("exec", "-T", "nsd", "nsd-control", "-c", "/etc/nsd/nsd.conf", *args)
    completed = subprocess.run(command, check=False, capture_output=True, text=True)
    if check and completed.returncode != 0:
        raise AssertionError(
            f"nsd-control command failed: {' '.join(args)}\nstdout:\n{completed.stdout}\nstderr:\n{completed.stderr}"
        )
    return completed


def _parse_kv_colon_output(raw: str) -> Dict[str, str]:
    parsed: Dict[str, str] = {}
    for line in raw.splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        parsed[key.strip()] = value.strip()
    return parsed


def _parse_zonestatus_output(raw: str) -> Dict[str, Dict[str, str]]:
    zones: Dict[str, Dict[str, str]] = {}
    current_zone = ""

    for line in raw.splitlines():
        stripped = line.strip()
        if not stripped or stripped == "ok":
            continue
        if stripped.startswith("zone:"):
            _, zone_name = stripped.split(":", 1)
            current_zone = zone_name.strip()
            zones[current_zone] = {}
            continue
        if ":" not in stripped and "=" not in stripped and not stripped.startswith("["):
            current_zone = stripped
            zones[current_zone] = {}
            continue

        if current_zone and ":" in stripped:
            key, value = stripped.split(":", 1)
            zones[current_zone][key.strip()] = value.strip()

    return zones


def _write_dynamic_zone_file(zone_name: str) -> Path:
    RUNTIME_DYNAMIC_ZONE_DIR.mkdir(parents=True, exist_ok=True)
    zone_path = RUNTIME_DYNAMIC_ZONE_DIR / f"{zone_name}.zone"
    zone_content = f"""$ORIGIN {zone_name}.
$TTL 3600
@ IN SOA ns1.{zone_name}. hostmaster.{zone_name}. (
  2026032701
  3600
  600
  1209600
  3600
)
@ IN NS ns1.{zone_name}.
ns1 IN A 192.0.2.100
www IN A 192.0.2.101
"""
    zone_path.write_text(zone_content, encoding="ascii")
    return zone_path


def _wait_until_nsd_ready(timeout_seconds: int = 60) -> None:
    deadline = time.time() + timeout_seconds
    last_error = ""

    while time.time() < deadline:
        status = _nsd_control("status", check=False)
        if status.returncode == 0 and "version:" in status.stdout:
            return
        last_error = f"stdout:\n{status.stdout}\nstderr:\n{status.stderr}"
        time.sleep(1)

    raise TimeoutError(f"NSD did not become ready within {timeout_seconds}s\n{last_error}")


def _cleanup_dynamic_zone(zone_name: str) -> None:
    _nsd_control("delzone", zone_name, check=False)
    zone_path = RUNTIME_DYNAMIC_ZONE_DIR / f"{zone_name}.zone"
    if zone_path.exists():
        zone_path.unlink()


@pytest.fixture(scope="session", autouse=True)
def _integration_readiness() -> Iterator[None]:
    _wait_until_nsd_ready()
    yield


@pytest.fixture
def nsd_client() -> Iterator[Client]:
    client = Client(
        client_cert=RUNTIME_CERTS_DIR / "nsd_control.pem",
        client_key=RUNTIME_CERTS_DIR / "nsd_control.key",
        server_cert=RUNTIME_CERTS_DIR / "nsd_server.pem",
        host="127.0.0.1",
        port=CONTROL_PORT,
        ssl_verify=False,
    )
    try:
        yield client
    finally:
        client.close()


def test_status_returns_real_server_data(nsd_client: Client) -> None:
    result = nsd_client.status()

    assert result.success is True
    assert isinstance(result.data, dict)
    assert "version" in result.data

    raw_status = _nsd_control("status").stdout
    parsed_raw = _parse_kv_colon_output(raw_status)

    assert result.data["version"] == parsed_raw.get("version")
    if "verbosity" in result.data and "verbosity" in parsed_raw:
        assert result.data["verbosity"] == parsed_raw["verbosity"]


def test_serverpid_returns_integer_and_matches_nsd(nsd_client: Client) -> None:
    result = nsd_client.serverpid()

    assert result.success is True
    assert isinstance(result.data, dict)
    assert isinstance(result.data["pid"], int)

    raw_pid_output = _nsd_control("serverpid").stdout.strip().splitlines()[0]
    assert result.data["pid"] == int(raw_pid_output)


def test_zonestatus_for_static_zone(nsd_client: Client) -> None:
    zone_name = "example.com"
    result = nsd_client.zonestatus(zone_name)

    assert result.success is True
    assert isinstance(result.data, dict)
    assert zone_name in result.data

    raw_zone = _parse_zonestatus_output(_nsd_control("zonestatus", zone_name).stdout)
    assert zone_name in raw_zone

    parsed_zone_data = result.data[zone_name]
    raw_zone_data = raw_zone[zone_name]
    shared_keys = set(parsed_zone_data).intersection(raw_zone_data)

    assert shared_keys
    for key in shared_keys:
        assert parsed_zone_data[key] == raw_zone_data[key]


def test_addzone_then_confirm_with_zonestatus(nsd_client: Client) -> None:
    zone_name = f"ci-{uuid.uuid4().hex}.example"

    try:
        _write_dynamic_zone_file(zone_name)

        add_result = nsd_client.addzone(zone_name, "dynamic-primary")
        assert add_result.success is True

        zone_result = nsd_client.zonestatus(zone_name)
        assert zone_result.success is True
        assert isinstance(zone_result.data, dict)
        assert zone_name in zone_result.data

        raw_zone = _parse_zonestatus_output(_nsd_control("zonestatus", zone_name).stdout)
        assert zone_name in raw_zone

        parsed_zone_data = zone_result.data[zone_name]
        raw_zone_data = raw_zone[zone_name]
        shared_keys = set(parsed_zone_data).intersection(raw_zone_data)

        assert shared_keys
        for key in shared_keys:
            assert parsed_zone_data[key] == raw_zone_data[key]
    finally:
        _cleanup_dynamic_zone(zone_name)


def test_delzone_removes_dynamic_zone(nsd_client: Client) -> None:
    zone_name = f"ci-{uuid.uuid4().hex}.example"

    _write_dynamic_zone_file(zone_name)
    try:
        add_result = nsd_client.addzone(zone_name, "dynamic-primary")
        assert add_result.success is True

        del_result = nsd_client.delzone(zone_name)
        assert del_result.success is True

        after_delete = _nsd_control("zonestatus", zone_name, check=False)
        assert after_delete.returncode != 0 or zone_name not in after_delete.stdout
    finally:
        _cleanup_dynamic_zone(zone_name)
