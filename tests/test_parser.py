"""Tests for bandmix_cli.parser — HTML parsing functions."""

from datetime import date, datetime

from bandmix_cli.enums import (
    ActionType,
    Availability,
    CommitmentLevel,
    EmailFormat,
    EnabledDisabled,
    ExperienceLevel,
    Genre,
    GigFrequency,
    GigsPlayed,
    Instrument,
    PracticeFrequency,
    SearchCategory,
    YearsPlaying,
)
from bandmix_cli.parser import (
    parse_calendar,
    parse_csrf_token,
    parse_feed,
    parse_login_response,
    parse_matches,
    parse_member_profile,
    parse_message_thread,
    parse_messages_list,
    parse_music,
    parse_photos,
    parse_profile,
    parse_search_results,
    parse_seeking,
    parse_settings_email,
    parse_videos,
)


# ---------------------------------------------------------------------------
# HTML Fixtures
# ---------------------------------------------------------------------------

LOGIN_SUCCESS_HTML = """
<html><body>
  <div class="account-name">JimStone</div>
  <div id="dashboard">Welcome back!</div>
</body></html>
"""

LOGIN_FAILURE_HTML = """
<html><body>
  <form id="login-form" action="/login/">
    <div class="error-message">Invalid email or password.</div>
    <input name="email" type="text" />
    <input name="password" type="password" />
  </form>
</body></html>
"""

LOGIN_FORM_NO_ERROR_HTML = """
<html><body>
  <form id="login-form" action="/login/">
    <input name="email" type="text" />
    <input name="password" type="password" />
  </form>
</body></html>
"""

CSRF_TOKEN_HTML = """
<html><body>
  <form>
    <input type="hidden" name="csrfmiddlewaretoken" value="abc123token" />
    <input type="text" name="email" />
  </form>
</body></html>
"""

CSRF_META_HTML = """
<html>
<head><meta name="csrf-token" content="meta-token-xyz" /></head>
<body></body>
</html>
"""

PROFILE_HTML = """
<html><body>
  <form>
    <input name="screen_name" value="JimStone" />
    <input name="contact_name" value="Jim Stone" />
    <input name="city" value="Waco" />
    <input name="zip" value="76710" />
    <input name="phone" value="555-1234" />
    <input name="birthdate" value="1975-06-15" />
    <input name="address" value="123 Main St" />

    <select name="gender">
      <option>Select</option>
      <option selected>male</option>
    </select>
    <select name="state">
      <option selected>Texas</option>
    </select>
    <select name="years_playing">
      <option selected>25</option>
    </select>
    <select name="commitment_level">
      <option selected>Very Committed</option>
    </select>
    <select name="gigs_played">
      <option selected>Over 100</option>
    </select>
    <select name="practice_frequency">
      <option selected>2-3 times per week</option>
    </select>
    <select name="gig_availability">
      <option selected>2-3 nights a week</option>
    </select>
    <select name="most_available">
      <option selected>Nights</option>
    </select>

    <input type="checkbox" name="instruments" value="Vocalist" checked />
    <input type="checkbox" name="instruments" value="Acoustic Guitar" checked />
    <input type="checkbox" name="instruments" value="Lead Guitar" />

    <input type="checkbox" name="genres" value="Country" checked />
    <input type="checkbox" name="genres" value="Folk" checked />
    <input type="checkbox" name="genres" value="Americana" checked />

    <input type="checkbox" name="studio_musician" value="1" checked />
    <input type="checkbox" name="seeking_band" value="1" checked />

    <input type="checkbox" name="seeking_instruments" value="Drums" checked />
    <input type="checkbox" name="seeking_instruments" value="Bass Guitar" checked />

    <textarea name="description">Singer-songwriter from central Texas.</textarea>
    <textarea name="influences">Willie Nelson, Townes Van Zandt</textarea>
    <textarea name="equipment">Martin D-28, Shure SM58</textarea>
  </form>
</body></html>
"""

