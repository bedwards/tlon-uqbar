"""Tests for member view and actions commands."""

from __future__ import annotations

import responses
from click.testing import CliRunner

from bandmix_cli.client import BASE_URL
from bandmix_cli.commands.member import member
from bandmix_cli.models import MemberProfile
from bandmix_cli.parser import parse_member_profile

# ---------------------------------------------------------------------------
# Sample HTML fixtures
# ---------------------------------------------------------------------------

MEMBER_PROFILE_HTML = """\
<html>
<body>
<h1 class="profile-name">Jim Stone</h1>
<ul class="profile-info">
  <li><strong>Member Since:</strong> Jan 2020</li>
  <li><strong>Last Active:</strong> 2 days ago</li>
  <li><strong>Commitment Level:</strong> Very Committed</li>
  <li><strong>Years Playing:</strong> 25</li>
  <li><strong>Gigs Played:</strong> Over 100</li>
  <li><strong>Practice Frequency:</strong> 2-3 times per week</li>
  <li><strong>Gig Availability:</strong> 2-3 nights a week</li>
  <li><strong>Most Available:</strong> Nights</li>
</ul>
<ul class="profile-instruments">
  <li>Acoustic Guitar (Advanced)</li>
  <li>Vocalist (Expert)</li>
</ul>
<ul class="profile-genres">
  <li>Country</li>
  <li>Folk</li>
</ul>
<ul class="profile-seeking">
  <li>Drums</li>
  <li>Bass Guitar</li>
</ul>
<div class="profile-description">Singer-songwriter from Texas.</div>
<div class="profile-influences">Willie Nelson, Merle Haggard</div>
<div class="profile-equipment">Taylor 814ce, Shure SM58</div>
<div class="profile-location">Austin, TX</div>
<div class="profile-images">
  <img src="https://cdn.bandmix.com/img1.jpg" />
  <img src="https://cdn.bandmix.com/img2.jpg" />
</div>
<ul class="profile-audio">
  <li>Dusty Roads</li>
  <li>Open Highway</li>
</ul>
<ul class="profile-videos">
  <li>Live at ACL</li>
</ul>
</body>
</html>
"""

MINIMAL_PROFILE_HTML = """\
<html><body>
<h1>Unknown User</h1>
</body></html>
"""


# ---------------------------------------------------------------------------
# Parser tests
# ---------------------------------------------------------------------------


class TestParseMemberProfile:
    def test_full_profile(self):
        profile = parse_member_profile(MEMBER_PROFILE_HTML, "jim-stone")
        assert profile.screen_name == "Jim Stone"
        assert profile.slug == "jim-stone"
        assert profile.member_since == "Jan 2020"
        assert profile.last_active == "2 days ago"
        assert profile.commitment_level is not None
        assert profile.commitment_level.value == "Very Committed"
        assert profile.years_playing is not None
        assert profile.years_playing.value == "25"
        assert profile.gigs_played is not None
        assert profile.gigs_played.value == "Over 100"
        assert profile.practice_frequency is not None
        assert profile.practice_frequency.value == "2-3 times per week"
        assert profile.gig_availability is not None
        assert profile.gig_availability.value == "2-3 nights a week"
        assert profile.most_available is not None
        assert profile.most_available.value == "Nights"

        assert len(profile.instruments) == 2
        assert profile.instruments[0].instrument.value == "Acoustic Guitar"
        assert profile.instruments[0].experience is not None
        assert profile.instruments[0].experience.value == "Advanced"
        assert profile.instruments[1].instrument.value == "Vocalist"
        assert profile.instruments[1].experience is not None
        assert profile.instruments[1].experience.value == "Expert"

        assert [g.value for g in profile.genres] == ["Country", "Folk"]
        assert [s.value for s in profile.seeking] == ["Drums", "Bass Guitar"]

        assert profile.description == "Singer-songwriter from Texas."
        assert profile.influences == "Willie Nelson, Merle Haggard"
        assert profile.equipment == "Taylor 814ce, Shure SM58"
        assert profile.location == "Austin, TX"

        assert len(profile.images) == 2
        assert profile.images[0] == "https://cdn.bandmix.com/img1.jpg"

        assert profile.audio_tracks == ["Dusty Roads", "Open Highway"]
        assert profile.videos == ["Live at ACL"]

    def test_minimal_profile(self):
        profile = parse_member_profile(MINIMAL_PROFILE_HTML, "unknown")
        assert profile.screen_name == "Unknown User"
        assert profile.slug == "unknown"
        assert profile.instruments == []
        assert profile.genres == []
        assert profile.description is None

    def test_returns_member_profile_model(self):
        profile = parse_member_profile(MEMBER_PROFILE_HTML, "jim-stone")
        assert isinstance(profile, MemberProfile)


