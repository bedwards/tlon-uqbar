"""BeautifulSoup4 + lxml HTML parsers for all BandMix page types."""

from __future__ import annotations

import re
from datetime import date, datetime

from bs4 import BeautifulSoup, Tag

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
from bandmix_cli.models import (
    AudioTrack,
    CalendarEvent,
    DashboardSettings,
    EmailSettings,
    FeedEntry,
    InstrumentWithExperience,
    Match,
    MatchMailerSettings,
    MemberProfile,
    Message,
    MessageThread,
    Photo,
    Profile,
    SearchResult,
    SeekingStatus,
    Video,
)


def _soup(html: str) -> BeautifulSoup:
    """Create a BeautifulSoup parser from an HTML string."""
    return BeautifulSoup(html, "lxml")


def _text(tag: Tag | None) -> str | None:
    """Extract stripped text from a tag, or None."""
    if tag is None:
        return None
    text = tag.get_text(strip=True)
    return text if text else None


def _attr(tag: Tag | None, attr: str) -> str:
    """Safely get a tag attribute as a string."""
    if tag is None:
        return ""
    val = tag.get(attr, "")
    if isinstance(val, list):
        val = val[0] if val else ""
    return str(val)


def _safe_enum(enum_cls: type, value: str | None):
    """Try to match a string to an enum value, return None on failure."""
    if not value:
        return None
    stripped = value.strip()
    if not stripped:
        return None
    for member in enum_cls:
        if member.value.lower() == stripped.lower():
            return member
    return None


def _parse_datetime_attr(tag: Tag | None) -> datetime | None:
    """Extract a datetime from a tag's datetime attribute."""
    if tag is None:
        return None
    dt_attr = _attr(tag, "datetime")
    if not dt_attr:
        return None
    try:
        return datetime.fromisoformat(dt_attr)
    except ValueError:
        return None


# ---------------------------------------------------------------------------
# Login
# ---------------------------------------------------------------------------


def parse_login_response(html: str) -> dict:
    """Parse login response to detect success/failure and extract session info.

    Returns a dict with keys:
      - success (bool)
      - error (str | None): error message if login failed
      - screen_name (str | None): user's screen name on success
    """
    soup = _soup(html)

    # Check for error messages (login form with error)
    error_el = soup.select_one(".error-message, .alert-danger, .form-error")
    if error_el:
        return {
            "success": False,
            "error": _text(error_el),
            "screen_name": None,
        }

    # If we landed on a dashboard/account page, login succeeded
    screen_name_el = soup.select_one(".account-name, .user-name, #account-screen-name")
    if screen_name_el:
        return {
            "success": True,
            "error": None,
            "screen_name": _text(screen_name_el),
        }

    # If the login form is still present, login failed
    login_form = soup.select_one("form#login-form, form[action*='login']")
    if login_form:
        return {
            "success": False,
            "error": "Login failed",
            "screen_name": None,
        }

    # Default: assume success if no login form found (redirect scenario)
    return {"success": True, "error": None, "screen_name": None}


# ---------------------------------------------------------------------------
# CSRF Token
# ---------------------------------------------------------------------------


def parse_csrf_token(html: str) -> str:
    """Extract a CSRF token from a hidden form input or meta tag."""
    soup = _soup(html)
    token_input = soup.select_one(
        "input[name='csrfmiddlewaretoken'], "
        "input[name='csrf_token'], "
        "input[name='_token']"
    )
    if token_input:
        return _attr(token_input, "value")
    meta = soup.select_one("meta[name='csrf-token']")
    if meta:
        return _attr(meta, "content")
    return ""


# ---------------------------------------------------------------------------
# Profile
# ---------------------------------------------------------------------------


