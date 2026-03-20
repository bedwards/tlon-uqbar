"""Videos command — manage YouTube video links."""

from __future__ import annotations

import click

from bandmix_cli.client import BandMixClient
from bandmix_cli.formatters import auto_format, format_output
from bandmix_cli.parser import parse_csrf_token, parse_videos


@click.group()
def videos():
    """Manage your YouTube video links."""


@videos.command("list")
@click.option(
    "--format",
    "fmt",
    type=click.Choice(["table", "json", "text", "raw"], case_sensitive=False),
    default=None,
    help="Output format.",
)
@click.option("--raw", is_flag=True, help="Print raw HTML response.")
def list_videos(fmt: str | None, raw: bool) -> None:
    """List all videos."""
    output_format = fmt or auto_format()
    client = BandMixClient()
    resp = client.get("/account/video/")

    if raw:
        click.echo(resp.text)
        return

    video_list = parse_videos(resp.text)
    if not video_list:
        click.echo("No videos found.")
        return

    click.echo(format_output(video_list, output_format))


@videos.command()
@click.option("--title", required=True, help="Video title.")
@click.option("--url", required=True, help="YouTube URL.")
@click.option("--visible/--no-visible", default=True, help="Video visibility.")
def add(title: str, url: str, visible: bool) -> None:
    """Add a YouTube video link."""
    client = BandMixClient()
    page_resp = client.get("/account/video/")
    csrf = parse_csrf_token(page_resp.text)

    data: dict[str, str] = {
        "title": title,
        "url": url,
        "visible": "1" if visible else "0",
    }
    if csrf:
        data["csrfmiddlewaretoken"] = csrf

    resp = client.post("/account/video/", data=data)
    if resp.status_code < 400:
        click.echo(f"Added video '{title}'.")
    else:
        click.echo(f"Failed to add video '{title}'.", err=True)
        raise SystemExit(1)


@videos.command()
@click.argument("video_ids", nargs=-1, required=True)
def delete(video_ids: tuple[str, ...]) -> None:
    """Delete videos by ID."""
    client = BandMixClient()
    page_resp = client.get("/account/video/")
    csrf = parse_csrf_token(page_resp.text)

    for vid in video_ids:
        data: dict[str, str] = {"delete": vid}
        if csrf:
            data["csrfmiddlewaretoken"] = csrf

        resp = client.post("/account/video/", data=data)
        if resp.status_code < 400:
            click.echo(f"Deleted video {vid}.")
        else:
            click.echo(f"Failed to delete video {vid}.", err=True)
            raise SystemExit(1)


@videos.command()
@click.argument("video_ids", nargs=-1, required=True)
def reorder(video_ids: tuple[str, ...]) -> None:
    """Reorder videos."""
    client = BandMixClient()
    order_data = {f"order[{i}]": vid for i, vid in enumerate(video_ids)}
    resp = client.post("/ajax/reorder-videos/", data=order_data)
    if resp.status_code < 400:
        click.echo("Videos reordered.")
    else:
        click.echo("Failed to reorder videos.", err=True)
        raise SystemExit(1)
