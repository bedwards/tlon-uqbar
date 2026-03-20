"""HTTP client with session/cookie persistence for BandMix.com."""

from __future__ import annotations

import json
import logging
import time
from pathlib import Path
from typing import Any

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

BASE_URL = "https://www.bandmix.com"
DEFAULT_CONFIG_DIR = Path.home() / ".config" / "bandmix-cli"
DEFAULT_SESSION_PATH = DEFAULT_CONFIG_DIR / "session.json"
LOGIN_PATH = "/login/"

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)

MAX_RETRIES = 3
BACKOFF_DELAYS = [1, 2, 4]


class BandMixClientError(Exception):
    """Base exception for client errors."""


class AuthenticationError(BandMixClientError):
    """Raised when the session is expired or invalid."""


class ServerError(BandMixClientError):
    """Raised when the server returns a 5xx error after retries."""


class BandMixClient:
    """HTTP client wrapping requests.Session with cookie persistence.

    Provides session/cookie persistence to disk, CSRF token extraction,
    retry with exponential backoff, and convenience methods for common
    HTTP operations against BandMix.com.
    """

    def __init__(
        self,
        base_url: str = BASE_URL,
        session_path: Path | str | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.session_path = Path(session_path) if session_path else DEFAULT_SESSION_PATH
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": USER_AGENT})
        self._load_session()

    # ------------------------------------------------------------------
    # Session persistence
    # ------------------------------------------------------------------

    def _load_session(self) -> None:
        """Load cookies from the session file if it exists."""
        if not self.session_path.exists():
            return
        try:
            data = json.loads(self.session_path.read_text())
            for cookie in data.get("cookies", []):
                self.session.cookies.set(
                    cookie["name"],
                    cookie["value"],
                    domain=cookie.get("domain", ""),
                    path=cookie.get("path", "/"),
                )
            logger.debug("Loaded session from %s", self.session_path)
        except (json.JSONDecodeError, KeyError):
            logger.warning("Corrupt session file; ignoring: %s", self.session_path)

    def save_session(self) -> None:
        """Persist current cookies to the session file."""
        self.session_path.parent.mkdir(parents=True, exist_ok=True)
        cookies = [
            {
                "name": c.name,
                "value": c.value,
                "domain": c.domain,
                "path": c.path,
            }
            for c in self.session.cookies
        ]
        self.session_path.write_text(json.dumps({"cookies": cookies}, indent=2))
        logger.debug("Saved session to %s", self.session_path)

    def clear_session(self) -> None:
        """Remove persisted session data and clear cookies."""
        self.session.cookies.clear()
        if self.session_path.exists():
            self.session_path.unlink()
            logger.debug("Removed session file %s", self.session_path)

    # ------------------------------------------------------------------
    # CSRF helpers
    # ------------------------------------------------------------------

    @staticmethod
    def extract_csrf_token(html: str) -> str | None:
        """Extract a CSRF token from a hidden input field in HTML.

        Looks for ``<input type="hidden" name="csrfmiddlewaretoken" ...>``
        or a ``<meta name="csrf-token" ...>`` tag.
        """
        soup = BeautifulSoup(html, "lxml")
        # Django-style hidden input
        tag = soup.find("input", {"name": "csrfmiddlewaretoken"})
        if tag and tag.get("value"):
            return tag["value"]
        # Meta tag fallback
        meta = soup.find("meta", {"name": "csrf-token"})
        if meta and meta.get("content"):
            return meta["content"]
        return None

    # ------------------------------------------------------------------
    # Session validation
    # ------------------------------------------------------------------

    def is_session_valid(self, response: requests.Response) -> bool:
        """Check whether a response indicates an expired session.

        BandMix redirects to the login page when the session has expired.
        """
        if response.history:
            for r in response.history:
                if r.status_code in (301, 302, 303, 307) and LOGIN_PATH in (
                    r.headers.get("Location", "")
                ):
                    return False
        if LOGIN_PATH in str(response.url):
            return False
        return True

    # ------------------------------------------------------------------
    # Core request with retry
    # ------------------------------------------------------------------

    def _request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        data: dict[str, Any] | None = None,
        files: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        allow_redirects: bool = True,
        check_auth: bool = True,
    ) -> requests.Response:
        """Execute an HTTP request with retry and session validation.

        Retries up to ``MAX_RETRIES`` times on 5xx errors with exponential
        backoff (1s, 2s, 4s). Raises ``AuthenticationError`` if the response
        redirects to the login page.
        """
        url = f"{self.base_url}{path}" if path.startswith("/") else path

        last_exc: Exception | None = None
        for attempt in range(MAX_RETRIES):
            try:
                resp = self.session.request(
                    method,
                    url,
                    params=params,
                    data=data,
                    files=files,
                    headers=headers,
                    allow_redirects=allow_redirects,
                )
                if resp.status_code >= 500:
                    raise ServerError(
                        f"Server error {resp.status_code} for {method} {path}"
                    )

                if check_auth and not self.is_session_valid(resp):
                    raise AuthenticationError(
                        "Session expired. Please re-authenticate with: "
                        "bandmix auth login"
                    )

                return resp
            except ServerError as exc:
                last_exc = exc
                if attempt < MAX_RETRIES - 1:
                    delay = BACKOFF_DELAYS[attempt]
                    logger.warning(
                        "Retry %d/%d after %ds: %s",
                        attempt + 1,
                        MAX_RETRIES,
                        delay,
                        exc,
                    )
                    time.sleep(delay)

        raise last_exc  # type: ignore[misc]

    # ------------------------------------------------------------------
    # Convenience methods
    # ------------------------------------------------------------------

    def get(
        self,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        check_auth: bool = True,
    ) -> requests.Response:
        """Send a GET request."""
        return self._request(
            "GET",
            path,
            params=params,
            headers=headers,
            check_auth=check_auth,
        )

    def post(
        self,
        path: str,
        *,
        data: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        check_auth: bool = True,
    ) -> requests.Response:
        """Send a POST request (form-encoded)."""
        return self._request(
            "POST",
            path,
            data=data,
            headers=headers,
            check_auth=check_auth,
        )

    def upload(
        self,
        path: str,
        *,
        files: dict[str, Any],
        data: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        check_auth: bool = True,
    ) -> requests.Response:
        """Send a multipart file upload POST request."""
        return self._request(
            "POST",
            path,
            data=data,
            files=files,
            headers=headers,
            check_auth=check_auth,
        )