def parse_profile(html: str) -> Profile:
    """Parse the authenticated user's profile page (/account/profile/)."""
    soup = _soup(html)

    def _input_val(name: str) -> str | None:
        el = soup.select_one(f"input[name='{name}']")
        if el is None:
            return None
        val = _attr(el, "value")
        return val if val else None

    def _textarea_val(name: str) -> str | None:
        el = soup.select_one(f"textarea[name='{name}']")
        return _text(el)

    def _select_val(name: str) -> str | None:
        el = soup.select_one(f"select[name='{name}'] option[selected]")
        return _text(el)

    def _checked_values(name: str) -> list[str]:
        values = []
        for el in soup.select(f"input[name='{name}']"):
            if el.has_attr("checked"):
                val = _attr(el, "value")
                if val:
                    values.append(val)
        return values

    # Parse birthdate
    birthdate = None
    bd_str = _input_val("birthdate")
    if bd_str:
        for fmt in ("%Y-%m-%d", "%m/%d/%Y"):
            try:
                birthdate = datetime.strptime(bd_str, fmt).date()
                break
            except ValueError:
                continue

    # Parse instruments
    instruments = [
        inst
        for raw in _checked_values("instruments")
        if (inst := _safe_enum(Instrument, raw)) is not None
    ]

    # Parse genres
    genres = [
        g
        for raw in _checked_values("genres")
        if (g := _safe_enum(Genre, raw)) is not None
    ]

    # Parse seeking instruments
    seeking_instruments = [
        inst
        for raw in _checked_values("seeking_instruments")
        if (inst := _safe_enum(Instrument, raw)) is not None
    ]

    # Checkboxes
    studio_el = soup.select_one("input[name='studio_musician']")
    studio_musician = studio_el is not None and studio_el.has_attr("checked")

    seeking_band_el = soup.select_one("input[name='seeking_band']")
    seeking_band = seeking_band_el is not None and seeking_band_el.has_attr("checked")

    return Profile(
        screen_name=_input_val("screen_name") or "",
        contact_name=_input_val("contact_name"),
        gender=_select_val("gender"),
        birthdate=birthdate,
        state=_select_val("state"),
        city=_input_val("city"),
        zip=_input_val("zip"),
        address=_input_val("address"),
        phone=_input_val("phone"),
        studio_musician=studio_musician,
        years_playing=_safe_enum(YearsPlaying, _select_val("years_playing")),
        commitment_level=_safe_enum(CommitmentLevel, _select_val("commitment_level")),
        instruments=instruments,
        genres=genres,
        seeking_band=seeking_band,
        seeking_instruments=seeking_instruments,
        description=_textarea_val("description"),
        influences=_textarea_val("influences"),
        equipment=_textarea_val("equipment"),
        gigs_played=_safe_enum(GigsPlayed, _select_val("gigs_played")),
        practice_frequency=_safe_enum(
            PracticeFrequency, _select_val("practice_frequency")
        ),
        gig_availability=_safe_enum(GigFrequency, _select_val("gig_availability")),
        most_available=_safe_enum(Availability, _select_val("most_available")),
    )


# ---------------------------------------------------------------------------
# Search Results
# ---------------------------------------------------------------------------


def parse_search_results(html: str) -> tuple[list[SearchResult], int | None]:
    """Parse search results page.

    Returns (results, next_page) where next_page is the next page number
    or None if there is no next page.
    """
    soup = _soup(html)
    results: list[SearchResult] = []

    for card in soup.select(".search-result, .result-card"):
        name_el = card.select_one(".screen-name, .result-name, h3 a")
        slug = ""
        if name_el:
            href = _attr(name_el, "href")
            if href:
                slug = href.strip("/").split("/")[-1]

        location_el = card.select_one(".location, .result-location")
        zip_el = card.select_one(".zip, .result-zip")
        category_el = card.select_one(".category, .result-category")
        snippet_el = card.select_one(
            ".snippet, .result-description, .description-preview"
        )
        last_active_el = card.select_one(".last-active, .activity-date")

        # Instruments
        instr_el = card.select_one(".instruments, .result-instruments")
        instr_list: list[Instrument] = []
        if instr_el:
            for name in (_text(instr_el) or "").split(","):
                inst = _safe_enum(Instrument, name.strip())
                if inst:
                    instr_list.append(inst)

        # Genres
        genre_el = card.select_one(".genres, .result-genres")
        genre_list: list[Genre] = []
        if genre_el:
            for name in (_text(genre_el) or "").split(","):
                g = _safe_enum(Genre, name.strip())
                if g:
                    genre_list.append(g)

        has_image = card.select_one(".has-image, img.profile-image") is not None
        has_audio = card.select_one(".has-audio, .audio-icon") is not None
        has_video = card.select_one(".has-video, .video-icon") is not None
        seeking = card.select_one(".seeking, .is-seeking") is not None

        results.append(
            SearchResult(
                screen_name=_text(name_el) or "",
                slug=slug,
                location=_text(location_el),
                zip=_text(zip_el),
                category=_safe_enum(SearchCategory, _text(category_el)),
                instruments=instr_list,
                genres=genre_list,
                seeking=seeking,
                last_active=_text(last_active_el),
                has_image=has_image,
                has_audio=has_audio,
                has_video=has_video,
                snippet=_text(snippet_el),
            )
        )

    # Pagination
    next_page = None
    next_link = soup.select_one("a.next-page, a[rel='next'], .pagination .next a")
    if next_link:
        href = _attr(next_link, "href")
        m = re.search(r"page=(\d+)", href)
        if m:
            next_page = int(m.group(1))

    return results, next_page


