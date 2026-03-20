"""Settings command — account settings (email, matchmailer, dashboard, password)."""

from __future__ import annotations

import click

from bandmix_cli.client import BandMixClient
from bandmix_cli.formatters import auto_format, format_output
from bandmix_cli.parser import (
    parse_csrf_token,
    parse_settings_dashboard,
    parse_settings_email,
    parse_settings_matchmailer,
)


@click.group()
def settings():
    """Manage account settings."""


# ---------------------------------------------------------------------------
# Email settings
# ---------------------------------------------------------------------------


@settings.group()
def email():
    """Email notification settings."""


@email.command("get")
@click.option(
    "--format",
    "fmt",
    type=click.Choice(["table", "json", "text", "raw"], case_sensitive=False),
    default=None,
    help="Output format.",
)
@click.option("--raw", is_flag=True, help="Print raw HTML response.")
def email_get(fmt: str | None, raw: bool) -> None:
    """Get current email settings."""
    output_format = fmt or auto_format()
    client = BandMixClient()
    resp = client.get("/account/email/")

    if raw:
        click.echo(resp.text)
        return

    email_settings = parse_settings_email(resp.text)
    click.echo(format_output(email_settings, output_format))


@email.command("set")
@click.option(
    "--newsletters",
    type=click.Choice(["enabled", "disabled"], case_sensitive=False),
    default=None,
)
@click.option(
    "--user-views",
    type=click.Choice(["enabled", "disabled"], case_sensitive=False),
    default=None,
)
@click.option(
    "--user-visited",
    type=click.Choice(["enabled", "disabled"], case_sensitive=False),
    default=None,
)
@click.option(
    "--user-music-lists",
    type=click.Choice(["enabled", "disabled"], case_sensitive=False),
    default=None,
)
@click.option(
    "--general-notifications",
    type=click.Choice(["enabled", "disabled"], case_sensitive=False),
    default=None,
)
@click.option(
    "--format-pref",
    "format_pref",
    type=click.Choice(["html", "plaintext"], case_sensitive=False),
    default=None,
    help="Email format preference.",
)
def email_set(
    newsletters: str | None,
    user_views: str | None,
    user_visited: str | None,
    user_music_lists: str | None,
    general_notifications: str | None,
    format_pref: str | None,
) -> None:
    """Update email notification settings."""
    client = BandMixClient()
    page_resp = client.get("/account/email/")
    csrf = parse_csrf_token(page_resp.text)

    data: dict[str, str] = {}
    if csrf:
        data["csrfmiddlewaretoken"] = csrf
    if newsletters is not None:
        data["newsletters"] = newsletters
    if user_views is not None:
        data["user_views"] = user_views
    if user_visited is not None:
        data["user_visited"] = user_visited
    if user_music_lists is not None:
        data["user_music_lists"] = user_music_lists
    if general_notifications is not None:
        data["general_notifications"] = general_notifications
    if format_pref is not None:
        data["format"] = format_pref

    resp = client.post("/account/email/", data=data)
    if resp.status_code < 400:
        click.echo("Email settings updated.")
    else:
        click.echo("Failed to update email settings.", err=True)
        raise SystemExit(1)


# ---------------------------------------------------------------------------
# Match Mailer
# ---------------------------------------------------------------------------


@settings.group()
def matchmailer():
    """Match mailer settings."""


@matchmailer.command("get")
@click.option(
    "--format",
    "fmt",
    type=click.Choice(["table", "json", "text", "raw"], case_sensitive=False),
    default=None,
    help="Output format.",
)
@click.option("--raw", is_flag=True, help="Print raw HTML response.")
def matchmailer_get(fmt: str | None, raw: bool) -> None:
    """Get current match mailer settings."""
    output_format = fmt or auto_format()
    client = BandMixClient()
    resp = client.get("/account/email/")

    if raw:
        click.echo(resp.text)
        return

    mm_settings = parse_settings_matchmailer(resp.text)
    click.echo(format_output(mm_settings, output_format))


