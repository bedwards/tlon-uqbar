"""Click command group for authentication (login, logout, status)."""

from __future__ import annotations

import click

from bandmix_cli.client import AuthenticationError


@click.group()
def auth():
    """Authenticate with BandMix.com."""


@auth.command()
@click.option("--email", required=True, help="Your BandMix account email.")
def login(email: str):
    """Log in to BandMix.com (prompts for password)."""
    from bandmix_cli.auth import login as do_login

    password = click.prompt("Password", hide_input=True)
    try:
        do_login(email, password)
        click.echo("Login successful.")
    except AuthenticationError as exc:
        raise click.ClickException(str(exc)) from exc


@auth.command()
def logout():
    """Log out and clear the saved session."""
    from bandmix_cli.auth import logout as do_logout

    do_logout()
    click.echo("Logged out.")


@auth.command()
def status():
    """Show the current session status (screen name and membership tier)."""
    from bandmix_cli.auth import get_status

    try:
        info = get_status()
        click.echo(f"Logged in as: {info['screen_name']}")
        click.echo(f"Membership:   {info['tier']}")
    except AuthenticationError as exc:
        raise click.ClickException(str(exc)) from exc