# ---------------------------------------------------------------------------
# Member Profile
# ---------------------------------------------------------------------------


def parse_member_profile(html: str, slug: str = "") -> MemberProfile:
    """Parse a member's public profile page into a MemberProfile model.

    The profile page at ``/<slug>/`` contains the member's public info
    in a structured HTML layout.
    """
    soup = _soup(html)

    # Screen name
    screen_name = ""
    name_tag = soup.find("h1", class_="profile-name") or soup.find("h1")
    if name_tag:
        screen_name = name_tag.get_text(strip=True)

    # Derive slug from canonical URL if not provided
    if not slug:
        canonical = soup.select_one("link[rel='canonical']")
        if canonical:
            href = _attr(canonical, "href")
            slug = href.strip("/").split("/")[-1]

    # Info sidebar items (key-value pairs)
    info: dict[str, str] = {}
    for item in soup.select(".info-list li, .profile-info li, .details-list li"):
        label_tag = item.find(["strong", "span", "label"])
        if label_tag:
            label = label_tag.get_text(strip=True).rstrip(":").strip()
            value = item.get_text(strip=True)
            value = value.replace(label_tag.get_text(strip=True), "", 1).strip()
            value = value.lstrip(":").strip()
            if label and value:
                info[label.lower()] = value

    member_since = info.get("member since")
    last_active = info.get("last active") or info.get("last login")
    commitment_level = _safe_enum(
        CommitmentLevel,
        info.get("commitment level") or info.get("commitment"),
    )
    years_playing = _safe_enum(YearsPlaying, info.get("years playing"))
    gigs_played = _safe_enum(GigsPlayed, info.get("gigs played"))
    practice_frequency = _safe_enum(
        PracticeFrequency,
        info.get("practice frequency") or info.get("practice"),
    )
    gig_availability = _safe_enum(
        GigFrequency,
        info.get("gig availability") or info.get("available to gig"),
    )
    most_available = _safe_enum(
        Availability,
        info.get("most available") or info.get("availability"),
    )

    # Instruments with experience levels
    instruments: list[InstrumentWithExperience] = []
    for inst_el in soup.select(
        ".instruments li, .profile-instruments li, .instrument-list li"
    ):
        inst_text = inst_el.get_text(strip=True)
        match = re.match(r"^(.+?)\s*\(([^)]+)\)\s*$", inst_text)
        if match:
            inst_name = match.group(1).strip()
            exp_name = match.group(2).strip()
        else:
            inst_name = inst_text.strip()
            exp_name = None

        instrument = _safe_enum(Instrument, inst_name)
        experience = _safe_enum(ExperienceLevel, exp_name)
        if instrument:
            instruments.append(
                InstrumentWithExperience(instrument=instrument, experience=experience)
            )

    # Genres
    genres: list[Genre] = []
    for genre_el in soup.select(".genres li, .profile-genres li, .genre-list li"):
        genre = _safe_enum(Genre, genre_el.get_text(strip=True))
        if genre:
            genres.append(genre)

    # Seeking
    seeking: list[Instrument] = []
    for seek_el in soup.select(".seeking li, .profile-seeking li, .seeking-list li"):
        inst = _safe_enum(Instrument, seek_el.get_text(strip=True))
        if inst:
            seeking.append(inst)

    # Description, influences, equipment
    desc_tag = soup.select_one(
        ".profile-description, .description, .bio, [class*='description']"
    )
    description = _text(desc_tag)

    infl_tag = soup.select_one(
        ".profile-influences, .influences, [class*='influences']"
    )
    influences = _text(infl_tag)

    equip_tag = soup.select_one(".profile-equipment, .equipment, [class*='equipment']")
    equipment = _text(equip_tag)

    # Location — try info dict first, then CSS selectors
    location = info.get("location")
    if not location:
        loc_tag = soup.select_one(".profile-location, .location, [class*='location']")
        location = _text(loc_tag)

    # Images
    images: list[str] = []
    for img in soup.select(
        ".profile-images img, .gallery img, .photo-gallery img, .images img"
    ):
        src = _attr(img, "src")
        if src:
            images.append(src)

    # Audio tracks
    audio_tracks: list[str] = []
    for track in soup.select(
        ".audio-tracks li, .profile-audio li, .music-list li, .tracks li"
    ):
        title = track.get_text(strip=True)
        if title:
            audio_tracks.append(title)

    # Videos
    videos: list[str] = []
    for video in soup.select(".profile-videos li, .video-list li, .videos li"):
        title = video.get_text(strip=True)
        if title:
            videos.append(title)

    return MemberProfile(
        screen_name=screen_name,
        slug=slug,
        member_since=member_since,
        last_active=last_active,
        commitment_level=commitment_level,
        years_playing=years_playing,
        gigs_played=gigs_played,
        practice_frequency=practice_frequency,
        gig_availability=gig_availability,
        most_available=most_available,
        instruments=instruments,
        genres=genres,
        seeking=seeking,
        description=description,
        influences=influences,
        equipment=equipment,
        location=location,
        images=images,
        audio_tracks=audio_tracks,
        videos=videos,
    )


