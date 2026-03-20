"""Search command for bandmix-cli."""

from __future__ import annotations

import click

from bandmix_cli.client import BandMixClient
from bandmix_cli.enums import (
    ActiveWithin,
    CommitmentLevel,
    ExperienceLevel,
    Gender,
    SearchRadius,
    SearchSort,
)
from bandmix_cli.formatters import auto_format, format_output
from bandmix_cli.parser import parse_search_results

# Mapping from CLI category names to BandMix URL path segments
_CATEGORY_PATH = {
    "musicians": "musicians",
    "bands": "bands",
    "industry": "industry",
}

# Mapping from ActiveWithin values to the site's numeric weeks parameter
_ACTIVE_WITHIN_WEEKS = {
    "1w": "1",
    "2w": "2",
    "3w": "3",
    "4w": "4",
    "5w": "5",
    "6w": "6",
}

# Mapping from commitment level to the site's numeric value
_COMMITMENT_VALUES = {
    "Just for Fun": "1",
    "Moderately Committed": "2",
    "Committed": "3",
    "Very Committed": "4",
    "Touring": "5",
}

# Mapping from experience level to the site's numeric value
_EXPERIENCE_VALUES = {
    "Beginner": "1",
    "Intermediate": "2",
    "Moderate": "3",
    "Advanced": "4",
    "Expert": "5",
}

# Mapping from gender to the site's parameter value
_GENDER_VALUES = {
    "any": "",
    "male": "m",
    "female": "f",
}

# Mapping from sort to the site's parameter value
_SORT_VALUES = {
    "location": "distance",
    "activity": "activity",
    "date": "date",
}


def _build_search_params(  # noqa: PLR0912, PLR0913
    *,
    instruments: str | None,
    location: str | None,
    radius: str | None,
    sort: str | None,
    gender: str | None,
    age_from: int | None,
    age_to: int | None,
    genre: str | None,
    experience: str | None,
    commitment: str | None,
    commitment_mode: str | None,
    keywords: str | None,
    has_images: bool,
    has_audio: bool,
    has_video: bool,
    studio: bool,
    seeking: bool,
    active_within: str | None,
    page: int,
    name: str | None,
    member_id: str | None,
) -> dict[str, str]:
    """Build query parameters dict from CLI options."""
    params: dict[str, str] = {}

    if location:
        params["location"] = location

    if radius:
        params["radius"] = radius

    if sort:
        params["sort"] = _SORT_VALUES.get(sort, sort)

    if gender and gender != "any":
        params["gender"] = _GENDER_VALUES.get(gender, gender)

    if age_from is not None:
        params["age_from"] = str(age_from)

    if age_to is not None:
        params["age_to"] = str(age_to)

    if instruments:
        params["instruments"] = instruments

    if genre:
        params["genre"] = genre

    if experience:
        params["experience"] = _EXPERIENCE_VALUES.get(experience, experience)

    if commitment:
        params["commitment"] = _COMMITMENT_VALUES.get(commitment, commitment)

    if commitment_mode:
        params["commitment_mode"] = commitment_mode

    if keywords:
        params["keywords"] = keywords

    if has_images:
        params["has_images"] = "1"

    if has_audio:
        params["has_audio"] = "1"

    if has_video:
        params["has_video"] = "1"

    if studio:
        params["studio"] = "1"

    if seeking:
        params["seeking"] = "1"

    if active_within:
        params["active_within"] = _ACTIVE_WITHIN_WEEKS.get(active_within, active_within)

    if page > 1:
        params["page"] = str(page)

    if name:
        params["name"] = name

    if member_id:
        params["id"] = member_id

    return params


