"""Tests for remaining commands: matches, feed, photos, music, videos,
calendar, seeking, musiclist, hidden, settings."""

from __future__ import annotations

import responses
from click.testing import CliRunner

from bandmix_cli.client import BASE_URL
from bandmix_cli.commands.calendar import calendar
from bandmix_cli.commands.feed import feed
from bandmix_cli.commands.hidden import hidden
from bandmix_cli.commands.matches import matches
from bandmix_cli.commands.music import music
from bandmix_cli.commands.musiclist import musiclist
from bandmix_cli.commands.photos import photos
from bandmix_cli.commands.seeking import seeking
from bandmix_cli.commands.settings import settings
from bandmix_cli.commands.videos import videos
from bandmix_cli.models import (
    AudioTrack,
    CalendarEvent,
    DashboardSettings,
    EmailSettings,
    FeedEntry,
    Match,
    MatchMailerSettings,
    Photo,
    SeekingStatus,
    Video,
)
from bandmix_cli.parser import (
    parse_calendar,
    parse_feed,
    parse_hidden,
    parse_matches,
    parse_music,
    parse_musiclist,
    parse_photos,
    parse_seeking,
    parse_settings_dashboard,
    parse_settings_email,
    parse_settings_matchmailer,
    parse_videos,
)

# ---------------------------------------------------------------------------
# HTML fixtures
# ---------------------------------------------------------------------------

MATCHES_HTML = """\
<html><body>
<div class="match-card">
  <a class="screen-name" href="/jim-stone/">Jim Stone</a>
  <span class="location">Austin, TX</span>
  <span class="instruments">Acoustic Guitar, Vocalist</span>
  <span class="genres">Country, Folk</span>
  <span class="last-active">2 days ago</span>
  <span class="snippet">Singer-songwriter</span>
</div>
<div class="match-card">
  <a class="screen-name" href="/jane-doe/">Jane Doe</a>
  <span class="location">Dallas, TX</span>
  <span class="instruments">Drums</span>
</div>
</body></html>
"""

FEED_HTML = """\
<html><body>
<div class="feed-item" data-feed-id="101">
  <a class="feed-user" href="/jim-stone/">Jim Stone</a>
  <span class="location">Austin, TX</span>
  <span class="action-type">joined</span>
  <span class="feed-detail">Joined BandMix</span>
</div>
<div class="feed-item" data-feed-id="102">
  <a class="feed-user" href="/jane-doe/">Jane Doe</a>
  <span class="action-type">uploaded_images</span>
</div>
</body></html>
"""

PHOTOS_HTML = """\
<html><body>
<div class="photo-item" data-photo-id="p1" data-main="true">
  <img src="https://cdn.bandmix.com/img1.jpg" />
</div>
<div class="photo-item" data-photo-id="p2">
  <img src="https://cdn.bandmix.com/img2.jpg" />
</div>
<input type="hidden" name="csrfmiddlewaretoken" value="csrf123" />
</body></html>
"""

MUSIC_HTML = """\
<html><body>
<div class="audio-track" data-track-id="t1">
  <span class="track-title">Dusty Roads</span>
  <span class="track-type">mp3</span>
  <span class="track-size">4.2 MB</span>
</div>
<div class="audio-track" data-track-id="t2">
  <span class="track-title">Open Highway</span>
  <span class="track-type">wav</span>
  <span class="track-size">12.1 MB</span>
  <span class="mastered"></span>
</div>
<input type="hidden" name="csrfmiddlewaretoken" value="csrf123" />
</body></html>
"""

VIDEOS_HTML = """\
<html><body>
<div class="video-item" data-video-id="v1">
  <span class="video-title">Live at ACL</span>
  <a class="video-link" href="https://youtube.com/watch?v=abc123">Watch</a>
</div>
<div class="video-item" data-video-id="v2">
  <span class="video-title">Studio Session</span>
  <a class="video-link" href="https://youtube.com/watch?v=def456">Watch</a>
  <span class="hidden"></span>
</div>
<input type="hidden" name="csrfmiddlewaretoken" value="csrf123" />
</body></html>
"""

