"""HTML parsers for BandMix.com pages."""

from __future__ import annotations

import re

from bs4 import BeautifulSoup, Tag

from bandmix_cli.enums import (
    Availability,
    CommitmentLevel,
    ExperienceLevel,
    Genre,
    GigFrequency,
    GigsPlayed,
    Instrument,
    PracticeFrequency,
    SearchCategory,
    YearsPlaying,
)
from bandmix_cli.models import InstrumentWithExperience, MemberProfile, SearchResult


def _text(tag: Tag | None) -> str | None:
    """Extract stripped text from a tag, or None."""
    if tag is None:
        return None
    text = tag.get_text(strip=True)
    return text if text else None


def _safe_enum(enum_cls: type, value: str | None):
    """Try to match a string to an enum value, return None on failure."""
    if not value:
        return None
    for member in enum_cls:
        if member.value.lower() == value.strip().lower():
            return member
    return None


def parse_member_profile(html: str, slug: str) -> MemberProfile:
    """Parse a member's public profile page into a MemberProfile model.

    The profile page at ``/<slug>/`` contains the member's public info
    in a structured HTML layout.
    """
    soup = BeautifulSoup(html, "lxml")

    # Screen name — typically in an h1 or h2 element
    screen_name = ""
    name_tag = soup.find("h1", class_="profile-name") or soup.find("h1")
    if name_tag:
        screen_name = name_tag.get_text(strip=True)

    # Info sidebar items (key-value pairs)
    info: dict[str, str] = {}
    for item in soup.select(".info-list li, .profile-info li, .details-list li"):
        label_tag = item.find(["strong", "span", "label"])
        if label_tag:
            label = label_tag.get_text(strip=True).rstrip(":").strip()
            # Value is the remaining text after removing label
            value = item.get_text(strip=True)
            value = value.replace(label_tag.get_text(strip=True), "", 1).strip()
            value = value.lstrip(":").strip()
            if label and value:
                info[label.lower()] = value

    # Member since / last active from meta or info
    member_since = info.get("member since")
    last_active = info.get("last active") or info.get("last login")

    # Commitment level
    commitment_level = _safe_enum(
        CommitmentLevel, info.get("commitment level") or info.get("commitment")
    )

    # Years playing
    years_playing = _safe_enum(YearsPlaying, info.get("years playing"))

    # Gigs played
    gigs_played = _safe_enum(GigsPlayed, info.get("gigs played"))

    # Practice frequency
    practice_frequency = _safe_enum(
        PracticeFrequency, info.get("practice frequency") or info.get("practice")
    )

    # Gig availability
    gig_availability = _safe_enum(
        GigFrequency, info.get("gig availability") or info.get("available to gig")
    )

    # Most available
    most_available = _safe_enum(
        Availability, info.get("most available") or info.get("availability")
    )

    # Instruments with experience levels
    instruments: list[InstrumentWithExperience] = []
    for inst_el in soup.select(
        ".instruments li, .profile-instruments li, .instrument-list li"
    ):
        inst_text = inst_el.get_text(strip=True)
        # Pattern: "Instrument Name (Experience Level)" or just "Instrument Name"
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

    # Description
    desc_tag = soup.select_one(
        ".profile-description, .description, .bio, [class*='description']"
    )
    description = _text(desc_tag)

    # Influences
    infl_tag = soup.select_one(
        ".profile-influences, .influences, [class*='influences']"
    )
    influences = _text(infl_tag)

    # Equipment
    equip_tag = soup.select_one(".profile-equipment, .equipment, [class*='equipment']")
    equipment = _text(equip_tag)

    # Location
    loc_tag = soup.select_one(".profile-location, .location, [class*='location']")
    location = _text(loc_tag)

    # Images
    images: list[str] = []
    for img in soup.select(
        ".profile-images img, .gallery img, .photo-gallery img, .images img"
    ):
        src = img.get("src")
        if src:
            images.append(str(src))

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


# ------------------------------------------------------------------
# Search results parser
# ------------------------------------------------------------------


def _safe_enum_list(enum_cls: type, values: list[str]) -> list:
    """Convert a list of strings to enum values, skipping unrecognized ones."""
    result = []
    for v in values:
        member = _safe_enum(enum_cls, v)
        if member is not None:
            result.append(member)
    return result


