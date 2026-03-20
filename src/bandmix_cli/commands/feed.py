"""Feed command — view activity feed, like/unlike entries."""

from __future__ import annotations

import click

from bandmix_cli.client import BandMixClient
from bandmix_cli.enums import FeedFilter
from bandmix_cli.formatters import auto_format, format_output
from bandmix_cli.parser import parse_feed

# Mapping from CLI filter names to BandMix feeds_show parameter values
_FILTER_MAP = {
    "all": "1",
    "local": "2",
    "music-list": "3",
    "my-feeds": "4",
}


@click.group()
def feed():
    """View activity feed and manage likes."""


@feed.command("list")
@click.option(
    "--filter",
    "feed_filter",
    type=click.Choice([f.value for f in FeedFilter], case_sensitive=False),
    default="all",
    help="Filter feed entries. Default: all.",
)
@click.option("--limit", type=int, default=None, help="Max entries to return.")
@click.option(
    "--format",
    "fmt",
    type=click.Choice(["table", "json", "text", "raw"], case_sensitive=False),
    default=None,
    help="Output format.",
)
@click.option("--raw", is_flag=True, help="Print raw HTML response.")
def list_feed(feed_filter: str, limit: int | None, fmt: str | None, raw: bool) -> None:
    """List activity feed entries."""
    output_format = fmt or auto_format()
    client = BandMixClient()

    feeds_show = _FILTER_MAP.get(feed_filter, "1")
    resp = client.get("/account/feeds-load/", params={"feeds_show": feeds_show})

    if raw:
        click.echo(resp.text)
        return

    entries = parse_feed(resp.text)
    if limit is not None:
        entries = entries[:limit]

    if not entries:
        click.echo("No feed entries found.")
        return

    click.echo(format_output(entries, output_format))


@feed.command()
@click.argument("feed_id")
def like(feed_id: str) -> None:
    """Like a feed entry."""
    client = BandMixClient()
    resp = client.post(
        "/account/feeds-load-comments/",
        data={"feed": feed_id, "action": "like"},
    )
    if resp.status_code < 400:
        click.echo(f"Liked feed entry {feed_id}.")
    else:
        click.echo(f"Failed to like feed entry {feed_id}.", err=True)
        raise SystemExit(1)


@feed.command()
@click.argument("feed_id")
def unlike(feed_id: str) -> None:
    """Unlike a feed entry."""
    client = BandMixClient()
    resp = client.post(
        "/account/feeds-load-comments/",
        data={"feed": feed_id, "action": "unlike"},
    )
    if resp.status_code < 400:
        click.echo(f"Unliked feed entry {feed_id}.")
    else:
        click.echo(f"Failed to unlike feed entry {feed_id}.", err=True)
        raise SystemExit(1)