SEARCH_RESULTS_HTML = """
<html><body>
  <div class="search-result">
    <h3><a class="screen-name" href="/darrell1917056/">Darrell</a></h3>
    <span class="location">Austin, TX</span>
    <span class="zip">73301</span>
    <span class="category">Musicians</span>
    <span class="instruments">Drums, Bass Guitar</span>
    <span class="genres">Country, Rock</span>
    <span class="last-active">3 days ago</span>
    <span class="snippet">Looking to jam with country artists.</span>
    <span class="is-seeking"></span>
    <img class="profile-image" src="/img/darrell.jpg" />
    <span class="has-audio"></span>
  </div>
  <div class="search-result">
    <h3><a class="screen-name" href="/sarah42/">Sarah</a></h3>
    <span class="location">Dallas, TX</span>
    <span class="instruments">Vocalist, Piano</span>
    <span class="genres">Folk, Acoustic</span>
    <span class="last-active">1 week ago</span>
    <span class="snippet">Experienced vocalist seeking band.</span>
  </div>
  <div class="pagination">
    <span class="next"><a href="/search/?page=2">Next</a></span>
  </div>
</body></html>
"""

MEMBER_PROFILE_HTML = """
<html>
<head>
  <link rel="canonical" href="https://www.bandmix.com/darrell1917056/" />
</head>
<body>
  <h1 class="profile-name">Darrell</h1>
  <ul class="profile-info">
    <li><strong>Member Since:</strong> January 2020</li>
    <li><strong>Last Active:</strong> 3 days ago</li>
    <li><strong>Commitment Level:</strong> Very Committed</li>
    <li><strong>Years Playing:</strong> 25</li>
    <li><strong>Gigs Played:</strong> Over 100</li>
    <li><strong>Practice Frequency:</strong> 2-3 times per week</li>
    <li><strong>Gig Availability:</strong> 2-3 nights a week</li>
    <li><strong>Most Available:</strong> Nights</li>
    <li><strong>Location:</strong> Austin, TX</li>
  </ul>
  <ul class="profile-instruments">
    <li>Drums (Expert)</li>
    <li>Bass Guitar (Advanced)</li>
    <li>Vocalist (Intermediate)</li>
  </ul>
  <ul class="profile-genres">
    <li>Country</li>
    <li>Rock</li>
    <li>Southern Rock</li>
  </ul>
  <ul class="profile-seeking">
    <li>Lead Guitar</li>
    <li>Keyboard</li>
  </ul>
  <div class="profile-description">Drummer with 25 years of experience.</div>
  <div class="profile-influences">Neil Peart, John Bonham</div>
  <div class="profile-equipment">Pearl Reference kit, Zildjian cymbals</div>
  <div class="profile-images">
    <img src="/images/darrell1.jpg" />
    <img src="/images/darrell2.jpg" />
  </div>
  <ul class="profile-audio">
    <li>Dusty Roads</li>
    <li>Midnight Ride</li>
  </ul>
  <ul class="profile-videos">
    <li>Live at SXSW</li>
  </ul>
</body></html>
"""

MATCHES_HTML = """
<html><body>
  <div class="match-card">
    <a class="match-name" href="/mike_drums/">Mike</a>
    <span class="location">Houston, TX</span>
    <span class="zip">77001</span>
    <span class="instruments">Drums, Other Percussion</span>
    <span class="genres">Rock, Blues</span>
    <span class="last-active">Today</span>
    <span class="category">Musicians</span>
    <span class="snippet">Experienced drummer looking for gigs.</span>
  </div>
  <div class="match-card">
    <a class="match-name" href="/lisa_keys/">Lisa</a>
    <span class="location">San Antonio, TX</span>
    <span class="instruments">Keyboard, Piano</span>
    <span class="genres">Jazz, Blues</span>
    <span class="last-active">Yesterday</span>
    <span class="category">Musicians</span>
  </div>
</body></html>
"""

MESSAGES_LIST_HTML = """
<html><body>
  <div class="message-thread" data-thread-id="thread-101">
    <a class="participant" href="/darrell1917056/">Darrell</a>
    <span class="message-preview">Hey, want to jam sometime?</span>
    <time class="message-time" datetime="2026-03-15T14:30:00">Mar 15</time>
  </div>
  <div class="message-thread" data-thread-id="thread-102">
    <a class="participant" href="/sarah42/">Sarah</a>
    <span class="message-preview">Thanks for reaching out!</span>
    <time class="message-time" datetime="2026-03-14T09:00:00">Mar 14</time>
  </div>
</body></html>
"""

MESSAGE_THREAD_HTML = """
<html><body>
  <div class="thread-container" data-thread-id="thread-101">
    <h2 class="thread-participant">
      <a href="/darrell1917056/">Darrell</a>
    </h2>
    <div class="message">
      <span class="sender">JimStone</span>
      <span class="body">Hey Darrell, saw your profile. Want to jam?</span>
      <time class="message-time" datetime="2026-03-15T10:00:00">10:00 AM</time>
    </div>
    <div class="message">
      <span class="sender">Darrell</span>
      <span class="body">Absolutely! I'm free this weekend.</span>
      <time class="message-time" datetime="2026-03-15T14:30:00">2:30 PM</time>
    </div>
  </div>
</body></html>
"""

