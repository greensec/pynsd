"""Unit tests for the NSD response parser."""
import unittest

from pynsd.parser import Response, ResponseParser


class TestResponse(unittest.TestCase):
    def test_success_true(self):
        r = Response({"success": True})
        self.assertTrue(r.is_success())

    def test_success_false(self):
        r = Response({"success": False})
        self.assertFalse(r.is_success())

    def test_success_defaults_to_none(self):
        r = Response({})
        self.assertIsNone(r.success)
        self.assertFalse(r.is_success())

    def test_msg(self):
        r = Response({"msg": ["line1", "line2"]})
        self.assertEqual(r.get_message(), ["line1", "line2"])

    def test_msg_missing(self):
        r = Response({})
        self.assertIsNone(r.get_message())

    def test_data_from_result_key(self):
        r = Response({"result": {"key": "value"}})
        self.assertEqual(r.get_data(), {"key": "value"})

    def test_data_missing(self):
        r = Response({})
        self.assertIsNone(r.get_data())

    def test_to_dict(self):
        r = Response({"success": True, "msg": ["ok"], "result": {"key": "val"}})
        d = r.to_dict()
        self.assertEqual(d["success"], True)
        self.assertEqual(d["msg"], ["ok"])
        self.assertEqual(d["data"], {"key": "val"})

    def test_repr(self):
        r = Response({"success": True})
        self.assertIn("ControlResult", repr(r))


class TestResponseParserEmpty(unittest.TestCase):
    def test_empty_data_returns_failure(self):
        result = ResponseParser.parse("status", "")
        self.assertFalse(result.is_success())

    def test_empty_command_returns_failure(self):
        result = ResponseParser.parse("", "some data")
        self.assertFalse(result.is_success())

    def test_unknown_command_returns_none_success(self):
        result = ResponseParser.parse("unknown_cmd", "some response\n")
        self.assertIsNone(result.success)
        self.assertEqual(result.msg, ["some response"])


class TestResponseParserStatus(unittest.TestCase):
    STATUS_DATA = "version: 4.6.0\nverbosity: 0\ndebug mode: off\n"

    def test_parse_status_success(self):
        result = ResponseParser.parse("status", self.STATUS_DATA)
        self.assertTrue(result.is_success())
        assert result.data is not None
        self.assertEqual(result.data["version"], "4.6.0")
        self.assertEqual(result.data["verbosity"], "0")
        self.assertEqual(result.data["debug mode"], "off")

    def test_parse_status_failure_when_no_version(self):
        result = ResponseParser.parse("status", "error: not connected\n")
        self.assertFalse(result.is_success())

    def test_parse_status_accepts_bytes(self):
        result = ResponseParser.parse("status", b"version: 4.6.0\n")
        self.assertTrue(result.is_success())


class TestResponseParserStats(unittest.TestCase):
    STATS_DATA = "time.elapsed=0.001234\ntime.now=1234567890.123456\nnum.queries=42\n"

    def test_parse_stats_success(self):
        result = ResponseParser.parse("stats", self.STATS_DATA)
        self.assertTrue(result.is_success())
        assert result.data is not None
        self.assertEqual(result.data["time.elapsed"], "0.001234")
        self.assertEqual(result.data["num.queries"], "42")

    def test_parse_stats_noreset(self):
        result = ResponseParser.parse("stats_noreset", self.STATS_DATA)
        self.assertTrue(result.is_success())

    def test_parse_stats_failure_when_no_time_elapsed(self):
        result = ResponseParser.parse("stats", "num.queries=0\n")
        self.assertFalse(result.is_success())


class TestResponseParserOk(unittest.TestCase):
    def test_parse_ok_simple(self):
        result = ResponseParser.parse("notify", "ok\n")
        self.assertTrue(result.is_success())
        self.assertEqual(result.msg, ["ok"])

    def test_parse_ok_with_comma(self):
        result = ResponseParser.parse("notify", "ok, enqueued\n")
        self.assertTrue(result.is_success())

    def test_parse_ok_error_response(self):
        result = ResponseParser.parse("notify", "error: zone not found\n")
        self.assertFalse(result.is_success())

    def test_all_ok_commands_succeed_with_ok_response(self):
        for cmd in ResponseParser.OK_COMMANDS:
            with self.subTest(cmd=cmd):
                result = ResponseParser.parse(cmd, "ok\n")
                self.assertTrue(result.is_success())


