"""HTML parsers for BandMix.com pages."""

from __future__ import annotations

import re

from bs4 import BeautifulSoup, Tag

from bandmix_cli.enums import Genre, Instrument, SearchCategory
from bandmix_cli.models import SearchResult


def _safe_enum(enum_cls: type, value: str | None):
    """Try to match a string to an enum value, return None on failure."""
    if not value:
        return None
    for member in enum_cls:
        if member.value.lower() == value.strip().lower():
            return member
    return None


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