FEED_HTML = """
<html><body>
  <div class="feed-item" data-feed-id="feed-501">
    <a class="feed-user" href="/mike_drums/">Mike</a>
    <span class="feed-location">Houston, TX</span>
    <span class="feed-action">uploaded_music</span>
    <span class="feed-detail">Uploaded 2 new tracks</span>
    <time class="feed-time" datetime="2026-03-18T12:00:00">Mar 18</time>
  </div>
  <div class="feed-item" data-feed-id="feed-502">
    <a class="feed-user" href="/lisa_keys/">Lisa</a>
    <span class="feed-location">San Antonio, TX</span>
    <span class="feed-action">joined</span>
    <time class="feed-time" datetime="2026-03-17T08:00:00">Mar 17</time>
  </div>
</body></html>
"""

PHOTOS_HTML = """
<html><body>
  <div class="photo-item" data-photo-id="img-201" data-main="true">
    <img src="/photos/main-shot.jpg" />
    <span class="main-badge">Main</span>
  </div>
  <div class="photo-item" data-photo-id="img-202">
    <img src="/photos/stage-shot.jpg" />
  </div>
  <div class="photo-item" data-photo-id="img-203">
    <img src="/photos/studio.jpg" />
  </div>
</body></html>
"""

MUSIC_HTML = """
<html><body>
  <div class="audio-track" data-track-id="trk-301">
    <span class="track-title">Dusty Roads</span>
    <span class="track-type">mp3</span>
    <span class="track-size">4.2 MB</span>
    <span class="mastered"></span>
  </div>
  <div class="audio-track" data-track-id="trk-302">
    <span class="track-title">Midnight Ride</span>
    <span class="track-type">wav</span>
    <span class="track-size">24.1 MB</span>
  </div>
</body></html>
"""

VIDEOS_HTML = """
<html><body>
  <div class="video-item" data-video-id="vid-401">
    <span class="video-title">Live at SXSW 2025</span>
    <a class="video-link" href="https://youtube.com/watch?v=abc123">Watch</a>
  </div>
  <div class="video-item" data-video-id="vid-402">
    <span class="video-title">Studio Session</span>
    <a class="video-link" href="https://youtube.com/watch?v=def456">Watch</a>
    <span class="hidden"></span>
  </div>
</body></html>
"""

CALENDAR_HTML = """
<html><body>
  <div class="calendar-event" data-event-id="evt-601">
    <span class="event-title">Open Mic at Common Grounds</span>
    <span class="event-date">2026-05-01</span>
    <span class="event-time">20:00</span>
    <span class="event-description">Bring your acoustic!</span>
  </div>
  <div class="calendar-event" data-event-id="evt-602">
    <span class="event-title">Band Practice</span>
    <span class="event-date">2026-05-03</span>
    <span class="event-time">18:30</span>
  </div>
</body></html>
"""

SEEKING_HTML = """
<html><body>
  <form>
    <input type="checkbox" name="join_band" value="1" checked />
    <input type="checkbox" name="instruments" value="Lead Guitar" checked />
    <input type="checkbox" name="instruments" value="Drums" checked />
    <input type="checkbox" name="instruments" value="Bass Guitar" />
    <input type="checkbox" name="instruments" value="Keyboard" checked />
  </form>
</body></html>
"""

SETTINGS_EMAIL_HTML = """
<html><body>
  <form>
    <input type="radio" name="newsletters" value="enabled" checked />
    <input type="radio" name="newsletters" value="disabled" />

    <input type="radio" name="user_views" value="enabled" />
    <input type="radio" name="user_views" value="disabled" checked />

    <input type="radio" name="user_visited" value="enabled" checked />
    <input type="radio" name="user_visited" value="disabled" />

    <input type="radio" name="user_music_lists" value="enabled" checked />
    <input type="radio" name="user_music_lists" value="disabled" />

    <input type="radio" name="general_notifications" value="enabled" />
    <input type="radio" name="general_notifications" value="disabled" checked />

    <input type="radio" name="format" value="html" checked />
    <input type="radio" name="format" value="plaintext" />
  </form>
</body></html>
"""


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestParseLoginResponse:
    def test_success(self):
        result = parse_login_response(LOGIN_SUCCESS_HTML)
        assert result["success"] is True
        assert result["error"] is None
        assert result["screen_name"] == "JimStone"

    def test_failure_with_error(self):
        result = parse_login_response(LOGIN_FAILURE_HTML)
        assert result["success"] is False
        assert result["error"] == "Invalid email or password."
        assert result["screen_name"] is None

    def test_failure_form_present(self):
        result = parse_login_response(LOGIN_FORM_NO_ERROR_HTML)
        assert result["success"] is False
        assert result["error"] == "Login failed"

    def test_empty_page_defaults_to_success(self):
        result = parse_login_response("<html><body></body></html>")
        assert result["success"] is True


