"""Tests for bandmix_cli.enums module."""

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
    USState,
    YearsPlaying,
)


class TestInstrument:
    def test_count(self):
        assert len(Instrument) == 36

    def test_is_strenum(self):
        assert isinstance(Instrument.DRUMS, str)
        assert Instrument.DRUMS == "Drums"

    def test_lookup_by_value(self):
        assert Instrument("Acoustic Guitar") is Instrument.ACOUSTIC_GUITAR

    def test_vocalist_variants(self):
        vocalists = [m for m in Instrument if m.value.startswith("Vocalist")]
        assert len(vocalists) == 6

    def test_steel_guitar_lowercase(self):
        """Steel guitar uses lowercase 'g' on the site."""
        assert Instrument.STEEL_GUITAR == "Steel guitar"

    def test_upright_bass_lowercase(self):
        """Upright bass uses lowercase 'b' on the site."""
        assert Instrument.UPRIGHT_BASS == "Upright bass"


class TestGenre:
    def test_count(self):
        # Spec says 33 but lists 32 values (no duplicate). Count actual listed values.
        assert len(Genre) == 32

    def test_is_strenum(self):
        assert isinstance(Genre.COUNTRY, str)
        assert Genre.COUNTRY == "Country"

    def test_lookup_by_value(self):
        assert Genre("Classic Rock") is Genre.CLASSIC_ROCK

    def test_special_characters(self):
        assert Genre.CHRISTIAN_GOSPEL == "Christian / Gospel"
        assert Genre.HIP_HOP_RAP == "Hip Hop/Rap"
        assert Genre.COVER_TRIBUTE == "Cover/Tribute"
        assert Genre.RNB == "R&B"


class TestCommitmentLevel:
    def test_count(self):
        assert len(CommitmentLevel) == 5

    def test_values(self):
        expected = [
            "Just for Fun",
            "Moderately Committed",
            "Committed",
            "Very Committed",
            "Touring",
        ]
        assert [m.value for m in CommitmentLevel] == expected

    def test_lookup(self):
        assert CommitmentLevel("Very Committed") is CommitmentLevel.VERY_COMMITTED


class TestExperienceLevel:
    def test_count(self):
        assert len(ExperienceLevel) == 5

    def test_values(self):
        expected = ["Beginner", "Intermediate", "Moderate", "Advanced", "Expert"]
        assert [m.value for m in ExperienceLevel] == expected


class TestYearsPlaying:
    def test_count(self):
        assert len(YearsPlaying) == 24

    def test_first_and_last(self):
        values = [m.value for m in YearsPlaying]
        assert values[0] == "1"
        assert values[-1] == "60+"

    def test_is_string(self):
        assert isinstance(YearsPlaying.Y10, str)
        assert YearsPlaying.Y10 == "10"


class TestGigsPlayed:
    def test_count(self):
        assert len(GigsPlayed) == 5

    def test_values(self):
        expected = ["Unspecified", "Under 10", "10 to 50", "50 to 100", "Over 100"]
        assert [m.value for m in GigsPlayed] == expected


class TestPracticeFrequency:
    def test_count(self):
        assert len(PracticeFrequency) == 4

    def test_values(self):
        expected = [
            "Unspecified",
            "1 time per week",
            "2-3 times per week",
            "More than 3 times per week",
        ]
        assert [m.value for m in PracticeFrequency] == expected


class TestGigFrequency:
    def test_count(self):
        assert len(GigFrequency) == 5

    def test_values(self):
        expected = [
            "Unspecified",
            "1 night a week",
            "2-3 nights a week",
            "4-5 nights a week",
            "6-7 nights a week",
        ]
        assert [m.value for m in GigFrequency] == expected


class TestAvailability:
    def test_count(self):
        assert len(Availability) == 4

    def test_values(self):
        expected = ["Unspecified", "Mornings", "Days", "Nights"]
        assert [m.value for m in Availability] == expected


class TestSearchCategory:
    def test_count(self):
        assert len(SearchCategory) == 13

    def test_top_level_categories(self):
        assert SearchCategory.MUSICIANS == "Musicians"
        assert SearchCategory.BANDS == "Bands"

    def test_industry_subcategories(self):
        industry = [
            m
            for m in SearchCategory
            if m not in (SearchCategory.MUSICIANS, SearchCategory.BANDS)
        ]
        assert len(industry) == 11


class TestUSState:
    def test_fifty_states_plus_dc(self):
        # 50 states + DC + 8 territories + 3 armed forces = 62
        assert len(USState) == 62

    def test_state_lookup(self):
        assert USState.TX == "Texas"
        assert USState.CA == "California"

    def test_dc(self):
        assert USState.DC == "District of Columbia"

    def test_territories(self):
        assert USState.PR == "Puerto Rico"
        assert USState.GU == "Guam"
        assert USState.VI == "US Virgin Islands"

    def test_armed_forces(self):
        assert USState.AA == "Armed Forces Americas"
        assert USState.AE == "Armed Forces Europe"
        assert USState.AP == "Armed Forces Pacific"


class TestStrEnumBehavior:
    """Verify that all enums behave as proper StrEnums."""

    def test_all_are_strings(self):
        assert isinstance(Instrument.DRUMS, str)
        assert isinstance(Genre.ROCK, str)
        assert isinstance(CommitmentLevel.TOURING, str)
        assert isinstance(ExperienceLevel.EXPERT, str)
        assert isinstance(YearsPlaying.Y1, str)
        assert isinstance(GigsPlayed.OVER_100, str)
        assert isinstance(PracticeFrequency.UNSPECIFIED, str)
        assert isinstance(GigFrequency.UNSPECIFIED, str)
        assert isinstance(Availability.NIGHTS, str)
        assert isinstance(SearchCategory.MUSICIANS, str)
        assert isinstance(USState.TX, str)

    def test_string_operations(self):
        """StrEnum values can be used directly as strings."""
        assert Instrument.ACOUSTIC_GUITAR.lower() == "acoustic guitar"
        assert Genre.CLASSIC_ROCK.replace(" ", "-") == "Classic-Rock"
        assert f"Playing: {Instrument.DRUMS}" == "Playing: Drums"
