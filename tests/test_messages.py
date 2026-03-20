"""Tests for messages commands — list, read, send."""

from __future__ import annotations

import responses
from click.testing import CliRunner

from bandmix_cli.auth import PremierRequiredError
from bandmix_cli.client import BASE_URL
from bandmix_cli.commands.messages import messages
from bandmix_cli.models import MessageThread
from bandmix_cli.parser import parse_messages_list, parse_message_thread

# ---------------------------------------------------------------------------
# Sample HTML fixtures
# ---------------------------------------------------------------------------

MESSAGES_LIST_HTML = """\
<html>
<body>
<div class="message-thread" data-thread-id="101">
  <span class="thread-participant"><a href="/jim-stone/">Jim Stone</a></span>
  <span class="thread-preview">Hey, want to jam?</span>
  <time class="thread-time" datetime="2025-03-15T10:30:00">Mar 15</time>
</div>
<div class="message-thread" data-thread-id="102">
  <span class="thread-participant"><a href="/jane-doe/">Jane Doe</a></span>
  <span class="thread-preview">Great show last night!</span>
  <time class="thread-time" datetime="2025-03-14T18:00:00">Mar 14</time>
</div>
</body>
</html>
"""

EMPTY_MESSAGES_HTML = """\
<html><body>
<div class="messages-container"></div>
</body></html>
"""

MESSAGE_THREAD_HTML = """\
<html>
<body>
<div id="message-thread" data-thread-id="101">
  <h2 class="thread-participant"><a href="/jim-stone/">Jim Stone</a></h2>
  <div class="message">
    <span class="message-sender">Jim Stone</span>
    <div class="message-body">Hey, want to jam this weekend?</div>
    <time class="message-time" datetime="2025-03-15T10:30:00">10:30 AM</time>
  </div>
  <div class="message">
    <span class="message-sender">You</span>
    <div class="message-body">Sure, Saturday works for me!</div>
    <time class="message-time" datetime="2025-03-15T11:00:00">11:00 AM</time>
  </div>
</div>
</body>
</html>
"""

EMPTY_THREAD_HTML = """\
<html><body>
<div id="message-thread" data-thread-id="999">
  <h2 class="thread-participant"><a href="/nobody/">Nobody</a></h2>
</div>
</body></html>
"""

SEND_PAGE_HTML = """\
<html>
<body>
<form action="/account/messages/send/jim-stone/" method="post">
  <input type="hidden" name="csrfmiddlewaretoken" value="abc123" />
  <textarea name="body"></textarea>
  <button type="submit">Send</button>
</form>
</body>
</html>
"""

PREMIER_REQUIRED_HTML = """\
<html>
<body>
<div class="upgrade-notice">
  <p>You must be a Premier Member to send messages. Upgrade now!</p>
</div>
</body>
</html>
"""


# ---------------------------------------------------------------------------
# Parser tests
# ---------------------------------------------------------------------------


class TestParseMessagesList:
    def test_parses_threads(self):
        threads = parse_messages_list(MESSAGES_LIST_HTML)
        assert len(threads) == 2
        assert threads[0].thread_id == "101"
        assert threads[0].participant == "Jim Stone"
        assert threads[0].participant_slug == "jim-stone"
        assert threads[0].last_message_preview == "Hey, want to jam?"
        assert threads[0].last_message_time is not None
        assert threads[1].thread_id == "102"
        assert threads[1].participant == "Jane Doe"
        assert threads[1].participant_slug == "jane-doe"

    def test_empty_list(self):
        threads = parse_messages_list(EMPTY_MESSAGES_HTML)
        assert threads == []

    def test_returns_message_thread_models(self):
        threads = parse_messages_list(MESSAGES_LIST_HTML)
        for t in threads:
            assert isinstance(t, MessageThread)


class TestParseMessageThread:
    def test_parses_conversation(self):
        thread = parse_message_thread(MESSAGE_THREAD_HTML)
        assert thread.thread_id == "101"
        assert thread.participant == "Jim Stone"
        assert thread.participant_slug == "jim-stone"
        assert len(thread.messages) == 2
        assert thread.messages[0].sender == "Jim Stone"
        assert thread.messages[0].body == "Hey, want to jam this weekend?"
        assert thread.messages[0].timestamp is not None
        assert thread.messages[1].sender == "You"
        assert thread.messages[1].body == "Sure, Saturday works for me!"

    def test_empty_thread(self):
        thread = parse_message_thread(EMPTY_THREAD_HTML)
        assert thread.thread_id == "999"
        assert thread.messages == []

    def test_returns_message_thread_model(self):
        thread = parse_message_thread(MESSAGE_THREAD_HTML)
        assert isinstance(thread, MessageThread)


# ---------------------------------------------------------------------------
# CLI command tests
# ---------------------------------------------------------------------------