def _extract_slug(tag: Tag) -> str | None:
    """Extract a profile slug from an anchor tag href."""
    link = tag.find("a", href=re.compile(r"^/[a-zA-Z0-9][\w-]*/$"))
    if link:
        href = link.get("href", "")
        slug = href.strip("/")
        if slug and slug not in (
            "search",
            "login",
            "signup",
            "account",
            "about",
            "contact",
            "terms",
            "privacy",
        ):
            return slug
    return None


def _parse_single_search_result(card: Tag) -> SearchResult | None:
    """Parse a single search result card into a SearchResult model."""
    slug = _extract_slug(card)
    if not slug:
        return None

    link = card.find("a", href=re.compile(r"^/[a-zA-Z0-9][\w-]*/$"))
    screen_name = link.get_text(strip=True) if link else slug

    if not screen_name:
        return None

    # Location
    location_el = card.find(class_=re.compile(r"location|city|area"))
    location = location_el.get_text(strip=True) if location_el else None

    # ZIP code
    zip_el = card.find(class_=re.compile(r"zip"))
    zip_code = zip_el.get_text(strip=True) if zip_el else None

    # Category
    cat_el = card.find(class_=re.compile(r"category|type"))
    category = _safe_enum(
        SearchCategory, cat_el.get_text(strip=True) if cat_el else None
    )

    # Instruments
    instr_el = card.find(class_=re.compile(r"instruments?"))
    instruments_text = instr_el.get_text(strip=True) if instr_el else ""
    instr_list = _safe_enum_list(
        Instrument,
        [i.strip() for i in instruments_text.split(",") if i.strip()],
    )

    # Genres
    genre_el = card.find(class_=re.compile(r"genres?"))
    genres_text = genre_el.get_text(strip=True) if genre_el else ""
    genre_list = _safe_enum_list(
        Genre,
        [g.strip() for g in genres_text.split(",") if g.strip()],
    )

    # Seeking
    seeking_flag = bool(card.find(class_=re.compile(r"seeking")))

    # Last active
    active_el = card.find(class_=re.compile(r"active|last-active"))
    last_active = active_el.get_text(strip=True) if active_el else None

    # Media indicators
    has_image = bool(card.find(class_=re.compile(r"has-image|photo")))
    has_audio = bool(card.find(class_=re.compile(r"has-audio|music")))
    has_video = bool(card.find(class_=re.compile(r"has-video|video")))

    # Snippet
    snippet_el = card.find(class_=re.compile(r"snippet|description|bio|about"))
    snippet = snippet_el.get_text(strip=True) if snippet_el else None

    return SearchResult(
        screen_name=screen_name,
        slug=slug,
        location=location,
        zip=zip_code,
        category=category,
        instruments=instr_list,
        genres=genre_list,
        seeking=seeking_flag,
        last_active=last_active,
        has_image=has_image,
        has_audio=has_audio,
        has_video=has_video,
        snippet=snippet,
    )


def parse_search_results(html: str) -> list[SearchResult]:
    """Parse search results from the /search/ HTML page.

    Extracts profile cards from the search results page. Each card contains
    the musician/band name, slug (from the profile link), location, instruments,
    genres, and media indicators.
    """
    soup = BeautifulSoup(html, "lxml")
    results: list[SearchResult] = []

    # Search results are in divs with class 'search-result' or profile cards
    cards = soup.select(".search-result, .card, .profile-card, .result-item")

    # Fallback: look for links that point to member profiles
    if not cards:
        cards = soup.select("[data-profile], .member-card")

    # If still nothing, try to find profile links in the page
    if not cards:
        profile_links = soup.find_all("a", href=re.compile(r"^/[a-zA-Z0-9][\w-]*/$"))
        seen_parents: set[int] = set()
        for link in profile_links:
            parent = link.parent
            if parent and id(parent) not in seen_parents:
                seen_parents.add(id(parent))
                cards.append(parent)

    for card in cards:
        result = _parse_single_search_result(card)
        if result is not None:
            results.append(result)

    return results
