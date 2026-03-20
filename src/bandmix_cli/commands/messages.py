"""Messages commands — list threads, read conversations, send messages."""

from __future__ import annotations

import click

from bandmix_cli.auth import PremierRequiredError
from bandmix_cli.client import BandMixClient
from bandmix_cli.formatters import format_output
from bandmix_cli.parser import (
    parse_csrf_token,
    parse_messages_list,
    parse_message_thread,
)

MESSAGES_PATH = "/account/messages/"
SEND_MESSAGE_PATH = "/account/messages/send/"


@click.group()
def messages():
    """Read and compose messages."""


@messages.command("list")
@click.option(
    "--format",
    "fmt",
    type=click.Choice(["table", "json", "text"]),
    default="table",
    help="Output format.",
)
@click.option("--raw", is_flag=True, help="Print raw HTML response.")
def list_threads(fmt: str, raw: bool) -> None:
    """List message threads."""
    client = BandMixClient()
    resp = client.get(MESSAGES_PATH)

    if raw:
        click.echo(resp.text)
        return

    threads = parse_messages_list(resp.text)
    if not threads:
        click.echo("No message threads found.")
        return

    click.echo(format_output(threads, fmt))


@messages.command("read")
@click.argument("thread_id")
@click.option(
    "--format",
    "fmt",
    type=click.Choice(["table", "json", "text"]),
    default="table",
    help="Output format.",
)
@click.option("--raw", is_flag=True, help="Print raw HTML response.")
def read_thread(thread_id: str, fmt: str, raw: bool) -> None:
    """Read a conversation by thread ID."""
    client = BandMixClient()
    resp = client.get(f"{MESSAGES_PATH}{thread_id}/")

    if raw:
        click.echo(resp.text)
        return

    thread = parse_message_thread(resp.text)
    if not thread.messages:
        click.echo("No messages found in this thread.")
        return

    click.echo(format_output(thread, fmt))


@messages.command("send")
@click.argument("slug")
@click.option("--body", required=True, help="Message body text.")
def send_message(slug: str, body: str) -> None:
    """Send a message to a member (Premier only)."""
    client = BandMixClient()

    # Fetch the send-message page to get a CSRF token
    page_resp = client.get(f"{MESSAGES_PATH}send/{slug}/")

    # Detect premier-only gate
    page_lower = page_resp.text.lower()
    if "premier" in page_lower and (
        "upgrade" in page_lower or "premier member" in page_lower
    ):
        raise PremierRequiredError(
            "Sending messages requires a Premier membership. "
            "Upgrade at https://www.bandmix.com/account/upgrade/"
        )

    csrf_token = parse_csrf_token(page_resp.text)

    form_data: dict[str, str] = {"body": body}
    if csrf_token:
        form_data["csrfmiddlewaretoken"] = csrf_token

    resp = client.post(
        f"{MESSAGES_PATH}send/{slug}/",
        data=form_data,
    )

    if resp.status_code < 400:
        click.echo(f"Message sent to {slug}.")
    else:
        click.echo(f"Failed to send message to {slug}.", err=True)
        raise SystemExit(1)
