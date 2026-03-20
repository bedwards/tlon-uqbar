"""Tests for the search command and search results parser."""

from __future__ import annotations

import responses
from click.testing import CliRunner

from bandmix_cli.client import BASE_URL
from bandmix_cli.commands.search import _build_search_params
from bandmix_cli.main import cli
from bandmix_cli.models import SearchResult
from bandmix_cli.parser import parse_search_results

# ---------------------------------------------------------------------------
# Sample HTML for testing the parser
# ---------------------------------------------------------------------------

SAMPLE_SEARCH_HTML = """\
<html>
<body>
<div class="search-result">
  <h3><a href="/jim-stone-123/">Jim Stone</a></h3>
  <span class="location">Austin, TX</span>
  <span class="zip">78701</span>
  <span class="category">Musicians</span>
  <span class="instruments">Acoustic Guitar, Vocalist</span>
  <span class="genres">Country, Folk</span>
  <span class="seeking">Seeking</span>
  <span class="last-active">2 days ago</span>
  <span class="has-image">img</span>
  <span class="has-audio">audio</span>
  <span class="snippet">Singer-songwriter from Austin</span>
</div>
<div class="search-result">
  <h3><a href="/jane-doe-456/">Jane Doe</a></h3>
  <span class="location">Nashville, TN</span>
  <span class="instruments">Piano, Keyboard</span>
  <span class="genres">Jazz, Blues</span>
  <span class="last-active">1 week ago</span>
  <span class="has-video">video</span>
  <span class="snippet">Jazz pianist</span>
</div>
</body>
</html>
"""

EMPTY_SEARCH_HTML = """\
<html>
<body>
<div class="no-results">No results found.</div>
</body>
</html>
"""


# ---------------------------------------------------------------------------
# Parser tests
# ---------------------------------------------------------------------------


class TestParseSearchResults:
    def test_parses_multiple_results(self):
        results, _ = parse_search_results(SAMPLE_SEARCH_HTML)
        assert len(results) == 2

    def test_first_result_fields(self):
        results, _ = parse_search_results(SAMPLE_SEARCH_HTML)
        r = results[0]
        assert isinstance(r, SearchResult)
        assert r.screen_name == "Jim Stone"
        assert r.slug == "jim-stone-123"
        assert r.location == "Austin, TX"
        assert r.zip == "78701"
        assert r.seeking is True
        assert r.last_active == "2 days ago"
        assert r.has_image is True
        assert r.has_audio is True
        assert r.has_video is False
        assert r.snippet == "Singer-songwriter from Austin"

    def test_first_result_instruments(self):
        results, _ = parse_search_results(SAMPLE_SEARCH_HTML)
        r = results[0]
        instrument_values = [i.value for i in r.instruments]
        assert "Acoustic Guitar" in instrument_values
        assert "Vocalist" in instrument_values

    def test_first_result_genres(self):
        results, _ = parse_search_results(SAMPLE_SEARCH_HTML)
        r = results[0]
        genre_values = [g.value for g in r.genres]
        assert "Country" in genre_values
        assert "Folk" in genre_values

    def test_second_result_fields(self):
        results, _ = parse_search_results(SAMPLE_SEARCH_HTML)
        r = results[1]
        assert r.screen_name == "Jane Doe"
        assert r.slug == "jane-doe-456"
        assert r.location == "Nashville, TN"
        assert r.seeking is False
        assert r.has_video is True
        assert r.has_image is False

    def test_empty_results(self):
        results, _ = parse_search_results(EMPTY_SEARCH_HTML)
        assert results == []

    def test_empty_html(self):
        results, _ = parse_search_results("")
        assert results == []


# ---------------------------------------------------------------------------
# _build_search_params tests
# ---------------------------------------------------------------------------