# ---------------------------------------------------------------------------
# Matches
# ---------------------------------------------------------------------------


def parse_matches(html: str) -> list[Match]:
    """Parse match results from /account/connections/."""
    soup = _soup(html)
    matches: list[Match] = []

    for card in soup.select(".match-card, .match-result, .connection-item"):
        name_el = card.select_one(".screen-name, .match-name, h3 a")
        slug = ""
        if name_el:
            href = _attr(name_el, "href")
            if href:
                slug = href.strip("/").split("/")[-1]

        location_el = card.select_one(".location")
        zip_el = card.select_one(".zip")
        category_el = card.select_one(".category")
        snippet_el = card.select_one(".snippet, .description-preview")
        last_active_el = card.select_one(".last-active")

        instr_el = card.select_one(".instruments")
        instr_list: list[Instrument] = []
        if instr_el:
            for name in (_text(instr_el) or "").split(","):
                inst = _safe_enum(Instrument, name.strip())
                if inst:
                    instr_list.append(inst)

        genre_el = card.select_one(".genres")
        genre_list: list[Genre] = []
        if genre_el:
            for name in (_text(genre_el) or "").split(","):
                g = _safe_enum(Genre, name.strip())
                if g:
                    genre_list.append(g)

        matches.append(
            Match(
                screen_name=_text(name_el) or "",
                slug=slug,
                location=_text(location_el),
                zip=_text(zip_el),
                instruments=instr_list,
                genres=genre_list,
                last_active=_text(last_active_el),
                category=_safe_enum(SearchCategory, _text(category_el)),
                snippet=_text(snippet_el),
            )
        )

    return matches


# ---------------------------------------------------------------------------
# Messages
# ---------------------------------------------------------------------------


def parse_messages_list(html: str) -> list[MessageThread]:
    """Parse the messages list page (/account/messages/)."""
    soup = _soup(html)
    threads: list[MessageThread] = []

    for row in soup.select(".message-thread, .message-row, tr.message-item"):
        thread_id = _attr(row, "data-thread-id") or _attr(row, "id")

        participant_el = row.select_one(
            ".participant, .sender-name, .thread-participant a"
        )
        participant_slug = ""
        if participant_el:
            href = _attr(participant_el, "href")
            if href:
                participant_slug = href.strip("/").split("/")[-1]

        preview_el = row.select_one(".message-preview, .last-message, .thread-preview")
        time_el = row.select_one(".message-time, .thread-time, time")

        threads.append(
            MessageThread(
                thread_id=thread_id,
                participant=_text(participant_el) or "",
                participant_slug=participant_slug or None,
                last_message_preview=_text(preview_el),
                last_message_time=_parse_datetime_attr(time_el),
            )
        )

    return threads


