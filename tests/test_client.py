"""Tests for bandmix_cli.client using the responses mock library."""

from __future__ import annotations

import json
from pathlib import Path

import responses

from bandmix_cli.client import (
    AuthenticationError,
    BandMixClient,
    ServerError,
    USER_AGENT,
)


# ------------------------------------------------------------------
# Fixtures / helpers
# ------------------------------------------------------------------


def _make_client(tmp_path: Path) -> BandMixClient:
    """Create a client with a temporary session file."""
    return BandMixClient(
        base_url="https://www.bandmix.com",
        session_path=tmp_path / "session.json",
    )


# ------------------------------------------------------------------
# Session persistence
# ------------------------------------------------------------------


class TestSessionPersistence:
    def test_save_and_load_session(self, tmp_path: Path) -> None:
        client = _make_client(tmp_path)
        client.session.cookies.set("sid", "abc123", domain=".bandmix.com", path="/")
        client.save_session()

        # Verify file written
        data = json.loads((tmp_path / "session.json").read_text())
        assert len(data["cookies"]) == 1
        assert data["cookies"][0]["name"] == "sid"
        assert data["cookies"][0]["value"] == "abc123"

        # Load into a fresh client
        client2 = _make_client(tmp_path)
        assert client2.session.cookies.get("sid") == "abc123"

    def test_clear_session(self, tmp_path: Path) -> None:
        client = _make_client(tmp_path)
        client.session.cookies.set("sid", "abc123", domain=".bandmix.com", path="/")
        client.save_session()
        assert (tmp_path / "session.json").exists()

        client.clear_session()
        assert not (tmp_path / "session.json").exists()
        assert len(client.session.cookies) == 0

    def test_load_missing_session_file(self, tmp_path: Path) -> None:
        """No error when session file does not exist."""
        client = _make_client(tmp_path)
        assert len(client.session.cookies) == 0

    def test_load_corrupt_session_file(self, tmp_path: Path) -> None:
        (tmp_path / "session.json").write_text("NOT JSON")
        client = _make_client(tmp_path)
        assert len(client.session.cookies) == 0


# ------------------------------------------------------------------
# User-Agent
# ------------------------------------------------------------------


class TestUserAgent:
    @responses.activate
    def test_user_agent_header(self, tmp_path: Path) -> None:
        responses.add(
            responses.GET,
            "https://www.bandmix.com/test/",
            body="ok",
            status=200,
        )
        client = _make_client(tmp_path)
        client.get("/test/", check_auth=False)

        assert responses.calls[0].request.headers["User-Agent"] == USER_AGENT


# ------------------------------------------------------------------
# CSRF token extraction
# ------------------------------------------------------------------


class TestCSRFExtraction:
    def test_extract_csrf_from_hidden_input(self) -> None:
        html = (
            '<form><input type="hidden" name="csrfmiddlewaretoken" '
            'value="tok123"></form>'
        )
        assert BandMixClient.extract_csrf_token(html) == "tok123"

    def test_extract_csrf_from_meta(self) -> None:
        html = '<html><head><meta name="csrf-token" content="metatok"></head></html>'
        assert BandMixClient.extract_csrf_token(html) == "metatok"

    def test_no_csrf_returns_none(self) -> None:
        html = "<html><body>Hello</body></html>"
        assert BandMixClient.extract_csrf_token(html) is None


# ------------------------------------------------------------------
# Session validation (redirect to login)
# ------------------------------------------------------------------


class TestSessionValidation:
    @responses.activate
    def test_redirect_to_login_raises_auth_error(self, tmp_path: Path) -> None:
        responses.add(
            responses.GET,
            "https://www.bandmix.com/account/profile/",
            status=302,
            headers={"Location": "https://www.bandmix.com/login/"},
        )
        responses.add(
            responses.GET,
            "https://www.bandmix.com/login/",
            body="<html>Login</html>",
            status=200,
        )
        client = _make_client(tmp_path)
        try:
            client.get("/account/profile/")
            msg = "Expected AuthenticationError"
            raise AssertionError(msg)
        except AuthenticationError:
            pass

    @responses.activate
    def test_valid_session_no_error(self, tmp_path: Path) -> None:
        responses.add(
            responses.GET,
            "https://www.bandmix.com/account/profile/",
            body="<html>Profile</html>",
            status=200,
        )
        client = _make_client(tmp_path)
        resp = client.get("/account/profile/")
        assert resp.status_code == 200