class TestParseCsrfToken:
    def test_hidden_input(self):
        token = parse_csrf_token(CSRF_TOKEN_HTML)
        assert token == "abc123token"

    def test_meta_tag(self):
        token = parse_csrf_token(CSRF_META_HTML)
        assert token == "meta-token-xyz"

    def test_missing_token(self):
        token = parse_csrf_token("<html><body></body></html>")
        assert token == ""


class TestParseProfile:
    def test_full_profile(self):
        profile = parse_profile(PROFILE_HTML)
        assert profile.screen_name == "JimStone"
        assert profile.contact_name == "Jim Stone"
        assert profile.city == "Waco"
        assert profile.zip == "76710"
        assert profile.phone == "555-1234"
        assert profile.address == "123 Main St"
        assert profile.birthdate == date(1975, 6, 15)
        assert profile.gender == "male"
        assert profile.state == "Texas"
        assert profile.studio_musician is True
        assert profile.seeking_band is True
        assert profile.years_playing == YearsPlaying.Y25
        assert profile.commitment_level == CommitmentLevel.VERY_COMMITTED
        assert profile.gigs_played == GigsPlayed.OVER_100
        assert profile.practice_frequency == PracticeFrequency.TWO_THREE_PER_WEEK
        assert profile.gig_availability == GigFrequency.TWO_THREE_NIGHTS
        assert profile.most_available == Availability.NIGHTS
        assert Instrument.VOCALIST in profile.instruments
        assert Instrument.ACOUSTIC_GUITAR in profile.instruments
        assert len(profile.instruments) == 2
        assert Genre.COUNTRY in profile.genres
        assert Genre.FOLK in profile.genres
        assert Genre.AMERICANA in profile.genres
        assert len(profile.genres) == 3
        assert Instrument.DRUMS in profile.seeking_instruments
        assert Instrument.BASS_GUITAR in profile.seeking_instruments
        assert profile.description == "Singer-songwriter from central Texas."
        assert profile.influences == "Willie Nelson, Townes Van Zandt"
        assert profile.equipment == "Martin D-28, Shure SM58"

    def test_empty_profile(self):
        profile = parse_profile("<html><body><form></form></body></html>")
        assert profile.screen_name == ""
        assert profile.instruments == []
        assert profile.genres == []


class TestParseSearchResults:
    def test_results_and_pagination(self):
        results, next_page = parse_search_results(SEARCH_RESULTS_HTML)
        assert len(results) == 2
        assert next_page == 2

        r0 = results[0]
        assert r0.screen_name == "Darrell"
        assert r0.slug == "darrell1917056"
        assert r0.location == "Austin, TX"
        assert r0.zip == "73301"
        assert r0.category == SearchCategory.MUSICIANS
        assert Instrument.DRUMS in r0.instruments
        assert Instrument.BASS_GUITAR in r0.instruments
        assert Genre.COUNTRY in r0.genres
        assert Genre.ROCK in r0.genres
        assert r0.last_active == "3 days ago"
        assert r0.snippet == "Looking to jam with country artists."
        assert r0.seeking is True
        assert r0.has_image is True
        assert r0.has_audio is True
        assert r0.has_video is False

        r1 = results[1]
        assert r1.screen_name == "Sarah"
        assert r1.slug == "sarah42"
        assert r1.seeking is False
        assert r1.has_image is False

    def test_no_results(self):
        results, next_page = parse_search_results(
            "<html><body><p>No results found.</p></body></html>"
        )
        assert results == []
        assert next_page is None


