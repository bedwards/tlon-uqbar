"""Profile commands (get/set/type)."""

from __future__ import annotations

import click

from bandmix_cli.client import BandMixClient
from bandmix_cli.enums import CommitmentLevel, Genre, Instrument
from bandmix_cli.formatters import format_output
from bandmix_cli.parser import parse_csrf_token, parse_profile

PROFILE_PATH = "/account/profile/"
TYPE_PATH = "/account/type/"

# All known profile fields (from SPEC 4.1)
PROFILE_FIELDS = [
    "screen_name",
    "contact_name",
    "gender",
    "birthdate",
    "state",
    "city",
    "zip",
    "address",
    "phone",
    "studio_musician",
    "years_playing",
    "commitment_level",
    "instruments",
    "genres",
    "seeking_band",
    "seeking_instruments",
    "description",
    "influences",
    "equipment",
    "gigs_played",
    "practice_frequency",
    "gig_availability",
    "most_available",
]

# Fields that require enum validation
ENUM_FIELDS: dict[str, type] = {
    "instruments": Instrument,
    "genres": Genre,
    "seeking_instruments": Instrument,
    "commitment_level": CommitmentLevel,
}


def _validate_enum_values(field: str, raw_value: str) -> list[str]:
    """Validate comma-separated values against the appropriate enum.

    Returns the list of validated enum values as strings.
    Raises click.BadParameter if any value is invalid.
    """
    enum_cls = ENUM_FIELDS[field]
    values = [v.strip() for v in raw_value.split(",") if v.strip()]
    valid_names = [m.value for m in enum_cls]

    validated: list[str] = []
    for v in values:
        # Case-insensitive match
        matched = None
        for name in valid_names:
            if name.lower() == v.lower():
                matched = name
                break
        if matched is None:
            raise click.BadParameter(
                f"Invalid {field} value: {v!r}. Valid values: {', '.join(valid_names)}"
            )
        validated.append(matched)
    return validated


@click.group()
def profile():
    """Read and write your BandMix profile."""


@profile.command("get")
@click.option("--field", default=None, help="Specific field to retrieve.")
@click.option(
    "--format",
    "fmt",
    type=click.Choice(["table", "json", "text"]),
    default="table",
    help="Output format.",
)
@click.option("--raw", is_flag=True, help="Print raw HTML response.")
def profile_get(field: str | None, fmt: str, raw: bool) -> None:
    """Read your full profile or a specific field."""
    client = BandMixClient()
    resp = client.get(PROFILE_PATH)

    if raw:
        click.echo(resp.text)
        return

    prof = parse_profile(resp.text)

    if field:
        if field not in PROFILE_FIELDS:
            raise click.BadParameter(
                f"Unknown field: {field!r}. Valid fields: {', '.join(PROFILE_FIELDS)}"
            )
        value = getattr(prof, field)
        # For list fields, format as comma-separated
        if isinstance(value, list):
            click.echo(", ".join(str(v) for v in value))
        else:
            click.echo(value if value is not None else "")
    else:
        click.echo(format_output(prof, fmt))


@profile.command("set")
@click.option("--field", required=True, help="Profile field to update.")
@click.option("--value", required=True, help="New value for the field.")
def profile_set(field: str, value: str) -> None:
    """Update a profile field."""
    if field not in PROFILE_FIELDS:
        raise click.BadParameter(
            f"Unknown field: {field!r}. Valid fields: {', '.join(PROFILE_FIELDS)}"
        )

    # Validate enum fields
    if field in ENUM_FIELDS:
        _validate_enum_values(field, value)

    client = BandMixClient()

    # Fetch current page for CSRF token
    page_resp = client.get(PROFILE_PATH)
    csrf = parse_csrf_token(page_resp.text)

    form_data: dict[str, str] = {}
    if csrf:
        form_data["csrfmiddlewaretoken"] = csrf
    form_data[field] = value

    resp = client.post(PROFILE_PATH, data=form_data)

    if resp.status_code < 400:
        click.echo(f"Updated {field}.")
    else:
        click.echo(f"Failed to update {field}.", err=True)
        raise SystemExit(1)


# --- profile type subgroup ---


@profile.group("type")
def profile_type():
    """Get or set your account type (Musician/Band)."""


@profile_type.command("get")
@click.option("--raw", is_flag=True, help="Print raw HTML response.")
def type_get(raw: bool) -> None:
    """Get your account type."""
    client = BandMixClient()
    resp = client.get(TYPE_PATH)

    if raw:
        click.echo(resp.text)
        return

    prof = parse_profile(resp.text)
    account_type = prof.profile_type
    click.echo(account_type.value if account_type else "Unknown")


@profile_type.command("set")
@click.option("--value", required=True, help="Account type: Musician or Band.")
def type_set(value: str) -> None:
    """Set your account type."""
    valid = ["Musician", "Band"]
    matched = None
    for v in valid:
        if v.lower() == value.lower():
            matched = v
            break
    if matched is None:
        raise click.BadParameter(
            f"Invalid account type: {value!r}. Must be 'Musician' or 'Band'."
        )

    client = BandMixClient()
    page_resp = client.get(TYPE_PATH)
    csrf = parse_csrf_token(page_resp.text)

    form_data: dict[str, str] = {}
    if csrf:
        form_data["csrfmiddlewaretoken"] = csrf
    form_data["profile_type"] = matched

    resp = client.post(TYPE_PATH, data=form_data)

    if resp.status_code < 400:
        click.echo(f"Account type set to {matched}.")
    else:
        click.echo("Failed to set account type.", err=True)
        raise SystemExit(1)
