"""Tests for authentication (login, logout, status)."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import responses
from click.testing import CliRunner

from bandmix_cli.auth import get_status, login, logout
from bandmix_cli.client import AuthenticationError, BandMixClient
from bandmix_cli.commands.auth import auth as auth_group

BASE = "https://www.bandmix.com"

# ---------------------------------------------------------------------------
# HTML fixtures
# ---------------------------------------------------------------------------

LOGIN_PAGE_HTML = """
<html><body>
<form method="post" action="/login/">
  <input type="hidden" name="csrfmiddlewaretoken" value="tok123">
  <input name="email"><input name="password">
  <button type="submit">Log In</button>
</form>
</body></html>
"""

ACCOUNT_PAGE_HTML = """
<html><body>
<span class="screen-name">JimStone</span>
<span class="premier-badge">Premier</span>
<p>premier member</p>
</body></html>
"""

ACCOUNT_PAGE_FREE_HTML = """
<html><body>
<span class="screen-name">FreeUser</span>
</body></html>
"""


# ---------------------------------------------------------------------------
# Helper to build a client that writes to a temp dir
# ---------------------------------------------------------------------------


def _make_client(tmp_path: Path) -> BandMixClient:
    session_path = tmp_path / "session.json"
    return BandMixClient(session_path=session_path)


# ---------------------------------------------------------------------------
# auth.login
# ---------------------------------------------------------------------------


class TestLogin:
    @responses.activate
    def test_login_success(self, tmp_path: Path) -> None:
        # GET login page
        responses.add(responses.GET, f"{BASE}/login/", body=LOGIN_PAGE_HTML)
        # POST login — redirect to /account/
        responses.add(
            responses.POST,
            f"{BASE}/login/",
            status=302,
            headers={"Location": f"{BASE}/account/"},
        )
        responses.add(responses.GET, f"{BASE}/account/", body=ACCOUNT_PAGE_HTML)

        client = _make_client(tmp_path)
        login("jim@example.com", "secret", client=client)

        # Session file should have been created
        assert client.session_path.exists()

    @responses.activate
    def test_login_failure(self, tmp_path: Path) -> None:
        responses.add(responses.GET, f"{BASE}/login/", body=LOGIN_PAGE_HTML)
        # POST stays on login page (bad creds)
        responses.add(
            responses.POST,
            f"{BASE}/login/",
            body=LOGIN_PAGE_HTML,
        )

        client = _make_client(tmp_path)
        try:
            login("bad@example.com", "wrong", client=client)
            assert False, "Expected AuthenticationError"  # noqa: B011
        except AuthenticationError:
            pass


# ---------------------------------------------------------------------------
# auth.logout
# ---------------------------------------------------------------------------


class TestLogout:
    def test_logout_clears_session(self, tmp_path: Path) -> None:
        client = _make_client(tmp_path)
        # Create a session file first
        client.session.cookies.set("sid", "abc123")
        client.save_session()
        assert client.session_path.exists()

        logout(client=client)
        assert not client.session_path.exists()


# ---------------------------------------------------------------------------
# auth.get_status
# ---------------------------------------------------------------------------


class TestGetStatus:
    @responses.activate
    def test_status_premier(self, tmp_path: Path) -> None:
        responses.add(responses.GET, f"{BASE}/account/", body=ACCOUNT_PAGE_HTML)

        client = _make_client(tmp_path)
        info = get_status(client=client)
        assert info["screen_name"] == "JimStone"
        assert info["tier"] == "Premier"

    @responses.activate
    def test_status_free(self, tmp_path: Path) -> None:
        responses.add(responses.GET, f"{BASE}/account/", body=ACCOUNT_PAGE_FREE_HTML)

        client = _make_client(tmp_path)
        info = get_status(client=client)
        assert info["screen_name"] == "FreeUser"
        assert info["tier"] == "Free"

    @responses.activate
    def test_status_expired_session(self, tmp_path: Path) -> None:
        # Redirect to login page signals expired session
        responses.add(
            responses.GET,
            f"{BASE}/account/",
            status=302,
            headers={"Location": f"{BASE}/login/"},
        )
        responses.add(responses.GET, f"{BASE}/login/", body=LOGIN_PAGE_HTML)

        client = _make_client(tmp_path)
        try:
            get_status(client=client)
            assert False, "Expected AuthenticationError"  # noqa: B011
        except AuthenticationError:
            pass


# ---------------------------------------------------------------------------
# Click CLI commands
# ---------------------------------------------------------------------------


class TestAuthCLI:
    @responses.activate
    def test_login_command(self, tmp_path: Path) -> None:
        responses.add(responses.GET, f"{BASE}/login/", body=LOGIN_PAGE_HTML)
        responses.add(
            responses.POST,
            f"{BASE}/login/",
            status=302,
            headers={"Location": f"{BASE}/account/"},
        )
        responses.add(responses.GET, f"{BASE}/account/", body=ACCOUNT_PAGE_HTML)

        runner = CliRunner()
        session_path = tmp_path / "session.json"
        with patch(
            "bandmix_cli.auth.BandMixClient",
            lambda **kw: BandMixClient(session_path=session_path),
        ):
            result = runner.invoke(
                auth_group, ["login", "--email", "jim@example.com"], input="secret\n"
            )
        assert result.exit_code == 0
        assert "Login successful" in result.output

    def test_logout_command(self, tmp_path: Path) -> None:
        runner = CliRunner()
        session_path = tmp_path / "session.json"
        # Create a session file
        client = BandMixClient(session_path=session_path)
        client.session.cookies.set("sid", "abc")
        client.save_session()

        with patch(
            "bandmix_cli.auth.BandMixClient",
            lambda **kw: BandMixClient(session_path=session_path),
        ):
            result = runner.invoke(auth_group, ["logout"])
        assert result.exit_code == 0
        assert "Logged out" in result.output

    @responses.activate
    def test_status_command(self, tmp_path: Path) -> None:
        responses.add(responses.GET, f"{BASE}/account/", body=ACCOUNT_PAGE_HTML)

        runner = CliRunner()
        session_path = tmp_path / "session.json"
        with patch(
            "bandmix_cli.auth.BandMixClient",
            lambda **kw: BandMixClient(session_path=session_path),
        ):
            result = runner.invoke(auth_group, ["status"])
        assert result.exit_code == 0
        assert "JimStone" in result.output
        assert "Premier" in result.output

    @responses.activate
    def test_status_command_expired(self, tmp_path: Path) -> None:
        responses.add(
            responses.GET,
            f"{BASE}/account/",
            status=302,
            headers={"Location": f"{BASE}/login/"},
        )
        responses.add(responses.GET, f"{BASE}/login/", body=LOGIN_PAGE_HTML)

        runner = CliRunner()
        session_path = tmp_path / "session.json"
        with patch(
            "bandmix_cli.auth.BandMixClient",
            lambda **kw: BandMixClient(session_path=session_path),
        ):
            result = runner.invoke(auth_group, ["status"])
        assert result.exit_code != 0
        assert "Session expired" in result.output