@responses.activate
def test_messages_list_table():
    """messages list fetches and displays threads."""
    responses.add(
        responses.GET,
        f"{BASE_URL}/account/messages/",
        body=MESSAGES_LIST_HTML,
        status=200,
    )
    runner = CliRunner()
    result = runner.invoke(messages, ["list"])
    assert result.exit_code == 0
    assert "Jim Stone" in result.output
    assert "Jane Doe" in result.output


@responses.activate
def test_messages_list_json():
    """messages list --format json outputs JSON."""
    responses.add(
        responses.GET,
        f"{BASE_URL}/account/messages/",
        body=MESSAGES_LIST_HTML,
        status=200,
    )
    runner = CliRunner()
    result = runner.invoke(messages, ["list", "--format", "json"])
    assert result.exit_code == 0
    assert '"thread_id"' in result.output


@responses.activate
def test_messages_list_raw():
    """messages list --raw prints raw HTML."""
    responses.add(
        responses.GET,
        f"{BASE_URL}/account/messages/",
        body=MESSAGES_LIST_HTML,
        status=200,
    )
    runner = CliRunner()
    result = runner.invoke(messages, ["list", "--raw"])
    assert result.exit_code == 0
    assert "<div" in result.output


@responses.activate
def test_messages_list_empty():
    """messages list with no threads shows info message."""
    responses.add(
        responses.GET,
        f"{BASE_URL}/account/messages/",
        body=EMPTY_MESSAGES_HTML,
        status=200,
    )
    runner = CliRunner()
    result = runner.invoke(messages, ["list"])
    assert result.exit_code == 0
    assert "No message threads found" in result.output


@responses.activate
def test_messages_read_table():
    """messages read <thread_id> displays conversation."""
    responses.add(
        responses.GET,
        f"{BASE_URL}/account/messages/101/",
        body=MESSAGE_THREAD_HTML,
        status=200,
    )
    runner = CliRunner()
    result = runner.invoke(messages, ["read", "101"])
    assert result.exit_code == 0
    assert "Jim Stone" in result.output


@responses.activate
def test_messages_read_json():
    """messages read --format json outputs JSON."""
    responses.add(
        responses.GET,
        f"{BASE_URL}/account/messages/101/",
        body=MESSAGE_THREAD_HTML,
        status=200,
    )
    runner = CliRunner()
    result = runner.invoke(messages, ["read", "101", "--format", "json"])
    assert result.exit_code == 0
    assert '"messages"' in result.output


@responses.activate
def test_messages_read_raw():
    """messages read --raw prints raw HTML."""
    responses.add(
        responses.GET,
        f"{BASE_URL}/account/messages/101/",
        body=MESSAGE_THREAD_HTML,
        status=200,
    )
    runner = CliRunner()
    result = runner.invoke(messages, ["read", "101", "--raw"])
    assert result.exit_code == 0
    assert "<div" in result.output


@responses.activate
def test_messages_read_empty():
    """messages read with empty thread shows info message."""
    responses.add(
        responses.GET,
        f"{BASE_URL}/account/messages/999/",
        body=EMPTY_THREAD_HTML,
        status=200,
    )
    runner = CliRunner()
    result = runner.invoke(messages, ["read", "999"])
    assert result.exit_code == 0
    assert "No messages found" in result.output


@responses.activate
def test_messages_send_success():
    """messages send <slug> --body sends a message."""
    responses.add(
        responses.GET,
        f"{BASE_URL}/account/messages/send/jim-stone/",
        body=SEND_PAGE_HTML,
        status=200,
    )
    responses.add(
        responses.POST,
        f"{BASE_URL}/account/messages/send/jim-stone/",
        status=200,
    )
    runner = CliRunner()
    result = runner.invoke(messages, ["send", "jim-stone", "--body", "Hey!"])
    assert result.exit_code == 0
    assert "Message sent to jim-stone" in result.output


@responses.activate
def test_messages_send_premier_required():
    """messages send raises PremierRequiredError when not premier."""
    responses.add(
        responses.GET,
        f"{BASE_URL}/account/messages/send/jim-stone/",
        body=PREMIER_REQUIRED_HTML,
        status=200,
    )
    runner = CliRunner()
    result = runner.invoke(messages, ["send", "jim-stone", "--body", "Hey!"])
    assert result.exit_code != 0
    assert isinstance(result.exception, PremierRequiredError)


@responses.activate
def test_messages_send_failure():
    """messages send fails on server error."""
    responses.add(
        responses.GET,
        f"{BASE_URL}/account/messages/send/bad-slug/",
        body=SEND_PAGE_HTML,
        status=200,
    )
    responses.add(
        responses.POST,
        f"{BASE_URL}/account/messages/send/bad-slug/",
        status=400,
    )
    runner = CliRunner()
    result = runner.invoke(messages, ["send", "bad-slug", "--body", "Hey!"])
    assert result.exit_code != 0
