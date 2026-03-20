"""Enumerations for BandMix.com data values."""

from enum import StrEnum


class Instrument(StrEnum):
    """Musical instruments recognized by BandMix (36 values)."""

    ACCORDION = "Accordion"
    ACOUSTIC_GUITAR = "Acoustic Guitar"
    BACKGROUND_SINGER = "Background Singer"
    BAGPIPES = "Bagpipes"
    BANJO = "Banjo"
    BASS_GUITAR = "Bass Guitar"
    CELLO = "Cello"
    CLARINET = "Clarinet"
    DJ = "DJ"
    DOBRO = "Dobro"
    DRUMS = "Drums"
    ELECTRONIC_MUSIC = "Electronic Music"
    FIDDLE = "Fiddle"
    FLUTE = "Flute"
    HARMONICA = "Harmonica"
    HARP = "Harp"
    KEYBOARD = "Keyboard"
    LEAD_GUITAR = "Lead Guitar"
    MANDOLIN = "Mandolin"
    OTHER = "Other"
    OTHER_PERCUSSION = "Other Percussion"
    PIANO = "Piano"
    RHYTHM_GUITAR = "Rhythm Guitar"
    SAXOPHONE = "Saxophone"
    STEEL_GUITAR = "Steel guitar"
    TROMBONE = "Trombone"
    TRUMPET = "Trumpet"
    UKULELE = "Ukulele"
    UPRIGHT_BASS = "Upright bass"
    VIOLIN = "Violin"
    VOCALIST = "Vocalist"
    VOCALIST_ALTO = "Vocalist - Alto"
    VOCALIST_BARITONE = "Vocalist - Baritone"
    VOCALIST_BASS = "Vocalist - Bass"
    VOCALIST_SOPRANO = "Vocalist - Soprano"
    VOCALIST_TENOR = "Vocalist - Tenor"


class Genre(StrEnum):
    """Music genres recognized by BandMix (33 values, max 4 selectable)."""

    ACOUSTIC = "Acoustic"
    ALTERNATIVE = "Alternative"
    AMERICANA = "Americana"
    BLUEGRASS = "Bluegrass"
    BLUES = "Blues"
    CALYPSO = "Calypso"
    CELTIC = "Celtic"
    CHRISTIAN_GOSPEL = "Christian / Gospel"
    CHRISTIAN_CONTEMPORARY = "Christian Contemporary"
    CLASSIC_ROCK = "Classic Rock"
    CLASSICAL = "Classical"
    COUNTRY = "Country"
    COVER_TRIBUTE = "Cover/Tribute"
    DUBSTEP = "Dubstep"
    ELECTRONIC = "Electronic"
    FOLK = "Folk"
    FUNK = "Funk"
    HIP_HOP_RAP = "Hip Hop/Rap"
    JAZZ = "Jazz"
    LATIN = "Latin"
    LOUNGE = "Lounge"
    METAL = "Metal"
    OTHER = "Other"
    POP = "Pop"
    PROGRESSIVE = "Progressive"
    PUNK = "Punk"
    RNB = "R&B"
    REGGAE = "Reggae"
    ROCK = "Rock"
    SKA = "Ska"
    SOUTHERN_ROCK = "Southern Rock"
    WORLD = "World"


class CommitmentLevel(StrEnum):
    """Commitment levels for musicians and bands."""

    JUST_FOR_FUN = "Just for Fun"
    MODERATELY_COMMITTED = "Moderately Committed"
    COMMITTED = "Committed"
    VERY_COMMITTED = "Very Committed"
    TOURING = "Touring"


class ExperienceLevel(StrEnum):
    """Instrument experience levels."""

    BEGINNER = "Beginner"
    INTERMEDIATE = "Intermediate"
    MODERATE = "Moderate"
    ADVANCED = "Advanced"
    EXPERT = "Expert"


class YearsPlaying(StrEnum):
    """Years of playing experience."""

    Y1 = "1"
    Y2 = "2"
    Y3 = "3"
    Y4 = "4"
    Y5 = "5"
    Y6 = "6"
    Y7 = "7"
    Y8 = "8"
    Y9 = "9"
    Y10 = "10"
    Y11 = "11"
    Y12 = "12"
    Y13 = "13"
    Y14 = "14"
    Y15 = "15"
    Y20 = "20"
    Y25 = "25"
    Y30 = "30"
    Y35 = "35"
    Y40 = "40"
    Y45 = "45"
    Y50 = "50"
    Y55 = "55"
    Y60_PLUS = "60+"


class GigsPlayed(StrEnum):
    """Number of gigs played."""

    UNSPECIFIED = "Unspecified"
    UNDER_10 = "Under 10"
    FROM_10_TO_50 = "10 to 50"
    FROM_50_TO_100 = "50 to 100"
    OVER_100 = "Over 100"


class PracticeFrequency(StrEnum):
    """How often one practices."""

    UNSPECIFIED = "Unspecified"
    ONCE_PER_WEEK = "1 time per week"
    TWO_THREE_PER_WEEK = "2-3 times per week"
    MORE_THAN_THREE_PER_WEEK = "More than 3 times per week"