def parse_message_thread(html: str) -> MessageThread:
    """Parse a single message thread/conversation page."""
    soup = _soup(html)

    # Thread metadata
    thread_el = soup.select_one("[data-thread-id], .thread-container, #message-thread")
    thread_id = ""
    if thread_el:
        thread_id = _attr(thread_el, "data-thread-id") or _attr(thread_el, "id")

    participant_el = soup.select_one(
        ".thread-participant, .conversation-with, h2.participant"
    )
    participant_slug = ""
    if participant_el:
        link = participant_el.select_one("a")
        if link:
            href = _attr(link, "href")
            if href:
                participant_slug = href.strip("/").split("/")[-1]

    messages: list[Message] = []
    for msg_el in soup.select(".message, .message-item, .chat-bubble"):
        sender_el = msg_el.select_one(".sender, .message-sender, .from")
        body_el = msg_el.select_one(".body, .message-body, .message-content")
        time_el = msg_el.select_one(".message-time, time")

        messages.append(
            Message(
                sender=_text(sender_el) or "",
                body=_text(body_el) or "",
                timestamp=_parse_datetime_attr(time_el),
            )
        )

    return MessageThread(
        thread_id=thread_id,
        participant=_text(participant_el) or "",
        participant_slug=participant_slug or None,
        messages=messages,
    )


# ---------------------------------------------------------------------------
# Feed
# ---------------------------------------------------------------------------


def parse_feed(html: str) -> list[FeedEntry]:
    """Parse activity feed from /account/feeds/."""
    soup = _soup(html)
    entries: list[FeedEntry] = []

    for item in soup.select(".feed-item, .feed-entry, .activity-item"):
        feed_id = _attr(item, "data-feed-id") or _attr(item, "id")

        user_el = item.select_one(".feed-user, .user-name a, .feed-author a")
        user_slug = ""
        if user_el:
            href = _attr(user_el, "href")
            if href:
                user_slug = href.strip("/").split("/")[-1]

        location_el = item.select_one(".location, .feed-location")
        action_el = item.select_one(".action-type, .feed-action, .activity-type")
        detail_el = item.select_one(".feed-detail, .activity-detail")
        time_el = item.select_one(".feed-time, time")

        entries.append(
            FeedEntry(
                feed_id=feed_id or None,
                user_screen_name=_text(user_el) or "",
                user_slug=user_slug or None,
                location=_text(location_el),
                action_type=_safe_enum(ActionType, _text(action_el)),
                timestamp=_parse_datetime_attr(time_el),
                detail=_text(detail_el),
            )
        )

    return entries


# ---------------------------------------------------------------------------
# Photos
# ---------------------------------------------------------------------------


def parse_photos(html: str) -> list[Photo]:
    """Parse photos from /account/images/."""
    soup = _soup(html)
    photos: list[Photo] = []

    for item in soup.select(".photo-item, .image-item, .gallery-item"):
        photo_id = _attr(item, "data-photo-id") or _attr(item, "data-id")

        img = item.select_one("img")
        url = _attr(img, "src") if img else ""

        is_main = bool(
            _attr(item, "data-main")
            or "main-photo" in (item.get("class") or [])
            or item.select_one(".main-badge, .is-main") is not None
        )

        photos.append(Photo(photo_id=photo_id, url=url, is_main=is_main))

    return photos


# ---------------------------------------------------------------------------
# Music / Audio
# ---------------------------------------------------------------------------


def parse_music(html: str) -> list[AudioTrack]:
    """Parse audio tracks from /account/audio/."""
    soup = _soup(html)
    tracks: list[AudioTrack] = []

    for item in soup.select(".audio-track, .track-item, .music-item"):
        track_id = _attr(item, "data-track-id") or _attr(item, "data-id")

        title_el = item.select_one(".track-title, .title")
        type_el = item.select_one(".track-type, .type")
        size_el = item.select_one(".track-size, .size")
        has_mastered = item.select_one(".mastered, .has-mastered") is not None

        tracks.append(
            AudioTrack(
                track_id=track_id,
                title=_text(title_el) or "",
                track_type=_text(type_el),
                size=_text(size_el),
                has_mastered=has_mastered,
            )
        )

    return tracks