class TestResponseParserTransfer(unittest.TestCase):
    def test_parse_transfer_with_zone_count(self):
        raw = ResponseParser._parse("transfer", "ok, 3 zones transferred\n")
        self.assertTrue(raw["success"])
        self.assertEqual(raw["zones"], 3)

    def test_parse_force_transfer_success(self):
        result = ResponseParser.parse("force_transfer", "ok\n")
        self.assertTrue(result.is_success())

    def test_parse_transfer_no_zone_count(self):
        raw = ResponseParser._parse("transfer", "ok\n")
        self.assertIsNone(raw["zones"])

    def test_parse_transfer_singular_zone(self):
        raw = ResponseParser._parse("transfer", "ok, 1 zone transferred\n")
        self.assertEqual(raw["zones"], 1)

    def test_parse_transfer_failure(self):
        result = ResponseParser.parse("transfer", "error: no such zone\n")
        self.assertFalse(result.is_success())


class TestResponseParserZoneStatus(unittest.TestCase):
    STATUS_DATA = "example.com\n\tstate: ok\n\tserved-serial: 2021061901\n\tnotified-serial: 2021061901\n"

    def test_parse_zonestatus_success(self):
        result = ResponseParser.parse("zonestatus", self.STATUS_DATA)
        self.assertTrue(result.is_success())
        assert isinstance(result.data, dict)
        self.assertIn("example.com", result.data)
        self.assertEqual(result.data["example.com"]["state"], "ok")
        self.assertEqual(result.data["example.com"]["served-serial"], "2021061901")

    def test_parse_zonestatus_empty_is_failure(self):
        result = ResponseParser.parse("zonestatus", "  \n")
        self.assertFalse(result.is_success())

    def test_parse_zonestatus_multiple_zones(self):
        data = "example.com\n\tstate: ok\ntest.org\n\tstate: refreshing\n"
        result = ResponseParser.parse("zonestatus", data)
        self.assertTrue(result.is_success())
        zones = result.data
        assert isinstance(zones, dict)
        self.assertIn("example.com", zones)
        self.assertIn("test.org", zones)
        self.assertEqual(zones["test.org"]["state"], "refreshing")


class TestResponseParserServerPid(unittest.TestCase):
    def test_parse_serverpid_success(self):
        result = ResponseParser.parse("serverpid", "12345\n")
        self.assertTrue(result.is_success())
        pid_data = result.data
        assert isinstance(pid_data, dict)
        self.assertEqual(pid_data["pid"], 12345)

    def test_parse_serverpid_invalid_returns_failure(self):
        result = ResponseParser.parse("serverpid", "not-a-pid\n")
        self.assertFalse(result.is_success())


class TestResponseParserTsig(unittest.TestCase):
    TSIG_DATA = "tsig-key.example.com\n\talgorithm: hmac-sha256\n\tsecret: c2VjcmV0\n"

    def test_parse_print_tsig_success(self):
        result = ResponseParser.parse("print_tsig", self.TSIG_DATA)
        self.assertTrue(result.is_success())
        keys = result.data
        assert isinstance(keys, dict)
        self.assertIn("tsig-key.example.com", keys)
        self.assertEqual(keys["tsig-key.example.com"]["algorithm"], "hmac-sha256")
        self.assertEqual(keys["tsig-key.example.com"]["secret"], "c2VjcmV0")


class TestResponseParserCookieSecrets(unittest.TestCase):
    COOKIE_DATA = "deadbeef01234567=active\n01234567deadbeef=staging\n"

    def test_parse_cookie_secrets_success(self):
        # result["result"] is a list, tested via _parse to avoid Dict[str,Any] annotation mismatch
        raw = ResponseParser._parse("print_cookie_secrets", self.COOKIE_DATA)
        self.assertTrue(raw["success"])
        cookies = raw["result"]
        self.assertEqual(len(cookies), 2)
        self.assertEqual(cookies[0]["secret"], "deadbeef01234567")
        self.assertEqual(cookies[0]["status"], "active")
        self.assertEqual(cookies[1]["secret"], "01234567deadbeef")
        self.assertEqual(cookies[1]["status"], "staging")

    def test_parse_cookie_secrets_single(self):
        raw = ResponseParser._parse("print_cookie_secrets", "abc123=active\n")
        self.assertTrue(raw["success"])
        self.assertEqual(raw["result"][0]["status"], "active")


if __name__ == "__main__":
    unittest.main()