# ---------------------------------------------------------------------------
# CLI command tests
# ---------------------------------------------------------------------------


@responses.activate
def test_member_view_table():
    """member view <slug> fetches and displays profile."""
    responses.add(
        responses.GET,
        f"{BASE_URL}/jim-stone/",
        body=MEMBER_PROFILE_HTML,
        status=200,
    )
    runner = CliRunner()
    result = runner.invoke(member, ["view", "jim-stone"])
    assert result.exit_code == 0
    assert "Jim Stone" in result.output


@responses.activate
def test_member_view_json():
    """member view --format json outputs JSON."""
    responses.add(
        responses.GET,
        f"{BASE_URL}/jim-stone/",
        body=MEMBER_PROFILE_HTML,
        status=200,
    )
    runner = CliRunner()
    result = runner.invoke(member, ["view", "jim-stone", "--format", "json"])
    assert result.exit_code == 0
    assert '"screen_name"' in result.output


@responses.activate
def test_member_view_raw():
    """member view --raw prints raw HTML."""
    responses.add(
        responses.GET,
        f"{BASE_URL}/jim-stone/",
        body=MEMBER_PROFILE_HTML,
        status=200,
    )
    runner = CliRunner()
    result = runner.invoke(member, ["view", "jim-stone", "--raw"])
    assert result.exit_code == 0
    assert "<h1" in result.output


@responses.activate
def test_member_add_to_list_success():
    """member add-to-list <slug> succeeds on 200."""
    responses.add(
        responses.POST,
        f"{BASE_URL}/account/bookmarks/add/jim-stone/",
        status=200,
    )
    runner = CliRunner()
    result = runner.invoke(member, ["add-to-list", "jim-stone"])
    assert result.exit_code == 0
    assert "Added jim-stone to Music List" in result.output


@responses.activate
def test_member_add_to_list_failure():
    """member add-to-list <slug> fails on 4xx."""
    responses.add(
        responses.POST,
        f"{BASE_URL}/account/bookmarks/add/bad-slug/",
        status=404,
    )
    runner = CliRunner()
    result = runner.invoke(member, ["add-to-list", "bad-slug"])
    assert result.exit_code != 0


@responses.activate
def test_member_remove_from_list_success():
    """member remove-from-list <slug> succeeds on 200."""
    responses.add(
        responses.POST,
        f"{BASE_URL}/account/bookmarks/remove/jim-stone/",
        status=200,
    )
    runner = CliRunner()
    result = runner.invoke(member, ["remove-from-list", "jim-stone"])
    assert result.exit_code == 0
    assert "Removed jim-stone from Music List" in result.output


@responses.activate
def test_member_hide_success():
    """member hide <slug> succeeds on 200."""
    responses.add(
        responses.POST,
        f"{BASE_URL}/account/hidden/add/jim-stone/",
        status=200,
    )
    runner = CliRunner()
    result = runner.invoke(member, ["hide", "jim-stone"])
    assert result.exit_code == 0
    assert "Hidden jim-stone" in result.output


@responses.activate
def test_member_hide_failure():
    """member hide <slug> fails on 4xx."""
    responses.add(
        responses.POST,
        f"{BASE_URL}/account/hidden/add/bad-slug/",
        status=400,
    )
    runner = CliRunner()
    result = runner.invoke(member, ["hide", "bad-slug"])
    assert result.exit_code != 0


@responses.activate
def test_member_unhide_success():
    """member unhide <slug> succeeds on 200."""
    responses.add(
        responses.POST,
        f"{BASE_URL}/account/hidden/remove/jim-stone/",
        status=200,
    )
    runner = CliRunner()
    result = runner.invoke(member, ["unhide", "jim-stone"])
    assert result.exit_code == 0
    assert "Unhidden jim-stone" in result.output


@responses.activate
def test_member_unhide_failure():
    """member unhide <slug> fails on 4xx."""
    responses.add(
        responses.POST,
        f"{BASE_URL}/account/hidden/remove/bad-slug/",
        status=400,
    )
    runner = CliRunner()
    result = runner.invoke(member, ["unhide", "bad-slug"])
    assert result.exit_code != 0
