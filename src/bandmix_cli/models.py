"""Pydantic v2 models for all BandMix data entities."""

from datetime import date, datetime

from pydantic import BaseModel, Field

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
    ProfileType,
    SearchCategory,
    YearsPlaying,
)


class InstrumentWithExperience(BaseModel):
    """An instrument paired with an experience level."""

    instrument: Instrument
    experience: ExperienceLevel | None = None


class Profile(BaseModel):
    """The authenticated user's profile (from /account/profile/)."""

    screen_name: str
    contact_name: str | None = None
    gender: str | None = None
    birthdate: date | None = None
    state: str | None = None
    city: str | None = None
    zip: str | None = None
    address: str | None = None
    phone: str | None = None
    studio_musician: bool = False
    years_playing: YearsPlaying | None = None
    commitment_level: CommitmentLevel | None = None
    instruments: list[Instrument] = Field(default_factory=list)
    genres: list[Genre] = Field(default_factory=list, max_length=4)
    seeking_band: bool = False
    seeking_instruments: list[Instrument] = Field(default_factory=list)
    description: str | None = None
    influences: str | None = None
    equipment: str | None = None
    gigs_played: GigsPlayed | None = None
    practice_frequency: PracticeFrequency | None = None
    gig_availability: GigFrequency | None = None
    most_available: Availability | None = None
    profile_type: ProfileType | None = None


class SearchResult(BaseModel):
    """A single search result from /search/."""

    screen_name: str
    slug: str
    location: str | None = None
    zip: str | None = None
    category: SearchCategory | None = None
    instruments: list[Instrument] = Field(default_factory=list)
    genres: list[Genre] = Field(default_factory=list)
    seeking: bool = False
    last_active: str | None = None
    has_image: bool = False
    has_audio: bool = False
    has_video: bool = False
    snippet: str | None = None


class MemberProfile(BaseModel):
    """A public member profile (from /member/<slug>/)."""

    screen_name: str
    slug: str
    member_since: str | None = None
    last_active: str | None = None
    commitment_level: CommitmentLevel | None = None
    years_playing: YearsPlaying | None = None
    gigs_played: GigsPlayed | None = None
    practice_frequency: PracticeFrequency | None = None
    gig_availability: GigFrequency | None = None
    most_available: Availability | None = None
    instruments: list[InstrumentWithExperience] = Field(default_factory=list)
    genres: list[Genre] = Field(default_factory=list)
    seeking: list[Instrument] = Field(default_factory=list)
    description: str | None = None
    influences: str | None = None
    equipment: str | None = None
    location: str | None = None
    images: list[str] = Field(default_factory=list)
    audio_tracks: list[str] = Field(default_factory=list)
    videos: list[str] = Field(default_factory=list)


class Match(BaseModel):
    """A match from /account/connections/."""

    screen_name: str
    slug: str
    location: str | None = None
    zip: str | None = None
    instruments: list[Instrument] = Field(default_factory=list)
    genres: list[Genre] = Field(default_factory=list)
    last_active: str | None = None
    category: SearchCategory | None = None
    snippet: str | None = None


class Message(BaseModel):
    """A single message within a conversation thread."""

    sender: str
    body: str
    timestamp: datetime | None = None


class MessageThread(BaseModel):
    """A message thread (conversation) from /account/messages/."""

    thread_id: str
    participant: str
    participant_slug: str | None = None
    last_message_preview: str | None = None
    last_message_time: datetime | None = None
    messages: list[Message] = Field(default_factory=list)


class FeedEntry(BaseModel):
    """An activity feed entry from /account/feeds/."""

    feed_id: str | None = None
    user_screen_name: str
    user_slug: str | None = None
    location: str | None = None
    action_type: ActionType | None = None
    timestamp: datetime | None = None
    detail: str | None = None


class Photo(BaseModel):
    """A user photo from /account/images/."""

    photo_id: str
    url: str
    is_main: bool = False


class AudioTrack(BaseModel):
    """An audio track from /account/audio/."""

    track_id: str
    title: str
    track_type: str | None = None
    size: str | None = None
    has_mastered: bool = False


class Video(BaseModel):
    """A YouTube video link from /account/video/."""

    video_id: str
    title: str
    youtube_url: str
    visible: bool = True


class CalendarEvent(BaseModel):
    """A calendar event from /account/calendar/."""

    event_id: str | None = None
    date: date
    time: str | None = None
    title: str
    description: str | None = None


class SeekingStatus(BaseModel):
    """Seeking/wanted-ads status from /account/ads/."""

    join_band: bool = False
    instruments: list[Instrument] = Field(default_factory=list)


class EmailSettings(BaseModel):
    """Email notification settings from /account/email/."""

    newsletters: EnabledDisabled | None = None
    user_views: EnabledDisabled | None = None
    user_visited: EnabledDisabled | None = None
    user_music_lists: EnabledDisabled | None = None
    general_notifications: EnabledDisabled | None = None
    format: EmailFormat | None = None


class MatchMailerSettings(BaseModel):
    """Match mailer settings from /account/email/#matchmailer."""

    enabled: bool = False
    radius: int | None = None
    age_from: int | None = None
    age_to: int | None = None
    filter_instrument: bool = False
    filter_genre: bool = False
    recommendations: EnabledDisabled | None = None
    additional_local: EnabledDisabled | None = None


class DashboardSettings(BaseModel):
    """Dashboard options from /account/dashboard-options/."""

    show_matches: bool = True
    radius: int | None = None
    age_from: int | None = None
    age_to: int | None = None
