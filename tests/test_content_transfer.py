"""
Content transfer tests (modern app.utils imports).

Live CLIENT/SERVER network cases are skipped — unit coverage without a peer is in
tests/test_content_transfer_unit.py.
"""
from unittest import TestCase

import pytest

from app.utils import content_transfer
from app.utils.common import SystemMode


class TestConnectServer(TestCase):
    def test_server_connect_unknown(self):
        data = {}
        content_transfer.new_client_connection(SystemMode.SERVER, "", data)
        assert data["error_code"] == 400
        assert data["error"] == "System in unknown mode"

    def test_server_connect_not_a_server(self):
        data = {}
        content_transfer.new_client_connection(SystemMode.CLIENT, "", data)
        assert data["error_code"] == 400
        assert data["error"] == "not a server"

    def test_server_connect_valid(self):
        data = {}
        content_transfer.new_client_connection(
            SystemMode.SERVER, content_transfer.get_handshake_secret(), data
        )
        assert data["error_code"] == 200
        assert data["server_token"] == content_transfer.get_handshake_response()

    def test_request_all_content_unauthorized(self):
        data = {}
        content_transfer.request_all_content("bad-token", data)
        assert data["error_code"] == 401


class TestQueryServerLive(TestCase):
    """Requires a running SERVER peer + server_url — not for CI."""

    @pytest.mark.skip(reason="Requires live SERVER peer; see test_content_transfer_unit.py")
    def test_connect_to_server(self):
        pass

    @pytest.mark.skip(reason="Requires live SERVER peer")
    def test_query_server(self):
        pass