class TestParseMemberProfile:
    def test_full_member_profile(self):
        profile = parse_member_profile(MEMBER_PROFILE_HTML)
        assert profile.screen_name == "Darrell"
        assert profile.slug == "darrell1917056"
        assert profile.member_since == "January 2020"
        assert profile.last_active == "3 days ago"
        assert profile.commitment_level == CommitmentLevel.VERY_COMMITTED
        assert profile.years_playing == YearsPlaying.Y25
        assert profile.gigs_played == GigsPlayed.OVER_100
        assert profile.practice_frequency == PracticeFrequency.TWO_THREE_PER_WEEK
        assert profile.gig_availability == GigFrequency.TWO_THREE_NIGHTS
        assert profile.most_available == Availability.NIGHTS
        assert profile.location == "Austin, TX"

        # Instruments with experience
        assert len(profile.instruments) == 3
        drums = profile.instruments[0]
        assert drums.instrument == Instrument.DRUMS
        assert drums.experience == ExperienceLevel.EXPERT
        bass = profile.instruments[1]
        assert bass.instrument == Instrument.BASS_GUITAR
        assert bass.experience == ExperienceLevel.ADVANCED

        # Genres
        assert Genre.COUNTRY in profile.genres
        assert Genre.ROCK in profile.genres
        assert Genre.SOUTHERN_ROCK in profile.genres

        # Seeking
        assert Instrument.LEAD_GUITAR in profile.seeking
        assert Instrument.KEYBOARD in profile.seeking

        assert profile.description == "Drummer with 25 years of experience."
        assert profile.influences == "Neil Peart, John Bonham"
        assert profile.equipment == "Pearl Reference kit, Zildjian cymbals"

        assert len(profile.images) == 2
        assert "/images/darrell1.jpg" in profile.images

        assert len(profile.audio_tracks) == 2
        assert "Dusty Roads" in profile.audio_tracks

        assert len(profile.videos) == 1
        assert "Live at SXSW" in profile.videos

    def test_explicit_slug(self):
        profile = parse_member_profile(
            "<html><body><h1>Test</h1></body></html>", slug="test-slug"
        )
        assert profile.slug == "test-slug"
        assert profile.screen_name == "Test"


class TestParseMatches:
    def test_matches(self):
        matches = parse_matches(MATCHES_HTML)
        assert len(matches) == 2

        m0 = matches[0]
        assert m0.screen_name == "Mike"
        assert m0.slug == "mike_drums"
        assert m0.location == "Houston, TX"
        assert m0.zip == "77001"
        assert Instrument.DRUMS in m0.instruments
        assert Instrument.OTHER_PERCUSSION in m0.instruments
        assert Genre.ROCK in m0.genres
        assert Genre.BLUES in m0.genres
        assert m0.last_active == "Today"
        assert m0.category == SearchCategory.MUSICIANS
        assert m0.snippet == "Experienced drummer looking for gigs."

        m1 = matches[1]
        assert m1.screen_name == "Lisa"
        assert m1.slug == "lisa_keys"
        assert m1.snippet is None

    def test_empty_matches(self):
        matches = parse_matches("<html><body></body></html>")
        assert matches == []


class TestParseMessagesList:
    def test_threads(self):
        threads = parse_messages_list(MESSAGES_LIST_HTML)
        assert len(threads) == 2

        t0 = threads[0]
        assert t0.thread_id == "thread-101"
        assert t0.participant == "Darrell"
        assert t0.participant_slug == "darrell1917056"
        assert t0.last_message_preview == "Hey, want to jam sometime?"
        assert t0.last_message_time == datetime(2026, 3, 15, 14, 30, 0)

        t1 = threads[1]
        assert t1.thread_id == "thread-102"
        assert t1.participant == "Sarah"

    def test_empty(self):
        threads = parse_messages_list("<html><body></body></html>")
        assert threads == []


class TestParseMessageThread:
    def test_thread(self):
        thread = parse_message_thread(MESSAGE_THREAD_HTML)
        assert thread.thread_id == "thread-101"
        assert thread.participant == "Darrell"
        assert thread.participant_slug == "darrell1917056"
        assert len(thread.messages) == 2

        msg0 = thread.messages[0]
        assert msg0.sender == "JimStone"
        assert "saw your profile" in msg0.body
        assert msg0.timestamp == datetime(2026, 3, 15, 10, 0, 0)

        msg1 = thread.messages[1]
        assert msg1.sender == "Darrell"
        assert "free this weekend" in msg1.body

    def test_empty_thread(self):
        thread = parse_message_thread("<html><body></body></html>")
        assert thread.messages == []