@matchmailer.command("set")
@click.option(
    "--enabled",
    type=click.Choice(["true", "false"], case_sensitive=False),
    default=None,
)
@click.option("--radius", type=int, default=None)
@click.option("--age-from", type=int, default=None)
@click.option("--age-to", type=int, default=None)
@click.option(
    "--filter-instrument",
    type=click.Choice(["true", "false"], case_sensitive=False),
    default=None,
)
@click.option(
    "--filter-genre",
    type=click.Choice(["true", "false"], case_sensitive=False),
    default=None,
)
@click.option(
    "--recommendations",
    type=click.Choice(["enabled", "disabled"], case_sensitive=False),
    default=None,
)
@click.option(
    "--additional-local",
    type=click.Choice(["enabled", "disabled"], case_sensitive=False),
    default=None,
)
def matchmailer_set(
    enabled: str | None,
    radius: int | None,
    age_from: int | None,
    age_to: int | None,
    filter_instrument: str | None,
    filter_genre: str | None,
    recommendations: str | None,
    additional_local: str | None,
) -> None:
    """Update match mailer settings."""
    client = BandMixClient()
    page_resp = client.get("/account/email/")
    csrf = parse_csrf_token(page_resp.text)

    data: dict[str, str] = {}
    if csrf:
        data["csrfmiddlewaretoken"] = csrf
    if enabled is not None:
        data["enabled"] = "on" if enabled.lower() == "true" else ""
    if radius is not None:
        data["radius"] = str(radius)
    if age_from is not None:
        data["age_from"] = str(age_from)
    if age_to is not None:
        data["age_to"] = str(age_to)
    if filter_instrument is not None:
        data["filter_instrument"] = "on" if filter_instrument.lower() == "true" else ""
    if filter_genre is not None:
        data["filter_genre"] = "on" if filter_genre.lower() == "true" else ""
    if recommendations is not None:
        data["recommendations"] = recommendations
    if additional_local is not None:
        data["additional_local"] = additional_local

    resp = client.post("/account/email/", data=data)
    if resp.status_code < 400:
        click.echo("Match mailer settings updated.")
    else:
        click.echo("Failed to update match mailer settings.", err=True)
        raise SystemExit(1)


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------


@settings.group()
def dashboard():
    """Dashboard display options."""


@dashboard.command("get")
@click.option(
    "--format",
    "fmt",
    type=click.Choice(["table", "json", "text", "raw"], case_sensitive=False),
    default=None,
    help="Output format.",
)
@click.option("--raw", is_flag=True, help="Print raw HTML response.")
def dashboard_get(fmt: str | None, raw: bool) -> None:
    """Get current dashboard settings."""
    output_format = fmt or auto_format()
    client = BandMixClient()
    resp = client.get("/account/dashboard-options/")

    if raw:
        click.echo(resp.text)
        return

    dash_settings = parse_settings_dashboard(resp.text)
    click.echo(format_output(dash_settings, output_format))


@dashboard.command("set")
@click.option(
    "--show-matches",
    type=click.Choice(["true", "false"], case_sensitive=False),
    default=None,
)
@click.option("--radius", type=int, default=None)
@click.option("--age-from", type=int, default=None)
@click.option("--age-to", type=int, default=None)
def dashboard_set(
    show_matches: str | None,
    radius: int | None,
    age_from: int | None,
    age_to: int | None,
) -> None:
    """Update dashboard display options."""
    client = BandMixClient()
    page_resp = client.get("/account/dashboard-options/")
    csrf = parse_csrf_token(page_resp.text)

    data: dict[str, str] = {}
    if csrf:
        data["csrfmiddlewaretoken"] = csrf
    if show_matches is not None:
        data["show_matches"] = "on" if show_matches.lower() == "true" else ""
    if radius is not None:
        data["radius"] = str(radius)
    if age_from is not None:
        data["age_from"] = str(age_from)
    if age_to is not None:
        data["age_to"] = str(age_to)

    resp = client.post("/account/dashboard-options/", data=data)
    if resp.status_code < 400:
        click.echo("Dashboard settings updated.")
    else:
        click.echo("Failed to update dashboard settings.", err=True)
        raise SystemExit(1)


# ---------------------------------------------------------------------------
# Password
# ---------------------------------------------------------------------------


@settings.group()
def password():
    """Password management."""


@password.command("update")
def password_update() -> None:
    """Update your password (prompts interactively)."""
    old_password = click.prompt("Current password", hide_input=True)
    new_password = click.prompt(
        "New password", hide_input=True, confirmation_prompt=True
    )

    client = BandMixClient()
    page_resp = client.get("/account/password/")
    csrf = parse_csrf_token(page_resp.text)

    data: dict[str, str] = {
        "old_password": old_password,
        "new_password": new_password,
    }
    if csrf:
        data["csrfmiddlewaretoken"] = csrf

    resp = client.post("/account/password/", data=data)
    if resp.status_code < 400:
        click.echo("Password updated.")
    else:
        click.echo("Failed to update password.", err=True)
        raise SystemExit(1)