CALENDAR_HTML = """\
<html><body>
<div class="calendar-event" data-event-id="e1">
  <span class="event-title">Open Mic</span>
  <span class="event-date">2026-04-14</span>
  <span class="event-time">22:30</span>
  <span class="event-description">Open mic at Common Grounds</span>
</div>
<input type="hidden" name="csrfmiddlewaretoken" value="csrf123" />
</body></html>
"""

SEEKING_HTML = """\
<html><body>
<input type="checkbox" name="join_band" checked />
<input type="checkbox" name="instruments" value="Drums" checked />
<input type="checkbox" name="instruments" value="Bass Guitar" checked />
<input type="checkbox" name="instruments" value="Lead Guitar" />
<input type="hidden" name="csrfmiddlewaretoken" value="csrf123" />
</body></html>
"""

MUSICLIST_HTML = """\
<html><body>
<div class="bookmark-item">
  <a href="/jim-stone/">Jim Stone</a>
  <span class="location">Austin, TX</span>
</div>
<div class="bookmark-item">
  <a href="/jane-doe/">Jane Doe</a>
  <span class="location">Dallas, TX</span>
</div>
</body></html>
"""

HIDDEN_HTML = """\
<html><body>
<div class="hidden-item">
  <a href="/spammer123/">Spammer</a>
  <span class="location">Unknown</span>
</div>
</body></html>
"""

EMAIL_SETTINGS_HTML = """\
<html><body>
<input type="radio" name="newsletters" value="enabled" checked />
<input type="radio" name="newsletters" value="disabled" />
<input type="radio" name="user_views" value="enabled" checked />
<input type="radio" name="user_views" value="disabled" />
<input type="radio" name="user_visited" value="disabled" checked />
<input type="radio" name="user_music_lists" value="enabled" checked />
<input type="radio" name="general_notifications" value="enabled" checked />
<input type="radio" name="format" value="html" checked />
<input type="hidden" name="csrfmiddlewaretoken" value="csrf123" />
</body></html>
"""

MATCHMAILER_HTML = """\
<html><body>
<input type="checkbox" name="enabled" checked />
<input type="text" name="radius" value="50" />
<input type="text" name="age_from" value="25" />
<input type="text" name="age_to" value="55" />
<input type="checkbox" name="filter_instrument" checked />
<input type="checkbox" name="filter_genre" />
<input type="radio" name="recommendations" value="enabled" checked />
<input type="radio" name="additional_local" value="disabled" checked />
<input type="hidden" name="csrfmiddlewaretoken" value="csrf123" />
</body></html>
"""

DASHBOARD_HTML = """\
<html><body>
<input type="checkbox" name="show_matches" checked />
<input type="text" name="radius" value="100" />
<input type="text" name="age_from" value="20" />
<input type="text" name="age_to" value="60" />
<input type="hidden" name="csrfmiddlewaretoken" value="csrf123" />
</body></html>
"""

EMPTY_HTML = "<html><body></body></html>"

PASSWORD_HTML = """\
<html><body>
<input type="hidden" name="csrfmiddlewaretoken" value="csrf123" />
</body></html>
"""


# ====================================================================
# Parser tests
# ====================================================================


class TestParseMatches:
    def test_parse_matches(self):
        results = parse_matches(MATCHES_HTML)
        assert len(results) == 2
        assert isinstance(results[0], Match)
        assert results[0].screen_name == "Jim Stone"
        assert results[0].slug == "jim-stone"
        assert results[0].location == "Austin, TX"
        assert results[1].screen_name == "Jane Doe"

    def test_parse_matches_empty(self):
        results = parse_matches(EMPTY_HTML)
        assert results == []


class TestParseFeed:
    def test_parse_feed(self):
        entries = parse_feed(FEED_HTML)
        assert len(entries) == 2
        assert isinstance(entries[0], FeedEntry)
        assert entries[0].feed_id == "101"
        assert entries[0].user_screen_name == "Jim Stone"
        assert entries[0].user_slug == "jim-stone"
        assert entries[0].detail == "Joined BandMix"
        assert entries[1].feed_id == "102"

    def test_parse_feed_empty(self):
        entries = parse_feed(EMPTY_HTML)
        assert entries == []