# ---------------------------------------------------------------------------
# Videos
# ---------------------------------------------------------------------------


def parse_videos(html: str) -> list[Video]:
    """Parse video list from /account/video/."""
    soup = _soup(html)
    videos: list[Video] = []

    for item in soup.select(".video-item, .video-row"):
        video_id = _attr(item, "data-video-id") or _attr(item, "data-id")

        title_el = item.select_one(".video-title, .title")
        url_el = item.select_one(
            "a.video-link, a[href*='youtube'], a[href*='youtu.be']"
        )
        youtube_url = _attr(url_el, "href") if url_el else ""

        visible = item.select_one(".hidden, .not-visible") is None

        videos.append(
            Video(
                video_id=video_id,
                title=_text(title_el) or "",
                youtube_url=youtube_url,
                visible=visible,
            )
        )

    return videos


# ---------------------------------------------------------------------------
# Calendar
# ---------------------------------------------------------------------------


def parse_calendar(html: str) -> list[CalendarEvent]:
    """Parse calendar events from /account/calendar/."""
    soup = _soup(html)
    events: list[CalendarEvent] = []

    for item in soup.select(".calendar-event, .event-item, .event-row"):
        event_id = _attr(item, "data-event-id") or _attr(item, "data-id")

        title_el = item.select_one(".event-title, .title")
        date_el = item.select_one(".event-date, .date")
        time_el = item.select_one(".event-time, .time")
        desc_el = item.select_one(".event-description, .description")

        event_date = date.today()
        date_text = _text(date_el)
        if date_text:
            for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%B %d, %Y"):
                try:
                    event_date = datetime.strptime(date_text, fmt).date()
                    break
                except ValueError:
                    continue

        events.append(
            CalendarEvent(
                event_id=event_id or None,
                date=event_date,
                time=_text(time_el),
                title=_text(title_el) or "",
                description=_text(desc_el),
            )
        )

    return events


# ---------------------------------------------------------------------------
# Seeking
# ---------------------------------------------------------------------------


def parse_seeking(html: str) -> SeekingStatus:
    """Parse seeking/wanted-ads from /account/ads/."""
    soup = _soup(html)

    join_band_el = soup.select_one("input[name='join_band']")
    join_band = join_band_el is not None and join_band_el.has_attr("checked")

    instruments: list[Instrument] = []
    for el in soup.select("input[name='instruments']"):
        if el.has_attr("checked"):
            val = _attr(el, "value")
            inst = _safe_enum(Instrument, val)
            if inst:
                instruments.append(inst)

    return SeekingStatus(join_band=join_band, instruments=instruments)


# ---------------------------------------------------------------------------
# Settings - Email
# ---------------------------------------------------------------------------


def parse_settings_email(html: str) -> EmailSettings:
    """Parse email notification settings from /account/email/."""
    soup = _soup(html)

    def _radio_val(name: str) -> str | None:
        for radio in soup.select(f"input[name='{name}']"):
            if radio.has_attr("checked"):
                val = _attr(radio, "value")
                return val if val else None
        return None

    return EmailSettings(
        newsletters=_safe_enum(EnabledDisabled, _radio_val("newsletters")),
        user_views=_safe_enum(EnabledDisabled, _radio_val("user_views")),
        user_visited=_safe_enum(EnabledDisabled, _radio_val("user_visited")),
        user_music_lists=_safe_enum(EnabledDisabled, _radio_val("user_music_lists")),
        general_notifications=_safe_enum(
            EnabledDisabled, _radio_val("general_notifications")
        ),
        format=_safe_enum(EmailFormat, _radio_val("format")),
    )


# ---------------------------------------------------------------------------
# Settings - Match Mailer
# ---------------------------------------------------------------------------


