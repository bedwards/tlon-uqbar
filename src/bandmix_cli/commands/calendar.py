"""Calendar command — manage calendar events."""

from __future__ import annotations

import click

from bandmix_cli.client import BandMixClient
from bandmix_cli.formatters import auto_format, format_output
from bandmix_cli.parser import parse_calendar, parse_csrf_token


@click.group()
def calendar():
    """Manage your calendar events."""


@calendar.command("list")
@click.option(
    "--format",
    "fmt",
    type=click.Choice(["table", "json", "text", "raw"], case_sensitive=False),
    default=None,
    help="Output format.",
)
@click.option("--raw", is_flag=True, help="Print raw HTML response.")
def list_events(fmt: str | None, raw: bool) -> None:
    """List calendar events."""
    output_format = fmt or auto_format()
    client = BandMixClient()
    resp = client.get("/account/calendar/")

    if raw:
        click.echo(resp.text)
        return

    events = parse_calendar(resp.text)
    if not events:
        click.echo("No calendar events found.")
        return

    click.echo(format_output(events, output_format))


@calendar.command()
@click.option("--date", "event_date", required=True, help="Event date (YYYY-MM-DD).")
@click.option("--time", "event_time", default=None, help="Event time (HH:MM).")
@click.option("--title", required=True, help="Event title.")
@click.option("--description", default=None, help="Event description.")
def add(
    event_date: str,
    event_time: str | None,
    title: str,
    description: str | None,
) -> None:
    """Add a calendar event."""
    client = BandMixClient()
    page_resp = client.get("/account/calendar/")
    csrf = parse_csrf_token(page_resp.text)

    data: dict[str, str] = {
        "date": event_date,
        "title": title,
    }
    if event_time:
        data["time"] = event_time
    if description:
        data["description"] = description
    if csrf:
        data["csrfmiddlewaretoken"] = csrf

    resp = client.post("/account/calendar/", data=data)
    if resp.status_code < 400:
        click.echo(f"Added event '{title}' on {event_date}.")
    else:
        click.echo(f"Failed to add event '{title}'.", err=True)
        raise SystemExit(1)


@calendar.command()
@click.argument("event_ids", nargs=-1, required=True)
def delete(event_ids: tuple[str, ...]) -> None:
    """Delete calendar events by ID."""
    client = BandMixClient()
    page_resp = client.get("/account/calendar/")
    csrf = parse_csrf_token(page_resp.text)

    for eid in event_ids:
        data: dict[str, str] = {"delete": eid}
        if csrf:
            data["csrfmiddlewaretoken"] = csrf

        resp = client.post("/account/calendar/", data=data)
        if resp.status_code < 400:
            click.echo(f"Deleted event {eid}.")
        else:
            click.echo(f"Failed to delete event {eid}.", err=True)
            raise SystemExit(1)
