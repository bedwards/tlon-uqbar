"""Music List command — manage saved profiles (bookmarks)."""

from __future__ import annotations

import click

from bandmix_cli.client import BandMixClient
from bandmix_cli.formatters import auto_format, format_output
from bandmix_cli.parser import parse_musiclist


@click.group()
def musiclist():
    """Manage your Music List (bookmarked profiles)."""


@musiclist.command("list")
@click.option(
    "--format",
    "fmt",
    type=click.Choice(["table", "json", "text", "raw"], case_sensitive=False),
    default=None,
    help="Output format.",
)
@click.option("--raw", is_flag=True, help="Print raw HTML response.")
def list_bookmarks(fmt: str | None, raw: bool) -> None:
    """List bookmarked profiles."""
    output_format = fmt or auto_format()
    client = BandMixClient()
    resp = client.get("/account/bookmarks/")

    if raw:
        click.echo(resp.text)
        return

    results = parse_musiclist(resp.text)
    if not results:
        click.echo("No bookmarked profiles found.")
        return

    click.echo(format_output(results, output_format))


@musiclist.command()
@click.argument("slug")
def add(slug: str) -> None:
    """Add a profile to your Music List."""
    client = BandMixClient()
    resp = client.post(f"/account/bookmarks/add/{slug}/")
    if resp.status_code < 400:
        click.echo(f"Added {slug} to Music List.")
    else:
        click.echo(f"Failed to add {slug} to Music List.", err=True)
        raise SystemExit(1)


@musiclist.command()
@click.argument("slug")
def remove(slug: str) -> None:
    """Remove a profile from your Music List."""
    client = BandMixClient()
    resp = client.post(f"/account/bookmarks/remove/{slug}/")
    if resp.status_code < 400:
        click.echo(f"Removed {slug} from Music List.")
    else:
        click.echo(f"Failed to remove {slug} from Music List.", err=True)
        raise SystemExit(1)
