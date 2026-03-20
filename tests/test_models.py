"""Tests for bandmix_cli models and enums."""

from datetime import date, datetime

import pytest
from pydantic import ValidationError

from bandmix_cli.enums import (
    ActionType,
    Availability,
    CommitmentLevel,
    EmailFormat,
    EnabledDisabled,
    ExperienceLevel,
    Genre,
    GigNightsPerWeek,
    GigsPlayed,
    Instrument,
    PracticeFrequency,
    ProfileType,
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


# --- Enum tests ---


class TestEnums:
    def test_instrument_count(self):
        assert len(Instrument) == 36

    def test_genre_count(self):
        assert len(Genre) == 32

    def test_commitment_values(self):
        assert CommitmentLevel.JUST_FOR_FUN == "Just for Fun"
        assert CommitmentLevel.TOURING == "Touring"

    def test_experience_values(self):
        assert ExperienceLevel.BEGINNER == "Beginner"
        assert ExperienceLevel.EXPERT == "Expert"

    def test_years_playing_includes_60_plus(self):
        assert YearsPlaying.Y60_PLUS == "60+"

    def test_gigs_played_values(self):
        assert GigsPlayed.UNSPECIFIED == "Unspecified"
        assert GigsPlayed.OVER_100 == "Over 100"

    def test_instrument_str_value(self):
        assert str(Instrument.ACOUSTIC_GUITAR) == "Acoustic Guitar"
        assert str(Instrument.VOCALIST_TENOR) == "Vocalist - Tenor"

    def test_genre_str_value(self):
        assert str(Genre.CHRISTIAN_GOSPEL) == "Christian / Gospel"
        assert str(Genre.HIP_HOP_RAP) == "Hip Hop/Rap"

    def test_profile_type(self):
        assert ProfileType.MUSICIAN == "Musician"
        assert ProfileType.BAND == "Band"

    def test_action_type(self):
        assert ActionType.JOINED == "joined"
        assert ActionType.UPLOADED_MUSIC == "uploaded_music"

    def test_search_category(self):
        assert SearchCategory.MUSICIANS == "Musicians"
        assert SearchCategory.BANDS == "Bands"


# --- Model tests ---


class TestProfile:
    def test_minimal_profile(self):
        p = Profile(screen_name="TestUser")
        assert p.screen_name == "TestUser"
        assert p.instruments == []
        assert p.genres == []
        assert p.seeking_band is False

    def test_full_profile(self):
        p = Profile(
            screen_name="JimStone",
            contact_name="Jim Stone",
            gender="male",
            birthdate=date(1985, 3, 15),
            state="TX",
            city="Austin",
            zip="78701",
            studio_musician=True,
            years_playing=YearsPlaying.Y25,
            commitment_level=CommitmentLevel.VERY_COMMITTED,
            instruments=[Instrument.VOCALIST, Instrument.ACOUSTIC_GUITAR],
            genres=[Genre.COUNTRY, Genre.FOLK, Genre.AMERICANA],
            seeking_band=True,
            seeking_instruments=[Instrument.DRUMS, Instrument.BASS_GUITAR],
            description="Singer-songwriter from Austin",
            influences="Willie Nelson, Townes Van Zandt",
            equipment="Taylor 814ce",
            gigs_played=GigsPlayed.OVER_100,
            practice_frequency=PracticeFrequency.TWO_THREE_PER_WEEK,
            gig_availability=GigNightsPerWeek.TWO_THREE_NIGHTS,
            most_available=Availability.NIGHTS,
            profile_type=ProfileType.MUSICIAN,
        )
        assert p.contact_name == "Jim Stone"
        assert len(p.instruments) == 2
        assert len(p.genres) == 3
        assert p.years_playing == YearsPlaying.Y25

    def test_genres_max_four(self):
        with pytest.raises(ValidationError):
            Profile(
                screen_name="Test",
                genres=[
                    Genre.COUNTRY,
                    Genre.FOLK,
                    Genre.ROCK,
                    Genre.BLUES,
                    Genre.JAZZ,
                ],
            )


class TestSearchResult:
    def test_minimal_search_result(self):
        sr = SearchResult(screen_name="Bob", slug="bob123")
        assert sr.screen_name == "Bob"
        assert sr.slug == "bob123"
        assert sr.seeking is False

    def test_full_search_result(self):
        sr = SearchResult(
            screen_name="Bob",
            slug="bob123",
            location="Austin, TX",
            zip="78701",
            category=SearchCategory.MUSICIANS,
            instruments=[Instrument.DRUMS],
            genres=[Genre.ROCK],
            seeking=True,
            last_active="2 days ago",
            has_image=True,
            has_audio=True,
            has_video=False,
            snippet="Experienced drummer looking for...",
        )
        assert sr.category == SearchCategory.MUSICIANS
        assert sr.has_image is True


class TestMemberProfile:
    def test_minimal_member(self):
        m = MemberProfile(screen_name="Alice", slug="alice456")
        assert m.screen_name == "Alice"
        assert m.instruments == []

    def test_member_with_instruments(self):
        m = MemberProfile(
            screen_name="Alice",
            slug="alice456",
            instruments=[
                InstrumentWithExperience(
                    instrument=Instrument.PIANO,
                    experience=ExperienceLevel.ADVANCED,
                ),
                InstrumentWithExperience(
                    instrument=Instrument.VOCALIST,
                    experience=ExperienceLevel.EXPERT,
                ),
            ],
        )
        assert len(m.instruments) == 2
        assert m.instruments[0].experience == ExperienceLevel.ADVANCED


class TestMatch:
    def test_match_creation(self):
        m = Match(
            screen_name="Charlie",
            slug="charlie789",
            location="Dallas, TX",
            instruments=[Instrument.LEAD_GUITAR],
            genres=[Genre.BLUES, Genre.ROCK],
            last_active="1 week ago",
            category=SearchCategory.MUSICIANS,
            snippet="Blues guitarist seeking...",
        )
        assert m.screen_name == "Charlie"
        assert len(m.genres) == 2


class TestMessageThread:
    def test_empty_thread(self):
        t = MessageThread(
            thread_id="100",
            participant="Dave",
        )
        assert t.messages == []

    def test_thread_with_messages(self):
        t = MessageThread(
            thread_id="100",
            participant="Dave",
            participant_slug="dave111",
            last_message_preview="Hey, want to jam?",
            last_message_time=datetime(2026, 3, 15, 14, 30),
            messages=[
                Message(
                    sender="Dave",
                    body="Hey, want to jam?",
                    timestamp=datetime(2026, 3, 15, 14, 30),
                ),
                Message(
                    sender="Me",
                    body="Sure, when works for you?",
                    timestamp=datetime(2026, 3, 15, 15, 0),
                ),
            ],
        )
        assert len(t.messages) == 2
        assert t.messages[0].sender == "Dave"


class TestMessage:
    def test_message(self):
        m = Message(sender="Alice", body="Hello!")
        assert m.sender == "Alice"
        assert m.timestamp is None


class TestFeedEntry:
    def test_feed_entry(self):
        entry = FeedEntry(
            feed_id="500",
            user_screen_name="Eve",
            user_slug="eve222",
            location="Nashville, TN",
            action_type=ActionType.UPLOADED_MUSIC,
            timestamp=datetime(2026, 3, 18, 10, 0),
            detail="Uploaded 3 new tracks",
        )
        assert entry.action_type == ActionType.UPLOADED_MUSIC


class TestPhoto:
    def test_photo(self):
        p = Photo(
            photo_id="p1",
            url="https://bandmix.com/images/p1.jpg",
            is_main=True,
        )
        assert p.is_main is True

    def test_photo_default_not_main(self):
        p = Photo(photo_id="p2", url="https://bandmix.com/images/p2.jpg")
        assert p.is_main is False


class TestAudioTrack:
    def test_audio_track(self):
        t = AudioTrack(
            track_id="t1",
            title="Dusty Roads",
            track_type="mp3",
            size="4.2 MB",
            has_mastered=True,
        )
        assert t.title == "Dusty Roads"
        assert t.has_mastered is True


class TestVideo:
    def test_video(self):
        v = Video(
            video_id="v1",
            title="Live at SXSW",
            youtube_url="https://youtube.com/watch?v=abc123",
            visible=True,
        )
        assert v.visible is True

    def test_video_required_fields(self):
        with pytest.raises(ValidationError):
            Video(video_id="v1", title="Test")  # type: ignore[call-arg]


class TestCalendarEvent:
    def test_calendar_event(self):
        e = CalendarEvent(
            event_id="e1",
            date=date(2026, 5, 1),
            time="20:00",
            title="Open Mic at Common Grounds",
            description="Bring your acoustic!",
        )
        assert e.title == "Open Mic at Common Grounds"

    def test_calendar_event_minimal(self):
        e = CalendarEvent(date=date(2026, 6, 1), title="Rehearsal")
        assert e.event_id is None
        assert e.time is None


class TestSeekingStatus:
    def test_seeking_status(self):
        s = SeekingStatus(
            join_band=True,
            instruments=[
                Instrument.LEAD_GUITAR,
                Instrument.BASS_GUITAR,
                Instrument.DRUMS,
            ],
        )
        assert s.join_band is True
        assert len(s.instruments) == 3

    def test_seeking_defaults(self):
        s = SeekingStatus()
        assert s.join_band is False
        assert s.instruments == []


class TestEmailSettings:
    def test_email_settings(self):
        s = EmailSettings(
            newsletters=EnabledDisabled.ENABLED,
            user_views=EnabledDisabled.DISABLED,
            format=EmailFormat.HTML,
        )
        assert s.newsletters == EnabledDisabled.ENABLED
        assert s.format == EmailFormat.HTML


class TestMatchMailerSettings:
    def test_match_mailer_settings(self):
        s = MatchMailerSettings(
            enabled=True,
            radius=50,
            age_from=25,
            age_to=55,
            filter_instrument=True,
            filter_genre=True,
            recommendations=EnabledDisabled.ENABLED,
            additional_local=EnabledDisabled.ENABLED,
        )
        assert s.enabled is True
        assert s.radius == 50


class TestDashboardSettings:
    def test_dashboard_settings(self):
        s = DashboardSettings(
            show_matches=True,
            radius=100,
            age_from=20,
            age_to=60,
        )
        assert s.radius == 100

    def test_dashboard_defaults(self):
        s = DashboardSettings()
        assert s.show_matches is True
        assert s.radius is None


class TestInstrumentWithExperience:
    def test_without_experience(self):
        ie = InstrumentWithExperience(instrument=Instrument.DRUMS)
        assert ie.experience is None

    def test_with_experience(self):
        ie = InstrumentWithExperience(
            instrument=Instrument.PIANO, experience=ExperienceLevel.EXPERT
        )
        assert ie.experience == ExperienceLevel.EXPERT

    def test_invalid_instrument(self):
        with pytest.raises(ValidationError):
            InstrumentWithExperience(instrument="Kazoo")  # type: ignore[arg-type]