class TestParsePhotos:
    def test_parse_photos(self):
        photo_list = parse_photos(PHOTOS_HTML)
        assert len(photo_list) == 2
        assert isinstance(photo_list[0], Photo)
        assert photo_list[0].photo_id == "p1"
        assert photo_list[0].is_main is True
        assert photo_list[1].photo_id == "p2"
        assert photo_list[1].is_main is False

    def test_parse_photos_empty(self):
        result = parse_photos(EMPTY_HTML)
        assert result == []


class TestParseMusic:
    def test_parse_music(self):
        tracks = parse_music(MUSIC_HTML)
        assert len(tracks) == 2
        assert isinstance(tracks[0], AudioTrack)
        assert tracks[0].track_id == "t1"
        assert tracks[0].title == "Dusty Roads"
        assert tracks[0].track_type == "mp3"
        assert tracks[0].size == "4.2 MB"
        assert tracks[0].has_mastered is False
        assert tracks[1].has_mastered is True

    def test_parse_music_empty(self):
        tracks = parse_music(EMPTY_HTML)
        assert tracks == []


class TestParseVideos:
    def test_parse_videos(self):
        video_list = parse_videos(VIDEOS_HTML)
        assert len(video_list) == 2
        assert isinstance(video_list[0], Video)
        assert video_list[0].video_id == "v1"
        assert video_list[0].title == "Live at ACL"
        assert video_list[0].youtube_url == "https://youtube.com/watch?v=abc123"
        assert video_list[0].visible is True
        assert video_list[1].visible is False

    def test_parse_videos_empty(self):
        vids = parse_videos(EMPTY_HTML)
        assert vids == []


class TestParseCalendar:
    def test_parse_calendar(self):
        events = parse_calendar(CALENDAR_HTML)
        assert len(events) == 1
        assert isinstance(events[0], CalendarEvent)
        assert events[0].event_id == "e1"
        assert events[0].title == "Open Mic"
        assert str(events[0].date) == "2026-04-14"
        assert events[0].time == "22:30"
        assert events[0].description == "Open mic at Common Grounds"

    def test_parse_calendar_empty(self):
        events = parse_calendar(EMPTY_HTML)
        assert events == []


class TestParseSeeking:
    def test_parse_seeking(self):
        status = parse_seeking(SEEKING_HTML)
        assert isinstance(status, SeekingStatus)
        assert status.join_band is True
        assert len(status.instruments) == 2
        assert status.instruments[0].value == "Drums"
        assert status.instruments[1].value == "Bass Guitar"

    def test_parse_seeking_empty(self):
        status = parse_seeking(EMPTY_HTML)
        assert status.join_band is False
        assert status.instruments == []


class TestParseMusicList:
    def test_parse_musiclist(self):
        results = parse_musiclist(MUSICLIST_HTML)
        assert len(results) == 2
        assert results[0].screen_name == "Jim Stone"
        assert results[0].slug == "jim-stone"
        assert results[0].location == "Austin, TX"

    def test_parse_musiclist_empty(self):
        results = parse_musiclist(EMPTY_HTML)
        assert results == []


class TestParseHidden:
    def test_parse_hidden(self):
        results = parse_hidden(HIDDEN_HTML)
        assert len(results) == 1
        assert results[0].screen_name == "Spammer"
        assert results[0].slug == "spammer123"

    def test_parse_hidden_empty(self):
        results = parse_hidden(EMPTY_HTML)
        assert results == []


class TestParseEmailSettings:
    def test_parse_settings_email(self):
        s = parse_settings_email(EMAIL_SETTINGS_HTML)
        assert isinstance(s, EmailSettings)
        assert s.newsletters is not None
        assert s.newsletters.value == "enabled"
        assert s.user_views is not None
        assert s.user_views.value == "enabled"
        assert s.user_visited is not None
        assert s.user_visited.value == "disabled"
        assert s.format is not None
        assert s.format.value == "html"


