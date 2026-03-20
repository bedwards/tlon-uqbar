"""Matches command — view dashboard match results."""

from __future__ import annotations

import click

from bandmix_cli.client import BandMixClient
from bandmix_cli.enums import MatchType
from bandmix_cli.formatters import auto_format, format_output
from bandmix_cli.parser import parse_matches


@click.group()
def matches():
    """View match results from your dashboard."""


@matches.command("list")
@click.option(
    "--type",
    "match_type",
    type=click.Choice(["new", "new-members"], case_sensitive=False),
    default="new",
    help="Match type: new (default) or new-members.",
)
@click.option("--page", type=int, default=1, help="Page number. Default: 1.")
@click.option(
    "--format",
    "fmt",
    type=click.Choice(["table", "json", "text", "raw"], case_sensitive=False),
    default=None,
    help="Output format.",
)
@click.option("--raw", is_flag=True, help="Print raw HTML response.")
def list_matches(match_type: str, page: int, fmt: str | None, raw: bool) -> None:
    """List matches from /account/connections/."""
    output_format = fmt or auto_format()
    client = BandMixClient()

    type_val = (
        MatchType.NEW_LOCAL_MEMBERS
        if match_type == "new-members"
        else MatchType.NEW_MATCHES
    )
    params: dict[str, str] = {"type": type_val.value}
    if page > 1:
        params["page"] = str(page)

    resp = client.get("/account/connections/", params=params)

    if raw:
        click.echo(resp.text)
        return

    results = parse_matches(resp.text)
    if not results:
        click.echo("No matches found.")
        return

    click.echo(format_output(results, output_format))