class TestBuildSearchParams:
    def test_default_params(self):
        params = _build_search_params(
            instruments=None,
            location=None,
            radius=None,
            sort=None,
            gender=None,
            age_from=None,
            age_to=None,
            genre=None,
            experience=None,
            commitment=None,
            commitment_mode=None,
            keywords=None,
            has_images=False,
            has_audio=False,
            has_video=False,
            studio=False,
            seeking=False,
            active_within=None,
            page=1,
            name=None,
            member_id=None,
        )
        assert params == {}

    def test_location_and_radius(self):
        params = _build_search_params(
            instruments=None,
            location="Austin, TX",
            radius="50",
            sort=None,
            gender=None,
            age_from=None,
            age_to=None,
            genre=None,
            experience=None,
            commitment=None,
            commitment_mode=None,
            keywords=None,
            has_images=False,
            has_audio=False,
            has_video=False,
            studio=False,
            seeking=False,
            active_within=None,
            page=1,
            name=None,
            member_id=None,
        )
        assert params["location"] == "Austin, TX"
        assert params["radius"] == "50"

    def test_all_flags(self):
        params = _build_search_params(
            instruments="Drums,Bass Guitar",
            location="78701",
            radius="25",
            sort="activity",
            gender="male",
            age_from=21,
            age_to=40,
            genre="Rock,Blues",
            experience="Advanced",
            commitment="Very Committed",
            commitment_mode="exact",
            keywords="session musician",
            has_images=True,
            has_audio=True,
            has_video=True,
            studio=True,
            seeking=True,
            active_within="2w",
            page=3,
            name="Jim",
            member_id="12345",
        )
        assert params["instruments"] == "Drums,Bass Guitar"
        assert params["location"] == "78701"
        assert params["radius"] == "25"
        assert params["sort"] == "activity"
        assert params["gender"] == "m"
        assert params["age_from"] == "21"
        assert params["age_to"] == "40"
        assert params["genre"] == "Rock,Blues"
        assert params["experience"] == "4"
        assert params["commitment"] == "4"
        assert params["commitment_mode"] == "exact"
        assert params["keywords"] == "session musician"
        assert params["has_images"] == "1"
        assert params["has_audio"] == "1"
        assert params["has_video"] == "1"
        assert params["studio"] == "1"
        assert params["seeking"] == "1"
        assert params["active_within"] == "2"
        assert params["page"] == "3"
        assert params["name"] == "Jim"
        assert params["id"] == "12345"

    def test_page_1_not_included(self):
        params = _build_search_params(
            instruments=None,
            location=None,
            radius=None,
            sort=None,
            gender=None,
            age_from=None,
            age_to=None,
            genre=None,
            experience=None,
            commitment=None,
            commitment_mode=None,
            keywords=None,
            has_images=False,
            has_audio=False,
            has_video=False,
            studio=False,
            seeking=False,
            active_within=None,
            page=1,
            name=None,
            member_id=None,
        )
        assert "page" not in params

    def test_gender_any_not_included(self):
        params = _build_search_params(
            instruments=None,
            location=None,
            radius=None,
            sort=None,
            gender="any",
            age_from=None,
            age_to=None,
            genre=None,
            experience=None,
            commitment=None,
            commitment_mode=None,
            keywords=None,
            has_images=False,
            has_audio=False,
            has_video=False,
            studio=False,
            seeking=False,
            active_within=None,
            page=1,
            name=None,
            member_id=None,
        )
        assert "gender" not in params


# ---------------------------------------------------------------------------
# CLI command integration tests
# ---------------------------------------------------------------------------