# ------------------------------------------------------------------
# Retry with exponential backoff
# ------------------------------------------------------------------


class TestRetryBackoff:
    @responses.activate
    def test_retries_on_500_then_succeeds(self, tmp_path: Path) -> None:
        responses.add(
            responses.GET,
            "https://www.bandmix.com/page/",
            body="error",
            status=500,
        )
        responses.add(
            responses.GET,
            "https://www.bandmix.com/page/",
            body="ok",
            status=200,
        )
        client = _make_client(tmp_path)
        # Monkey-patch time.sleep to avoid real delays
        import bandmix_cli.client as client_mod

        sleeps: list[float] = []
        original_sleep = client_mod.time.sleep
        client_mod.time.sleep = lambda s: sleeps.append(s)
        try:
            resp = client.get("/page/", check_auth=False)
            assert resp.status_code == 200
            assert len(responses.calls) == 2
            assert sleeps == [1]
        finally:
            client_mod.time.sleep = original_sleep

    @responses.activate
    def test_raises_after_max_retries(self, tmp_path: Path) -> None:
        for _ in range(3):
            responses.add(
                responses.GET,
                "https://www.bandmix.com/fail/",
                body="error",
                status=500,
            )
        client = _make_client(tmp_path)
        import bandmix_cli.client as client_mod

        client_mod.time.sleep = lambda s: None
        try:
            client.get("/fail/", check_auth=False)
            msg = "Expected ServerError"
            raise AssertionError(msg)
        except ServerError:
            pass
        finally:
            import time

            client_mod.time.sleep = time.sleep


# ------------------------------------------------------------------
# Convenience methods
# ------------------------------------------------------------------


class TestConvenienceMethods:
    @responses.activate
    def test_post(self, tmp_path: Path) -> None:
        responses.add(
            responses.POST,
            "https://www.bandmix.com/account/profile/",
            body="ok",
            status=200,
        )
        client = _make_client(tmp_path)
        resp = client.post(
            "/account/profile/",
            data={"field": "value"},
            check_auth=False,
        )
        assert resp.status_code == 200
        assert "field=value" in responses.calls[0].request.body

    @responses.activate
    def test_upload(self, tmp_path: Path) -> None:
        responses.add(
            responses.POST,
            "https://www.bandmix.com/account/images/",
            body="ok",
            status=200,
        )
        # Create a fake file
        fake_file = tmp_path / "photo.jpg"
        fake_file.write_bytes(b"\xff\xd8\xff\xe0fake-jpeg-data")

        client = _make_client(tmp_path)
        with open(fake_file, "rb") as f:
            resp = client.upload(
                "/account/images/",
                files={"file": ("photo.jpg", f, "image/jpeg")},
                check_auth=False,
            )
        assert resp.status_code == 200
        assert b"fake-jpeg-data" in responses.calls[0].request.body


# ------------------------------------------------------------------
# Redirect following
# ------------------------------------------------------------------


class TestRedirectFollowing:
    @responses.activate
    def test_follows_302_after_post(self, tmp_path: Path) -> None:
        responses.add(
            responses.POST,
            "https://www.bandmix.com/account/profile/",
            status=302,
            headers={"Location": "https://www.bandmix.com/account/profile/success/"},
        )
        responses.add(
            responses.GET,
            "https://www.bandmix.com/account/profile/success/",
            body="<html>Success</html>",
            status=200,
        )
        client = _make_client(tmp_path)
        resp = client.post(
            "/account/profile/",
            data={"field": "value"},
            check_auth=False,
        )
        assert resp.status_code == 200
        assert len(responses.calls) == 2
