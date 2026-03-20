"""Authentication: login, logout, and session status for BandMix.com."""

from __future__ import annotations

import logging

from bs4 import BeautifulSoup

from bandmix_cli.client import (
    AuthenticationError,
    BandMixClient,
    LOGIN_PATH,
)

logger = logging.getLogger(__name__)

ACCOUNT_PATH = "/account/"


class PremierRequiredError(Exception):
    """Raised when an action requires Premier membership."""


def login(email: str, password: str, *, client: BandMixClient | None = None) -> None:
    """Authenticate via POST to the BandMix login form and persist the session.

    Raises ``AuthenticationError`` on invalid credentials.
    """
    client = client or BandMixClient()

    # Fetch login page to get CSRF token
    login_resp = client.get(LOGIN_PATH, check_auth=False)
    csrf_token = client.extract_csrf_token(login_resp.text)

    form_data: dict[str, str] = {
        "email": email,
        "password": password,
    }
    if csrf_token:
        form_data["csrfmiddlewaretoken"] = csrf_token

    # Submit the login form
    resp = client.post(LOGIN_PATH, data=form_data, check_auth=False)

    # After successful login BandMix redirects away from the login page.
    # If we're still on the login page, the credentials were wrong.
    if LOGIN_PATH in str(resp.url):
        raise AuthenticationError("Login failed. Check your email and password.")

    client.save_session()
    logger.info("Login successful. Session saved.")


def logout(*, client: BandMixClient | None = None) -> None:
    """Clear the persisted session."""
    client = client or BandMixClient()
    client.clear_session()
    logger.info("Logged out. Session cleared.")


def get_status(*, client: BandMixClient | None = None) -> dict[str, str]:
    """Validate the current session and return the screen name and membership tier.

    Returns a dict with ``screen_name`` and ``tier`` keys.
    Raises ``AuthenticationError`` if the session is invalid/expired.
    """
    client = client or BandMixClient()

    resp = client.get(ACCOUNT_PATH, check_auth=True)
    soup = BeautifulSoup(resp.text, "lxml")

    # Extract screen name from the account page
    screen_name_tag = soup.select_one("span.screen-name, .user-name, h1.profile-name")
    screen_name = screen_name_tag.get_text(strip=True) if screen_name_tag else "Unknown"

    # Detect membership tier
    tier = "Free"
    page_text = resp.text.lower()
    if "premier" in page_text:
        # Look for premier badge or membership indicator
        premier_tag = soup.select_one(".premier-badge, .membership-premier")
        if premier_tag:
            tier = "Premier"
        elif "premier member" in page_text:
            tier = "Premier"

    return {"screen_name": screen_name, "tier": tier}
