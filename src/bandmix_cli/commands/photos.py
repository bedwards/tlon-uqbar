"""Photos command — manage profile photos."""

from __future__ import annotations

from pathlib import Path

import click

from bandmix_cli.client import BandMixClient
from bandmix_cli.formatters import auto_format, format_output
from bandmix_cli.parser import parse_csrf_token, parse_photos


@click.group()
def photos():
    """Manage your profile photos."""


@photos.command("list")
@click.option(
    "--format",
    "fmt",
    type=click.Choice(["table", "json", "text", "raw"], case_sensitive=False),
    default=None,
    help="Output format.",
)
@click.option("--raw", is_flag=True, help="Print raw HTML response.")
def list_photos(fmt: str | None, raw: bool) -> None:
    """List all uploaded photos."""
    output_format = fmt or auto_format()
    client = BandMixClient()
    resp = client.get("/account/images/")

    if raw:
        click.echo(resp.text)
        return

    photo_list = parse_photos(resp.text)
    if not photo_list:
        click.echo("No photos found.")
        return

    click.echo(format_output(photo_list, output_format))


@photos.command()
@click.argument("file_paths", nargs=-1, required=True, type=click.Path(exists=True))
def upload(file_paths: tuple[str, ...]) -> None:
    """Upload one or more images (JPEG/PNG, max 24MB each)."""
    client = BandMixClient()

    # Get CSRF token from the images page
    page_resp = client.get("/account/images/")
    csrf = parse_csrf_token(page_resp.text)

    for fp in file_paths:
        path = Path(fp)
        with open(path, "rb") as f:
            data = {"csrfmiddlewaretoken": csrf} if csrf else {}
            resp = client.upload(
                "/account/images/",
                files={"file": (path.name, f, "application/octet-stream")},
                data=data,
            )
        if resp.status_code < 400:
            click.echo(f"Uploaded {path.name}.")
        else:
            click.echo(f"Failed to upload {path.name}.", err=True)
            raise SystemExit(1)


@photos.command("set-main")
@click.argument("photo_id")
def set_main(photo_id: str) -> None:
    """Set a photo as the main profile picture."""
    client = BandMixClient()
    page_resp = client.get("/account/images/")
    csrf = parse_csrf_token(page_resp.text)

    data: dict[str, str] = {"photo_id": photo_id}
    if csrf:
        data["csrfmiddlewaretoken"] = csrf

    resp = client.post("/account/images/", data=data)
    if resp.status_code < 400:
        click.echo(f"Set photo {photo_id} as main.")
    else:
        click.echo(f"Failed to set photo {photo_id} as main.", err=True)
        raise SystemExit(1)


@photos.command()
@click.argument("photo_ids", nargs=-1, required=True)
def delete(photo_ids: tuple[str, ...]) -> None:
    """Delete photos by ID."""
    client = BandMixClient()
    page_resp = client.get("/account/images/")
    csrf = parse_csrf_token(page_resp.text)

    for pid in photo_ids:
        data: dict[str, str] = {"delete": pid}
        if csrf:
            data["csrfmiddlewaretoken"] = csrf

        resp = client.post("/account/images/", data=data)
        if resp.status_code < 400:
            click.echo(f"Deleted photo {pid}.")
        else:
            click.echo(f"Failed to delete photo {pid}.", err=True)
            raise SystemExit(1)


@photos.command()
@click.argument("photo_ids", nargs=-1, required=True)
def reorder(photo_ids: tuple[str, ...]) -> None:
    """Set display order for photos."""
    client = BandMixClient()
    order_data = {f"order[{i}]": pid for i, pid in enumerate(photo_ids)}
    resp = client.post("/ajax/sort-images/", data=order_data)
    if resp.status_code < 400:
        click.echo("Photos reordered.")
    else:
        click.echo("Failed to reorder photos.", err=True)
        raise SystemExit(1)