class TestParseFeed:
    def test_feed(self):
        entries = parse_feed(FEED_HTML)
        assert len(entries) == 2

        e0 = entries[0]
        assert e0.feed_id == "feed-501"
        assert e0.user_screen_name == "Mike"
        assert e0.user_slug == "mike_drums"
        assert e0.location == "Houston, TX"
        assert e0.action_type == ActionType.UPLOADED_MUSIC
        assert e0.detail == "Uploaded 2 new tracks"
        assert e0.timestamp == datetime(2026, 3, 18, 12, 0, 0)

        e1 = entries[1]
        assert e1.action_type == ActionType.JOINED
        assert e1.user_slug == "lisa_keys"

    def test_empty_feed(self):
        entries = parse_feed("<html><body></body></html>")
        assert entries == []


class TestParsePhotos:
    def test_photos(self):
        photos = parse_photos(PHOTOS_HTML)
        assert len(photos) == 3

        p0 = photos[0]
        assert p0.photo_id == "img-201"
        assert p0.url == "/photos/main-shot.jpg"
        assert p0.is_main is True

        p1 = photos[1]
        assert p1.photo_id == "img-202"
        assert p1.url == "/photos/stage-shot.jpg"
        assert p1.is_main is False

    def test_empty(self):
        photos = parse_photos("<html><body></body></html>")
        assert photos == []


class TestParseMusic:
    def test_tracks(self):
        tracks = parse_music(MUSIC_HTML)
        assert len(tracks) == 2

        t0 = tracks[0]
        assert t0.track_id == "trk-301"
        assert t0.title == "Dusty Roads"
        assert t0.track_type == "mp3"
        assert t0.size == "4.2 MB"
        assert t0.has_mastered is True

        t1 = tracks[1]
        assert t1.track_id == "trk-302"
        assert t1.title == "Midnight Ride"
        assert t1.track_type == "wav"
        assert t1.has_mastered is False

    def test_empty(self):
        tracks = parse_music("<html><body></body></html>")
        assert tracks == []


class TestParseVideos:
    def test_videos(self):
        videos = parse_videos(VIDEOS_HTML)
        assert len(videos) == 2

        v0 = videos[0]
        assert v0.video_id == "vid-401"
        assert v0.title == "Live at SXSW 2025"
        assert v0.youtube_url == "https://youtube.com/watch?v=abc123"
        assert v0.visible is True

        v1 = videos[1]
        assert v1.video_id == "vid-402"
        assert v1.title == "Studio Session"
        assert v1.visible is False

    def test_empty(self):
        videos = parse_videos("<html><body></body></html>")
        assert videos == []


class TestParseCalendar:
    def test_events(self):
        events = parse_calendar(CALENDAR_HTML)
        assert len(events) == 2

        e0 = events[0]
        assert e0.event_id == "evt-601"
        assert e0.title == "Open Mic at Common Grounds"
        assert e0.date == date(2026, 5, 1)
        assert e0.time == "20:00"
        assert e0.description == "Bring your acoustic!"

        e1 = events[1]
        assert e1.event_id == "evt-602"
        assert e1.title == "Band Practice"
        assert e1.date == date(2026, 5, 3)
        assert e1.time == "18:30"
        assert e1.description is None

    def test_empty(self):
        events = parse_calendar("<html><body></body></html>")
        assert events == []


class TestParseSeeking:
    def test_seeking(self):
        status = parse_seeking(SEEKING_HTML)
        assert status.join_band is True
        assert len(status.instruments) == 3
        assert Instrument.LEAD_GUITAR in status.instruments
        assert Instrument.DRUMS in status.instruments
        assert Instrument.KEYBOARD in status.instruments
        # Bass Guitar is not checked
        assert Instrument.BASS_GUITAR not in status.instruments

    def test_not_seeking(self):
        status = parse_seeking(
            "<html><body><form>"
            "<input type='checkbox' name='join_band' value='1' />"
            "</form></body></html>"
        )
        assert status.join_band is False
        assert status.instruments == []


class TestParseSettingsEmail:
    def test_settings(self):
        settings = parse_settings_email(SETTINGS_EMAIL_HTML)
        assert settings.newsletters == EnabledDisabled.ENABLED
        assert settings.user_views == EnabledDisabled.DISABLED
        assert settings.user_visited == EnabledDisabled.ENABLED
        assert settings.user_music_lists == EnabledDisabled.ENABLED
        assert settings.general_notifications == EnabledDisabled.DISABLED
        assert settings.format == EmailFormat.HTML

    def test_empty_settings(self):
        settings = parse_settings_email("<html><body></body></html>")
        assert settings.newsletters is None
        assert settings.format is None