@click.command("search")
@click.option(
    "--category",
    type=click.Choice(["musicians", "bands", "industry"], case_sensitive=False),
    default="musicians",
    help="Profile category. Default: musicians.",
)
@click.option(
    "--instruments",
    default=None,
    help="Comma-separated list of instruments to filter by.",
)
@click.option(
    "--location",
    default=None,
    help="ZIP code or city name for search center.",
)
@click.option(
    "--radius",
    type=click.Choice([r.value for r in SearchRadius], case_sensitive=False),
    default=None,
    help="Miles from location. Default: 50.",
)
@click.option(
    "--sort",
    type=click.Choice([s.value for s in SearchSort], case_sensitive=False),
    default=None,
    help="Sort order.",
)
@click.option(
    "--gender",
    type=click.Choice([g.value for g in Gender], case_sensitive=False),
    default=None,
    help="Gender filter.",
)
@click.option("--age-from", type=int, default=None, help="Minimum age.")
@click.option("--age-to", type=int, default=None, help="Maximum age.")
@click.option(
    "--genre",
    default=None,
    help="Comma-separated list of genres to filter by.",
)
@click.option(
    "--experience",
    type=click.Choice([e.value for e in ExperienceLevel], case_sensitive=False),
    default=None,
    help="Instrument experience level.",
)
@click.option(
    "--commitment",
    type=click.Choice([c.value for c in CommitmentLevel], case_sensitive=False),
    default=None,
    help="Commitment level.",
)
@click.option(
    "--commitment-mode",
    type=click.Choice(["exact", "at-least"], case_sensitive=False),
    default=None,
    help="Commitment filter mode.",
)
@click.option("--keywords", default=None, help="Free-text keyword search.")
@click.option(
    "--has-images", is_flag=True, default=False, help="Only profiles with photos."
)
@click.option(
    "--has-audio", is_flag=True, default=False, help="Only profiles with music."
)
@click.option(
    "--has-video", is_flag=True, default=False, help="Only profiles with video."
)
@click.option("--studio", is_flag=True, default=False, help="Only studio musicians.")
@click.option(
    "--seeking",
    is_flag=True,
    default=False,
    help="Only those seeking musicians/bands.",
)
@click.option(
    "--active-within",
    type=click.Choice([a.value for a in ActiveWithin], case_sensitive=False),
    default=None,
    help="Recency filter (e.g. 1w, 2w, ... 6w).",
)
@click.option("--page", type=int, default=1, help="Page number. Default: 1.")
@click.option(
    "--limit",
    type=int,
    default=None,
    help="Max results to return (fetches multiple pages if needed).",
)
@click.option("--name", default=None, help="Search by name.")
@click.option("--id", "member_id", default=None, help="Search by member ID.")
@click.option(
    "--format",
    "fmt",
    type=click.Choice(["table", "json", "text", "raw"], case_sensitive=False),
    default=None,
    help="Output format.",
)
@click.pass_context
def search(  # noqa: PLR0913
    ctx: click.Context,
    category: str,
    instruments: str | None,
    location: str | None,
    radius: str | None,
    sort: str | None,
    gender: str | None,
    age_from: int | None,
    age_to: int | None,
    genre: str | None,
    experience: str | None,
    commitment: str | None,
    commitment_mode: str | None,
    keywords: str | None,
    has_images: bool,
    has_audio: bool,
    has_video: bool,
    studio: bool,
    seeking: bool,
    active_within: str | None,
    page: int,
    limit: int | None,
    name: str | None,
    member_id: str | None,
    fmt: str | None,
) -> None:
    """Search for musicians and bands on BandMix.com."""
    output_format = fmt or auto_format()

    client: BandMixClient = ctx.obj if ctx.obj else BandMixClient()

    cat_path = _CATEGORY_PATH.get(category, "musicians")
    search_path = f"/search/{cat_path}/"

    params = _build_search_params(
        instruments=instruments,
        location=location,
        radius=radius,
        sort=sort,
        gender=gender,
        age_from=age_from,
        age_to=age_to,
        genre=genre,
        experience=experience,
        commitment=commitment,
        commitment_mode=commitment_mode,
        keywords=keywords,
        has_images=has_images,
        has_audio=has_audio,
        has_video=has_video,
        studio=studio,
        seeking=seeking,
        active_within=active_within,
        page=page,
        name=name,
        member_id=member_id,
    )

    all_results = []
    current_page = page

    while True:
        if current_page > page:
            params["page"] = str(current_page)

        resp = client.get(search_path, params=params)

        if output_format == "raw":
            click.echo(format_output(resp.text, "raw"))
            return

        page_results, _total_pages = parse_search_results(resp.text)
        all_results.extend(page_results)

        # If limit is set and we have enough, truncate and stop
        if limit is not None and len(all_results) >= limit:
            all_results = all_results[:limit]
            break

        # If no results on this page or no limit set, stop after first page
        if not page_results or limit is None:
            break

        current_page += 1

    if not all_results:
        click.echo("No results found.")
        return

    click.echo(format_output(all_results, output_format))