class GigFrequency(StrEnum):
    """Desired number of gig nights per week."""

    UNSPECIFIED = "Unspecified"
    ONE_NIGHT = "1 night a week"
    TWO_THREE_NIGHTS = "2-3 nights a week"
    FOUR_FIVE_NIGHTS = "4-5 nights a week"
    SIX_SEVEN_NIGHTS = "6-7 nights a week"


class Availability(StrEnum):
    """Time-of-day availability."""

    UNSPECIFIED = "Unspecified"
    MORNINGS = "Mornings"
    DAYS = "Days"
    NIGHTS = "Nights"


class SearchCategory(StrEnum):
    """Search profile categories."""

    MUSICIANS = "Musicians"
    BANDS = "Bands"
    SONGWRITERS = "Songwriters"
    PHOTOGRAPHERS = "Photographers"
    VENUES = "Venues"
    INDEPENDENT_LABELS = "Independent labels"
    MANAGEMENT = "Management"
    MUSIC_STORES = "Music stores"
    RECORDING_STUDIOS = "Recording studios"
    LIGHTINGS = "Lightings"
    SOUND_ENGINEERS = "Sound engineers"
    MUSIC_TEACHERS = "Music teachers"
    REHEARSAL_SPACE = "Rehearsal space"


class USState(StrEnum):
    """US states, territories, and armed forces regions."""

    # 50 states
    AL = "Alabama"
    AK = "Alaska"
    AZ = "Arizona"
    AR = "Arkansas"
    CA = "California"
    CO = "Colorado"
    CT = "Connecticut"
    DE = "Delaware"
    FL = "Florida"
    GA = "Georgia"
    HI = "Hawaii"
    ID = "Idaho"
    IL = "Illinois"
    IN = "Indiana"
    IA = "Iowa"
    KS = "Kansas"
    KY = "Kentucky"
    LA = "Louisiana"
    ME = "Maine"
    MD = "Maryland"
    MA = "Massachusetts"
    MI = "Michigan"
    MN = "Minnesota"
    MS = "Mississippi"
    MO = "Missouri"
    MT = "Montana"
    NE = "Nebraska"
    NV = "Nevada"
    NH = "New Hampshire"
    NJ = "New Jersey"
    NM = "New Mexico"
    NY = "New York"
    NC = "North Carolina"
    ND = "North Dakota"
    OH = "Ohio"
    OK = "Oklahoma"
    OR = "Oregon"
    PA = "Pennsylvania"
    RI = "Rhode Island"
    SC = "South Carolina"
    SD = "South Dakota"
    TN = "Tennessee"
    TX = "Texas"
    UT = "Utah"
    VT = "Vermont"
    VA = "Virginia"
    WA = "Washington"
    WV = "West Virginia"
    WI = "Wisconsin"
    WY = "Wyoming"
    # District of Columbia
    DC = "District of Columbia"
    # Territories
    AS = "American Samoa"
    GU = "Guam"
    MH = "Marshall Islands"
    FM = "Federated States of Micronesia"
    MP = "Northern Mariana Islands"
    PW = "Palau"
    PR = "Puerto Rico"
    VI = "US Virgin Islands"
    # Armed Forces
    AA = "Armed Forces Americas"
    AE = "Armed Forces Europe"
    AP = "Armed Forces Pacific"


# Additional enums for search, profile, and settings


class Gender(StrEnum):
    """Gender options."""

    ANY = "any"
    MALE = "male"
    FEMALE = "female"


class SearchSort(StrEnum):
    """Search result sort options."""

    LOCATION = "location"
    ACTIVITY = "activity"
    DATE = "date"


class SearchRadius(StrEnum):
    """Search radius in miles."""

    R10 = "10"
    R25 = "25"
    R50 = "50"
    R100 = "100"
    R250 = "250"


class ActiveWithin(StrEnum):
    """Recency filter for search."""

    ONE_WEEK = "1w"
    TWO_WEEKS = "2w"
    THREE_WEEKS = "3w"
    FOUR_WEEKS = "4w"
    FIVE_WEEKS = "5w"
    SIX_WEEKS = "6w"


class ProfileType(StrEnum):
    """Account profile type."""

    MUSICIAN = "Musician"
    BAND = "Band"


class MatchType(StrEnum):
    """Match listing types."""

    NEW_MATCHES = "1"
    NEW_LOCAL_MEMBERS = "2"


class FeedFilter(StrEnum):
    """Activity feed filter options."""

    ALL = "all"
    LOCAL = "local"
    MUSIC_LIST = "music-list"
    MY_FEEDS = "my-feeds"


class ActionType(StrEnum):
    """Activity feed action types."""

    JOINED = "joined"
    UPLOADED_IMAGES = "uploaded_images"
    UPLOADED_MUSIC = "uploaded_music"
    ADDED_VIDEOS = "added_videos"
    UPDATED_INSTRUMENTS = "updated_instruments"
    UPDATED_SEEKING = "updated_seeking"
    CHANGED_PICTURE = "changed_picture"


class EmailFormat(StrEnum):
    """Email format preference."""

    HTML = "html"
    PLAINTEXT = "plaintext"


class EnabledDisabled(StrEnum):
    """Generic enabled/disabled toggle."""

    ENABLED = "enabled"
    DISABLED = "disabled"


class OutputFormat(StrEnum):
    """CLI output format options."""

    JSON = "json"
    TEXT = "text"
    TABLE = "table"