class TestSearchCommand:
    @responses.activate
    def test_search_default(self):
        responses.add(
            responses.GET,
            f"{BASE_URL}/search/musicians/",
            body=SAMPLE_SEARCH_HTML,
            status=200,
        )
        runner = CliRunner()
        result = runner.invoke(cli, ["search", "--format", "json"])
        assert result.exit_code == 0
        assert "Jim Stone" in result.output
        assert "Jane Doe" in result.output

    @responses.activate
    def test_search_with_category_bands(self):
        responses.add(
            responses.GET,
            f"{BASE_URL}/search/bands/",
            body=SAMPLE_SEARCH_HTML,
            status=200,
        )
        runner = CliRunner()
        result = runner.invoke(
            cli, ["search", "--category", "bands", "--format", "json"]
        )
        assert result.exit_code == 0

    @responses.activate
    def test_search_with_location(self):
        responses.add(
            responses.GET,
            f"{BASE_URL}/search/musicians/",
            body=SAMPLE_SEARCH_HTML,
            status=200,
        )
        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "search",
                "--location",
                "78701",
                "--radius",
                "25",
                "--format",
                "json",
            ],
        )
        assert result.exit_code == 0
        assert "Jim Stone" in result.output

    @responses.activate
    def test_search_with_instruments(self):
        responses.add(
            responses.GET,
            f"{BASE_URL}/search/musicians/",
            body=SAMPLE_SEARCH_HTML,
            status=200,
        )
        runner = CliRunner()
        result = runner.invoke(
            cli,
            ["search", "--instruments", "Drums,Bass Guitar", "--format", "json"],
        )
        assert result.exit_code == 0

    @responses.activate
    def test_search_with_filters(self):
        responses.add(
            responses.GET,
            f"{BASE_URL}/search/musicians/",
            body=SAMPLE_SEARCH_HTML,
            status=200,
        )
        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "search",
                "--gender",
                "male",
                "--age-from",
                "21",
                "--age-to",
                "40",
                "--genre",
                "Rock",
                "--experience",
                "Advanced",
                "--commitment",
                "Very Committed",
                "--commitment-mode",
                "exact",
                "--format",
                "json",
            ],
        )
        assert result.exit_code == 0

    @responses.activate
    def test_search_with_boolean_flags(self):
        responses.add(
            responses.GET,
            f"{BASE_URL}/search/musicians/",
            body=SAMPLE_SEARCH_HTML,
            status=200,
        )
        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "search",
                "--has-images",
                "--has-audio",
                "--has-video",
                "--studio",
                "--seeking",
                "--format",
                "json",
            ],
        )
        assert result.exit_code == 0

    @responses.activate
    def test_search_with_keywords(self):
        responses.add(
            responses.GET,
            f"{BASE_URL}/search/musicians/",
            body=SAMPLE_SEARCH_HTML,
            status=200,
        )
        runner = CliRunner()
        result = runner.invoke(
            cli,
            ["search", "--keywords", "session musician", "--format", "json"],
        )
        assert result.exit_code == 0

    @responses.activate
    def test_search_with_active_within(self):
        responses.add(
            responses.GET,
            f"{BASE_URL}/search/musicians/",
            body=SAMPLE_SEARCH_HTML,
            status=200,
        )
        runner = CliRunner()
        result = runner.invoke(
            cli,
            ["search", "--active-within", "2w", "--format", "json"],
        )
        assert result.exit_code == 0

    @responses.activate
    def test_search_by_name(self):
        responses.add(
            responses.GET,
            f"{BASE_URL}/search/musicians/",
            body=SAMPLE_SEARCH_HTML,
            status=200,
        )
        runner = CliRunner()
        result = runner.invoke(
            cli, ["search", "--name", "Jim Stone", "--format", "json"]
        )
        assert result.exit_code == 0
        assert "Jim Stone" in result.output

    @responses.activate
    def test_search_by_id(self):
        responses.add(
            responses.GET,
            f"{BASE_URL}/search/musicians/",
            body=SAMPLE_SEARCH_HTML,
            status=200,
        )
        runner = CliRunner()
        result = runner.invoke(cli, ["search", "--id", "123456", "--format", "json"])
        assert result.exit_code == 0

    @responses.activate
    def test_search_empty_results(self):
        responses.add(
            responses.GET,
            f"{BASE_URL}/search/musicians/",
            body=EMPTY_SEARCH_HTML,
            status=200,
        )
        runner = CliRunner()
        result = runner.invoke(cli, ["search", "--format", "json"])
        assert result.exit_code == 0
        assert "No results found." in result.output

    @responses.activate
    def test_search_raw_format(self):
        responses.add(
            responses.GET,
            f"{BASE_URL}/search/musicians/",
            body=SAMPLE_SEARCH_HTML,
            status=200,
        )
        runner = CliRunner()
        result = runner.invoke(cli, ["search", "--format", "raw"])
        assert result.exit_code == 0
        assert "search-result" in result.output

    @responses.activate
    def test_search_table_format(self):
        responses.add(
            responses.GET,
            f"{BASE_URL}/search/musicians/",
            body=SAMPLE_SEARCH_HTML,
            status=200,
        )
        runner = CliRunner()
        result = runner.invoke(cli, ["search", "--format", "table"])
        assert result.exit_code == 0
        assert "Jim Stone" in result.output

    @responses.activate
    def test_search_text_format(self):
        responses.add(
            responses.GET,
            f"{BASE_URL}/search/musicians/",
            body=SAMPLE_SEARCH_HTML,
            status=200,
        )
        runner = CliRunner()
        result = runner.invoke(cli, ["search", "--format", "text"])
        assert result.exit_code == 0
        assert "Jim Stone" in result.output

    @responses.activate
    def test_search_with_limit(self):
        responses.add(
            responses.GET,
            f"{BASE_URL}/search/musicians/",
            body=SAMPLE_SEARCH_HTML,
            status=200,
        )
        runner = CliRunner()
        result = runner.invoke(cli, ["search", "--limit", "1", "--format", "json"])
        assert result.exit_code == 0
        assert "Jim Stone" in result.output
        # Only 1 result should be returned
        assert "Jane Doe" not in result.output

    @responses.activate
    def test_search_with_page(self):
        responses.add(
            responses.GET,
            f"{BASE_URL}/search/musicians/",
            body=SAMPLE_SEARCH_HTML,
            status=200,
        )
        runner = CliRunner()
        result = runner.invoke(cli, ["search", "--page", "2", "--format", "json"])
        assert result.exit_code == 0

    @responses.activate
    def test_search_sort_option(self):
        responses.add(
            responses.GET,
            f"{BASE_URL}/search/musicians/",
            body=SAMPLE_SEARCH_HTML,
            status=200,
        )
        runner = CliRunner()
        result = runner.invoke(
            cli, ["search", "--sort", "activity", "--format", "json"]
        )
        assert result.exit_code == 0

    @responses.activate
    def test_search_industry_category(self):
        responses.add(
            responses.GET,
            f"{BASE_URL}/search/industry/",
            body=SAMPLE_SEARCH_HTML,
            status=200,
        )
        runner = CliRunner()
        result = runner.invoke(
            cli, ["search", "--category", "industry", "--format", "json"]
        )
        assert result.exit_code == 0
