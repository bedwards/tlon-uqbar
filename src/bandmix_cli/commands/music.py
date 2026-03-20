"""Music command — manage audio tracks."""

from __future__ import annotations

from pathlib import Path

import click

from bandmix_cli.client import BandMixClient
from bandmix_cli.formatters import auto_format, format_output
from bandmix_cli.parser import parse_csrf_token, parse_music


@click.group()
def music():
    """Manage your audio tracks."""


@music.command("list")
@click.option(
    "--format",
    "fmt",
    type=click.Choice(["table", "json", "text", "raw"], case_sensitive=False),
    default=None,
    help="Output format.",
)
@click.option("--raw", is_flag=True, help="Print raw HTML response.")
def list_tracks(fmt: str | None, raw: bool) -> None:
    """List all audio tracks."""
    output_format = fmt or auto_format()
    client = BandMixClient()
    resp = client.get("/account/audio/")

    if raw:
        click.echo(resp.text)
        return

    tracks = parse_music(resp.text)
    if not tracks:
        click.echo("No audio tracks found.")
        return

    click.echo(format_output(tracks, output_format))


@music.command()
@click.argument("file_path", type=click.Path(exists=True))
@click.option("--title", required=True, help="Track title.")
def upload(file_path: str, title: str) -> None:
    """Upload an audio file."""
    client = BandMixClient()
    page_resp = client.get("/account/audio/")
    csrf = parse_csrf_token(page_resp.text)

    path = Path(file_path)
    with open(path, "rb") as f:
        data: dict[str, str] = {"title": title}
        if csrf:
            data["csrfmiddlewaretoken"] = csrf

        resp = client.upload(
            "/account/audio/",
            files={"file": (path.name, f, "audio/mpeg")},
            data=data,
        )

    if resp.status_code < 400:
        click.echo(f"Uploaded '{title}'.")
    else:
        click.echo(f"Failed to upload '{title}'.", err=True)
        raise SystemExit(1)


@music.command()
@click.argument("track_ids", nargs=-1, required=True)
def delete(track_ids: tuple[str, ...]) -> None:
    """Delete audio tracks by ID."""
    client = BandMixClient()
    page_resp = client.get("/account/audio/")
    csrf = parse_csrf_token(page_resp.text)

    for tid in track_ids:
        data: dict[str, str] = {"delete": tid}
        if csrf:
            data["csrfmiddlewaretoken"] = csrf

        resp = client.post("/account/audio/", data=data)
        if resp.status_code < 400:
            click.echo(f"Deleted track {tid}.")
        else:
            click.echo(f"Failed to delete track {tid}.", err=True)
            raise SystemExit(1)


@music.command()
@click.argument("track_id")
def master(track_id: str) -> None:
    """Submit a track for BandMix mastering."""
    client = BandMixClient()
    resp = client.post("/ajax/audio-mastering/", data={"audio": track_id})
    if resp.status_code < 400:
        click.echo(f"Mastering submitted for track {track_id}.")
    else:
        click.echo(f"Failed to submit mastering for track {track_id}.", err=True)
        raise SystemExit(1)


@music.command("master-status")
@click.argument("track_id")
def master_status(track_id: str) -> None:
    """Check mastering progress for a track."""
    client = BandMixClient()
    resp = client.get("/ajax/audio-mastering-progress/", params={"audio": track_id})
    if resp.status_code < 400:
        try:
            data = resp.json()
            progress = data.get("progress", "unknown")
            click.echo(f"Mastering progress for track {track_id}: {progress}%")
        except ValueError:
            click.echo(resp.text)
    else:
        click.echo(
            f"Failed to check mastering status for track {track_id}.",
            err=True,
        )
        raise SystemExit(1)


@music.command("download-master")
@click.argument("track_id")
@click.option(
    "--format",
    "audio_format",
    type=click.Choice(["mp3", "wav"], case_sensitive=False),
    default="mp3",
    help="Download format. Default: mp3.",
)
def download_master(track_id: str, audio_format: str) -> None:
    """Download the mastered version of a track."""
    client = BandMixClient()
    resp = client.get(
        "/ajax/audio-mastered/",
        params={"audio": track_id, "format": audio_format},
    )
    if resp.status_code < 400:
        try:
            data = resp.json()
            click.echo(data.get("content", resp.text))
        except ValueError:
            click.echo(resp.text)
    else:
        click.echo(f"Failed to download master for track {track_id}.", err=True)
        raise SystemExit(1)