class TestParseMatchMailer:
    def test_parse_settings_matchmailer(self):
        s = parse_settings_matchmailer(MATCHMAILER_HTML)
        assert isinstance(s, MatchMailerSettings)
        assert s.enabled is True
        assert s.radius == 50
        assert s.age_from == 25
        assert s.age_to == 55
        assert s.filter_instrument is True
        assert s.filter_genre is False
        assert s.recommendations is not None
        assert s.recommendations.value == "enabled"
        assert s.additional_local is not None
        assert s.additional_local.value == "disabled"


class TestParseDashboard:
    def test_parse_settings_dashboard(self):
        s = parse_settings_dashboard(DASHBOARD_HTML)
        assert isinstance(s, DashboardSettings)
        assert s.show_matches is True
        assert s.radius == 100
        assert s.age_from == 20
        assert s.age_to == 60


# ====================================================================
# CLI command tests
# ====================================================================


class TestMatchesCommand:
    @responses.activate
    def test_list_matches(self):
        responses.add(
            responses.GET,
            f"{BASE_URL}/account/connections/",
            body=MATCHES_HTML,
            status=200,
        )
        runner = CliRunner()
        result = runner.invoke(matches, ["list"])
        assert result.exit_code == 0
        assert "Jim Stone" in result.output

    @responses.activate
    def test_list_matches_new_members(self):
        responses.add(
            responses.GET,
            f"{BASE_URL}/account/connections/",
            body=MATCHES_HTML,
            status=200,
        )
        runner = CliRunner()
        result = runner.invoke(matches, ["list", "--type", "new-members"])
        assert result.exit_code == 0

    @responses.activate
    def test_list_matches_empty(self):
        responses.add(
            responses.GET,
            f"{BASE_URL}/account/connections/",
            body=EMPTY_HTML,
            status=200,
        )
        runner = CliRunner()
        result = runner.invoke(matches, ["list"])
        assert result.exit_code == 0
        assert "No matches found" in result.output


class TestFeedCommand:
    @responses.activate
    def test_list_feed(self):
        responses.add(
            responses.GET,
            f"{BASE_URL}/account/feeds-load/",
            body=FEED_HTML,
            status=200,
        )
        runner = CliRunner()
        result = runner.invoke(feed, ["list"])
        assert result.exit_code == 0
        assert "Jim Stone" in result.output

    @responses.activate
    def test_list_feed_with_limit(self):
        responses.add(
            responses.GET,
            f"{BASE_URL}/account/feeds-load/",
            body=FEED_HTML,
            status=200,
        )
        runner = CliRunner()
        result = runner.invoke(feed, ["list", "--limit", "1"])
        assert result.exit_code == 0

    @responses.activate
    def test_feed_like(self):
        responses.add(
            responses.POST,
            f"{BASE_URL}/account/feeds-load-comments/",
            status=200,
        )
        runner = CliRunner()
        result = runner.invoke(feed, ["like", "101"])
        assert result.exit_code == 0
        assert "Liked" in result.output

    @responses.activate
    def test_feed_unlike(self):
        responses.add(
            responses.POST,
            f"{BASE_URL}/account/feeds-load-comments/",
            status=200,
        )
        runner = CliRunner()
        result = runner.invoke(feed, ["unlike", "101"])
        assert result.exit_code == 0
        assert "Unliked" in result.output


