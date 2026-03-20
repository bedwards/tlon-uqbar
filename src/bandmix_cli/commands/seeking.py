"""Seeking command — manage 'Now Seeking' / wanted ads."""

from __future__ import annotations

import click

from bandmix_cli.client import BandMixClient
from bandmix_cli.formatters import auto_format, format_output
from bandmix_cli.parser import parse_csrf_token, parse_seeking


@click.group()
def seeking():
    """Manage your 'Now Seeking' settings."""


@seeking.command()
@click.option(
    "--format",
    "fmt",
    type=click.Choice(["table", "json", "text", "raw"], case_sensitive=False),
    default=None,
    help="Output format.",
)
@click.option("--raw", is_flag=True, help="Print raw HTML response.")
def get(fmt: str | None, raw: bool) -> None:
    """Get current seeking status."""
    output_format = fmt or auto_format()
    client = BandMixClient()
    resp = client.get("/account/ads/")

    if raw:
        click.echo(resp.text)
        return

    status = parse_seeking(resp.text)
    click.echo(format_output(status, output_format))


@seeking.command("set")
@click.option(
    "--join-band",
    type=click.Choice(["true", "false"], case_sensitive=False),
    default=None,
    help="Set 'looking to join a band'.",
)
@click.option(
    "--instruments",
    default=None,
    help="Comma-separated list of instruments you are seeking.",
)
def set_seeking(join_band: str | None, instruments: str | None) -> None:
    """Update seeking preferences."""
    client = BandMixClient()
    page_resp = client.get("/account/ads/")
    csrf = parse_csrf_token(page_resp.text)

    data: dict[str, str] = {}
    if csrf:
        data["csrfmiddlewaretoken"] = csrf

    if join_band is not None:
        data["join_band"] = "on" if join_band.lower() == "true" else ""

    if instruments is not None:
        for i, inst in enumerate(instruments.split(",")):
            data[f"instruments_{i}"] = inst.strip()

    resp = client.post("/account/ads/", data=data)
    if resp.status_code < 400:
        click.echo("Seeking preferences updated.")
    else:
        click.echo("Failed to update seeking preferences.", err=True)
        raise SystemExit(1)
