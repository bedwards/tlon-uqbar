"""Hidden command — manage hidden/blocked users."""

from __future__ import annotations

import click

from bandmix_cli.client import BandMixClient
from bandmix_cli.formatters import auto_format, format_output
from bandmix_cli.parser import parse_hidden


@click.group()
def hidden():
    """Manage hidden/blocked users."""


@hidden.command("list")
@click.option(
    "--format",
    "fmt",
    type=click.Choice(["table", "json", "text", "raw"], case_sensitive=False),
    default=None,
    help="Output format.",
)
@click.option("--raw", is_flag=True, help="Print raw HTML response.")
def list_hidden(fmt: str | None, raw: bool) -> None:
    """List hidden users."""
    output_format = fmt or auto_format()
    client = BandMixClient()
    resp = client.get("/account/hidden/")

    if raw:
        click.echo(resp.text)
        return

    results = parse_hidden(resp.text)
    if not results:
        click.echo("No hidden users found.")
        return

    click.echo(format_output(results, output_format))


@hidden.command()
@click.argument("slug")
def add(slug: str) -> None:
    """Add a user to the hidden list."""
    client = BandMixClient()
    resp = client.post(f"/account/hidden/add/{slug}/")
    if resp.status_code < 400:
        click.echo(f"Hidden {slug}.")
    else:
        click.echo(f"Failed to hide {slug}.", err=True)
        raise SystemExit(1)


@hidden.command()
@click.argument("slug")
def remove(slug: str) -> None:
    """Remove a user from the hidden list."""
    client = BandMixClient()
    resp = client.post(f"/account/hidden/remove/{slug}/")
    if resp.status_code < 400:
        click.echo(f"Unhidden {slug}.")
    else:
        click.echo(f"Failed to unhide {slug}.", err=True)
        raise SystemExit(1)