class TestPhotosCommand:
    @responses.activate
    def test_list_photos(self):
        responses.add(
            responses.GET,
            f"{BASE_URL}/account/images/",
            body=PHOTOS_HTML,
            status=200,
        )
        runner = CliRunner()
        result = runner.invoke(photos, ["list"])
        assert result.exit_code == 0
        assert "p1" in result.output

    @responses.activate
    def test_set_main(self):
        responses.add(
            responses.GET,
            f"{BASE_URL}/account/images/",
            body=PHOTOS_HTML,
            status=200,
        )
        responses.add(responses.POST, f"{BASE_URL}/account/images/", status=200)
        runner = CliRunner()
        result = runner.invoke(photos, ["set-main", "p1"])
        assert result.exit_code == 0
        assert "Set photo p1 as main" in result.output

    @responses.activate
    def test_delete_photo(self):
        responses.add(
            responses.GET,
            f"{BASE_URL}/account/images/",
            body=PHOTOS_HTML,
            status=200,
        )
        responses.add(responses.POST, f"{BASE_URL}/account/images/", status=200)
        runner = CliRunner()
        result = runner.invoke(photos, ["delete", "p1"])
        assert result.exit_code == 0
        assert "Deleted photo p1" in result.output

    @responses.activate
    def test_reorder_photos(self):
        responses.add(responses.POST, f"{BASE_URL}/ajax/sort-images/", status=200)
        runner = CliRunner()
        result = runner.invoke(photos, ["reorder", "p2", "p1"])
        assert result.exit_code == 0
        assert "Photos reordered" in result.output


class TestMusicCommand:
    @responses.activate
    def test_list_tracks(self):
        responses.add(
            responses.GET,
            f"{BASE_URL}/account/audio/",
            body=MUSIC_HTML,
            status=200,
        )
        runner = CliRunner()
        result = runner.invoke(music, ["list"])
        assert result.exit_code == 0
        assert "Dusty Roads" in result.output

    @responses.activate
    def test_delete_track(self):
        responses.add(
            responses.GET,
            f"{BASE_URL}/account/audio/",
            body=MUSIC_HTML,
            status=200,
        )
        responses.add(responses.POST, f"{BASE_URL}/account/audio/", status=200)
        runner = CliRunner()
        result = runner.invoke(music, ["delete", "t1"])
        assert result.exit_code == 0
        assert "Deleted track t1" in result.output

    @responses.activate
    def test_master(self):
        responses.add(responses.POST, f"{BASE_URL}/ajax/audio-mastering/", status=200)
        runner = CliRunner()
        result = runner.invoke(music, ["master", "t1"])
        assert result.exit_code == 0
        assert "Mastering submitted" in result.output

    @responses.activate
    def test_master_status(self):
        responses.add(
            responses.GET,
            f"{BASE_URL}/ajax/audio-mastering-progress/",
            json={"progress": 75, "id": "t1"},
            status=200,
        )
        runner = CliRunner()
        result = runner.invoke(music, ["master-status", "t1"])
        assert result.exit_code == 0
        assert "75" in result.output


class TestVideosCommand:
    @responses.activate
    def test_list_videos(self):
        responses.add(
            responses.GET,
            f"{BASE_URL}/account/video/",
            body=VIDEOS_HTML,
            status=200,
        )
        runner = CliRunner()
        result = runner.invoke(videos, ["list"])
        assert result.exit_code == 0
        assert "Live at ACL" in result.output

    @responses.activate
    def test_add_video(self):
        responses.add(
            responses.GET,
            f"{BASE_URL}/account/video/",
            body=VIDEOS_HTML,
            status=200,
        )
        responses.add(responses.POST, f"{BASE_URL}/account/video/", status=200)
        runner = CliRunner()
        result = runner.invoke(
            videos,
            [
                "add",
                "--title",
                "My Video",
                "--url",
                "https://youtube.com/watch?v=xyz",
            ],
        )
        assert result.exit_code == 0
        assert "Added video" in result.output

    @responses.activate
    def test_delete_video(self):
        responses.add(
            responses.GET,
            f"{BASE_URL}/account/video/",
            body=VIDEOS_HTML,
            status=200,
        )
        responses.add(responses.POST, f"{BASE_URL}/account/video/", status=200)
        runner = CliRunner()
        result = runner.invoke(videos, ["delete", "v1"])
        assert result.exit_code == 0
        assert "Deleted video v1" in result.output

    @responses.activate
    def test_reorder_videos(self):
        responses.add(responses.POST, f"{BASE_URL}/ajax/reorder-videos/", status=200)
        runner = CliRunner()
        result = runner.invoke(videos, ["reorder", "v2", "v1"])
        assert result.exit_code == 0
        assert "Videos reordered" in result.output


