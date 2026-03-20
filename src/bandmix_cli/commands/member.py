"""Member view and actions commands."""

from __future__ import annotations

import click

from bandmix_cli.client import BandMixClient
from bandmix_cli.formatters import format_output
from bandmix_cli.parser import parse_member_profile


@click.group()
def member():
    """View member profiles and manage music list / hidden users."""


@member.command()
@click.argument("slug")
@click.option(
    "--format",
    "fmt",
    type=click.Choice(["table", "json", "text"]),
    default="table",
    help="Output format.",
)
@click.option("--raw", is_flag=True, help="Print raw HTML response.")
def view(slug: str, fmt: str, raw: bool) -> None:
    """Fetch and display a member's public profile."""
    client = BandMixClient()
    resp = client.get(f"/{slug}/")

    if raw:
        click.echo(resp.text)
        return

    profile = parse_member_profile(resp.text, slug)
    click.echo(format_output(profile, fmt))


@member.command("add-to-list")
@click.argument("slug")
def add_to_list(slug: str) -> None:
    """Add a member to your Music List (bookmark)."""
    client = BandMixClient()
    resp = client.post(f"/account/bookmarks/add/{slug}/")
    if resp.status_code < 400:
        click.echo(f"Added {slug} to Music List.")
    else:
        click.echo(f"Failed to add {slug} to Music List.", err=True)
        raise SystemExit(1)


@member.command("remove-from-list")
@click.argument("slug")
def remove_from_list(slug: str) -> None:
    """Remove a member from your Music List."""
    client = BandMixClient()
    resp = client.post(f"/account/bookmarks/remove/{slug}/")
    if resp.status_code < 400:
        click.echo(f"Removed {slug} from Music List.")
    else:
        click.echo(f"Failed to remove {slug} from Music List.", err=True)
        raise SystemExit(1)


@member.command()
@click.argument("slug")
def hide(slug: str) -> None:
    """Add a member to your hidden users list."""
    client = BandMixClient()
    resp = client.post(f"/account/hidden/add/{slug}/")
    if resp.status_code < 400:
        click.echo(f"Hidden {slug}.")
    else:
        click.echo(f"Failed to hide {slug}.", err=True)
        raise SystemExit(1)


@member.command()
@click.argument("slug")
def unhide(slug: str) -> None:
    """Remove a member from your hidden users list."""
    client = BandMixClient()
    resp = client.post(f"/account/hidden/remove/{slug}/")
    if resp.status_code < 400:
        click.echo(f"Unhidden {slug}.")
    else:
        click.echo(f"Failed to unhide {slug}.", err=True)
        raise SystemExit(1)