def parse_settings_matchmailer(html: str) -> MatchMailerSettings:
    """Parse match mailer settings from /account/email/#matchmailer."""
    soup = _soup(html)

    def _input_val(name: str) -> str | None:
        el = soup.select_one(f"input[name='{name}']")
        if el is None:
            return None
        val = _attr(el, "value")
        return val if val else None

    def _checkbox_checked(name: str) -> bool:
        el = soup.select_one(f"input[name='{name}']")
        return el is not None and el.has_attr("checked")

    def _select_val(name: str) -> str | None:
        el = soup.select_one(f"select[name='{name}'] option[selected]")
        return _text(el)

    def _radio_val(name: str) -> str | None:
        for radio in soup.select(f"input[name='{name}']"):
            if radio.has_attr("checked"):
                val = _attr(radio, "value")
                return val if val else None
        return None

    radius_str = _input_val("radius") or _select_val("radius")
    age_from_str = _input_val("age_from") or _select_val("age_from")
    age_to_str = _input_val("age_to") or _select_val("age_to")

    return MatchMailerSettings(
        enabled=_checkbox_checked("enabled"),
        radius=int(radius_str) if radius_str and radius_str.isdigit() else None,
        age_from=int(age_from_str) if age_from_str and age_from_str.isdigit() else None,
        age_to=int(age_to_str) if age_to_str and age_to_str.isdigit() else None,
        filter_instrument=_checkbox_checked("filter_instrument"),
        filter_genre=_checkbox_checked("filter_genre"),
        recommendations=_safe_enum(EnabledDisabled, _radio_val("recommendations")),
        additional_local=_safe_enum(EnabledDisabled, _radio_val("additional_local")),
    )


# ---------------------------------------------------------------------------
# Settings - Dashboard
# ---------------------------------------------------------------------------


def parse_settings_dashboard(html: str) -> DashboardSettings:
    """Parse dashboard options from /account/dashboard-options/."""
    soup = _soup(html)

    def _input_val(name: str) -> str | None:
        el = soup.select_one(f"input[name='{name}']")
        if el is None:
            return None
        val = _attr(el, "value")
        return val if val else None

    def _checkbox_checked(name: str) -> bool:
        el = soup.select_one(f"input[name='{name}']")
        return el is not None and el.has_attr("checked")

    def _select_val(name: str) -> str | None:
        el = soup.select_one(f"select[name='{name}'] option[selected]")
        return _text(el)

    radius_str = _input_val("radius") or _select_val("radius")
    age_from_str = _input_val("age_from") or _select_val("age_from")
    age_to_str = _input_val("age_to") or _select_val("age_to")

    return DashboardSettings(
        show_matches=_checkbox_checked("show_matches"),
        radius=int(radius_str) if radius_str and radius_str.isdigit() else None,
        age_from=int(age_from_str) if age_from_str and age_from_str.isdigit() else None,
        age_to=int(age_to_str) if age_to_str and age_to_str.isdigit() else None,
    )


# ---------------------------------------------------------------------------
# Music List (Bookmarks)
# ---------------------------------------------------------------------------


def parse_musiclist(html: str) -> list[SearchResult]:
    """Parse bookmarked profiles from /account/bookmarks/."""
    soup = _soup(html)
    results: list[SearchResult] = []

    for card in soup.select(
        ".bookmark-item, .musiclist-item, .search-result, .result-card"
    ):
        name_el = card.select_one(".screen-name, .result-name, h3 a, a")
        slug = ""
        if name_el:
            href = _attr(name_el, "href")
            if href:
                slug = href.strip("/").split("/")[-1]

        location_el = card.select_one(".location, .result-location")
        snippet_el = card.select_one(".snippet, .description-preview")

        results.append(
            SearchResult(
                screen_name=_text(name_el) or "",
                slug=slug,
                location=_text(location_el),
                snippet=_text(snippet_el),
            )
        )

    return results


# ---------------------------------------------------------------------------
# Hidden Users
# ---------------------------------------------------------------------------


def parse_hidden(html: str) -> list[SearchResult]:
    """Parse hidden users from /account/hidden/."""
    soup = _soup(html)
    results: list[SearchResult] = []

    for card in soup.select(".hidden-item, .hidden-user, .search-result, .result-card"):
        name_el = card.select_one(".screen-name, .result-name, h3 a, a")
        slug = ""
        if name_el:
            href = _attr(name_el, "href")
            if href:
                slug = href.strip("/").split("/")[-1]

        location_el = card.select_one(".location, .result-location")

        results.append(
            SearchResult(
                screen_name=_text(name_el) or "",
                slug=slug,
                location=_text(location_el),
            )
        )

    return results