class TestCalendarCommand:
    @responses.activate
    def test_list_events(self):
        responses.add(
            responses.GET,
            f"{BASE_URL}/account/calendar/",
            body=CALENDAR_HTML,
            status=200,
        )
        runner = CliRunner()
        result = runner.invoke(calendar, ["list"])
        assert result.exit_code == 0
        assert "Open Mic" in result.output

    @responses.activate
    def test_add_event(self):
        responses.add(
            responses.GET,
            f"{BASE_URL}/account/calendar/",
            body=CALENDAR_HTML,
            status=200,
        )
        responses.add(responses.POST, f"{BASE_URL}/account/calendar/", status=200)
        runner = CliRunner()
        result = runner.invoke(
            calendar,
            [
                "add",
                "--date",
                "2026-05-01",
                "--time",
                "20:00",
                "--title",
                "Gig Night",
            ],
        )
        assert result.exit_code == 0
        assert "Added event" in result.output

    @responses.activate
    def test_delete_event(self):
        responses.add(
            responses.GET,
            f"{BASE_URL}/account/calendar/",
            body=CALENDAR_HTML,
            status=200,
        )
        responses.add(responses.POST, f"{BASE_URL}/account/calendar/", status=200)
        runner = CliRunner()
        result = runner.invoke(calendar, ["delete", "e1"])
        assert result.exit_code == 0
        assert "Deleted event e1" in result.output


class TestSeekingCommand:
    @responses.activate
    def test_get_seeking(self):
        responses.add(
            responses.GET,
            f"{BASE_URL}/account/ads/",
            body=SEEKING_HTML,
            status=200,
        )
        runner = CliRunner()
        result = runner.invoke(seeking, ["get"])
        assert result.exit_code == 0
        assert "True" in result.output or "true" in result.output.lower()

    @responses.activate
    def test_set_seeking(self):
        responses.add(
            responses.GET,
            f"{BASE_URL}/account/ads/",
            body=SEEKING_HTML,
            status=200,
        )
        responses.add(responses.POST, f"{BASE_URL}/account/ads/", status=200)
        runner = CliRunner()
        result = runner.invoke(seeking, ["set", "--join-band", "true"])
        assert result.exit_code == 0
        assert "updated" in result.output.lower()


class TestMusicListCommand:
    @responses.activate
    def test_list_bookmarks(self):
        responses.add(
            responses.GET,
            f"{BASE_URL}/account/bookmarks/",
            body=MUSICLIST_HTML,
            status=200,
        )
        runner = CliRunner()
        result = runner.invoke(musiclist, ["list"])
        assert result.exit_code == 0
        assert "Jim Stone" in result.output

    @responses.activate
    def test_add_to_musiclist(self):
        responses.add(
            responses.POST,
            f"{BASE_URL}/account/bookmarks/add/jim-stone/",
            status=200,
        )
        runner = CliRunner()
        result = runner.invoke(musiclist, ["add", "jim-stone"])
        assert result.exit_code == 0
        assert "Added jim-stone" in result.output

    @responses.activate
    def test_remove_from_musiclist(self):
        responses.add(
            responses.POST,
            f"{BASE_URL}/account/bookmarks/remove/jim-stone/",
            status=200,
        )
        runner = CliRunner()
        result = runner.invoke(musiclist, ["remove", "jim-stone"])
        assert result.exit_code == 0
        assert "Removed jim-stone" in result.output


class TestHiddenCommand:
    @responses.activate
    def test_list_hidden(self):
        responses.add(
            responses.GET,
            f"{BASE_URL}/account/hidden/",
            body=HIDDEN_HTML,
            status=200,
        )
        runner = CliRunner()
        result = runner.invoke(hidden, ["list"])
        assert result.exit_code == 0
        assert "Spammer" in result.output

    @responses.activate
    def test_add_hidden(self):
        responses.add(
            responses.POST,
            f"{BASE_URL}/account/hidden/add/spammer123/",
            status=200,
        )
        runner = CliRunner()
        result = runner.invoke(hidden, ["add", "spammer123"])
        assert result.exit_code == 0
        assert "Hidden spammer123" in result.output

    @responses.activate
    def test_remove_hidden(self):
        responses.add(
            responses.POST,
            f"{BASE_URL}/account/hidden/remove/spammer123/",
            status=200,
        )
        runner = CliRunner()
        result = runner.invoke(hidden, ["remove", "spammer123"])
        assert result.exit_code == 0
        assert "Unhidden spammer123" in result.output


class TestSettingsEmailCommand:
    @responses.activate
    def test_email_get(self):
        responses.add(
            responses.GET,
            f"{BASE_URL}/account/email/",
            body=EMAIL_SETTINGS_HTML,
            status=200,
        )
        runner = CliRunner()
        result = runner.invoke(settings, ["email", "get"])
        assert result.exit_code == 0
        assert "enabled" in result.output.lower()

    @responses.activate
    def test_email_set(self):
        responses.add(
            responses.GET,
            f"{BASE_URL}/account/email/",
            body=EMAIL_SETTINGS_HTML,
            status=200,
        )
        responses.add(responses.POST, f"{BASE_URL}/account/email/", status=200)
        runner = CliRunner()
        result = runner.invoke(settings, ["email", "set", "--newsletters", "disabled"])
        assert result.exit_code == 0
        assert "updated" in result.output.lower()


class TestSettingsMatchmailerCommand:
    @responses.activate
    def test_matchmailer_get(self):
        responses.add(
            responses.GET,
            f"{BASE_URL}/account/email/",
            body=MATCHMAILER_HTML,
            status=200,
        )
        runner = CliRunner()
        result = runner.invoke(settings, ["matchmailer", "get"])
        assert result.exit_code == 0

    @responses.activate
    def test_matchmailer_set(self):
        responses.add(
            responses.GET,
            f"{BASE_URL}/account/email/",
            body=MATCHMAILER_HTML,
            status=200,
        )
        responses.add(responses.POST, f"{BASE_URL}/account/email/", status=200)
        runner = CliRunner()
        result = runner.invoke(
            settings,
            ["matchmailer", "set", "--enabled", "true", "--radius", "100"],
        )
        assert result.exit_code == 0
        assert "updated" in result.output.lower()


class TestSettingsDashboardCommand:
    @responses.activate
    def test_dashboard_get(self):
        responses.add(
            responses.GET,
            f"{BASE_URL}/account/dashboard-options/",
            body=DASHBOARD_HTML,
            status=200,
        )
        runner = CliRunner()
        result = runner.invoke(settings, ["dashboard", "get"])
        assert result.exit_code == 0

    @responses.activate
    def test_dashboard_set(self):
        responses.add(
            responses.GET,
            f"{BASE_URL}/account/dashboard-options/",
            body=DASHBOARD_HTML,
            status=200,
        )
        responses.add(
            responses.POST,
            f"{BASE_URL}/account/dashboard-options/",
            status=200,
        )
        runner = CliRunner()
        result = runner.invoke(
            settings,
            [
                "dashboard",
                "set",
                "--show-matches",
                "true",
                "--radius",
                "50",
            ],
        )
        assert result.exit_code == 0
        assert "updated" in result.output.lower()


class TestSettingsPasswordCommand:
    @responses.activate
    def test_password_update(self):
        responses.add(
            responses.GET,
            f"{BASE_URL}/account/password/",
            body=PASSWORD_HTML,
            status=200,
        )
        responses.add(responses.POST, f"{BASE_URL}/account/password/", status=200)
        runner = CliRunner()
        result = runner.invoke(
            settings,
            ["password", "update"],
            input="oldpass\nnewpass\nnewpass\n",
        )
        assert result.exit_code == 0
        assert "Password updated" in result.output
