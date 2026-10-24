"""Integration tests for the Data Legion Python SDK.

These tests call the real Data Legion API. Set the DATALEGION_API_KEY
environment variable to run them.
"""

from __future__ import annotations

import os
from typing import ClassVar
from unittest.mock import AsyncMock, patch

import httpx
import pytest

from datalegion import (
    AsyncDataLegion,
    BulkCompanyEnrichResponse,
    BulkPersonEnrichResponse,
    DataLegion,
    DynamicBulkPersonEnrichResponse,
    EmailHashResponse,
    FieldCleanResponse,
    HealthResponse,
    PersonMatchesResponse,
    PersonResponse,
    ValidationResponse,
)
from datalegion._client import _first_match, _safe_int, _strip_none
from datalegion._exceptions import (
    APIError,
    AuthenticationError,
    BadRequestError,
    InsufficientCreditsError,
    NotFoundError,
    PermissionDeniedError,
    RateLimitError,
    RequestTimeoutError,
    ServerError,
    ValidationError,
)

API_KEY = os.environ.get("DATALEGION_API_KEY", "")

requires_api_key = pytest.mark.skipif(not API_KEY, reason="No DATALEGION_API_KEY set")
integration = pytest.mark.integration

# No real person in the code: person lookups that need a match run in sandbox mode, whose record fills
# every field and names no one; a bad key fails before the input matters.
MADE_UP_PROFILE = "https://www.linkedin.com/in/jane-exampleton-0001/"


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def client():
    """Create a sync client for the test session."""
    c = DataLegion(api_key=API_KEY)
    yield c
    c.close()


@pytest.fixture
async def async_client():
    """Create an async client for the test session."""
    c = AsyncDataLegion(api_key=API_KEY)
    yield c
    await c.close()


@pytest.fixture
def sandbox_client():
    """A sync client in sandbox mode: sample records, no credits."""
    c = DataLegion(api_key=API_KEY, sandbox=True)
    yield c
    c.close()


@pytest.fixture
async def async_sandbox_client():
    """An async client in sandbox mode: sample records, no credits."""
    c = AsyncDataLegion(api_key=API_KEY, sandbox=True)
    yield c
    await c.close()


# ---------------------------------------------------------------------------
# Client initialization
# ---------------------------------------------------------------------------


class TestClientInit:
    """Tests for client initialization (no API call needed)."""

    def test_missing_api_key_raises(self, monkeypatch):
        """Creating a client without an API key raises AuthenticationError."""
        monkeypatch.delenv("DATALEGION_API_KEY", raising=False)
        with pytest.raises(AuthenticationError):
            DataLegion(api_key="")

    def test_missing_api_key_async_raises(self, monkeypatch):
        """Creating an async client without an API key raises AuthenticationError."""
        monkeypatch.delenv("DATALEGION_API_KEY", raising=False)
        with pytest.raises(AuthenticationError):
            AsyncDataLegion(api_key="")

    @pytest.mark.parametrize("client_cls", [DataLegion, AsyncDataLegion])
    def test_api_key_is_trimmed(self, client_cls, monkeypatch):
        """A key passed or set with surrounding whitespace (e.g. a trailing newline) is trimmed."""
        assert client_cls(api_key="  legion_abc\n")._api_key == "legion_abc"
        monkeypatch.setenv("DATALEGION_API_KEY", "legion_env\n")
        assert client_cls()._api_key == "legion_env"

    @pytest.mark.parametrize("client_cls", [DataLegion, AsyncDataLegion])
    def test_whitespace_only_api_key_raises(self, client_cls, monkeypatch):
        """A key that is only whitespace counts as missing."""
        monkeypatch.delenv("DATALEGION_API_KEY", raising=False)
        with pytest.raises(AuthenticationError):
            client_cls(api_key=" \n")

    @requires_api_key
    def test_explicit_api_key(self):
        """Explicit api_key argument works."""
        c = DataLegion(api_key=API_KEY)
        assert c._api_key == API_KEY
        c.close()

    @requires_api_key
    def test_env_var_api_key(self, monkeypatch):
        """Client picks up API key from environment variable."""
        monkeypatch.setenv("DATALEGION_API_KEY", API_KEY)
        c = DataLegion()
        assert c._api_key == API_KEY
        c.close()

    @requires_api_key
    def test_context_manager(self):
        """Client works as a context manager."""
        with DataLegion(api_key=API_KEY) as c:
            assert c._api_key == API_KEY

    @requires_api_key
    async def test_async_context_manager(self):
        """Async client works as a context manager."""
        async with AsyncDataLegion(api_key=API_KEY) as c:
            assert c._api_key == API_KEY


# ---------------------------------------------------------------------------
# Error handling
# ---------------------------------------------------------------------------


class TestErrorHandling:
    """Tests for error handling."""

    def test_bad_api_key_raises_authentication_error(self):
        """A request with a bad API key raises AuthenticationError."""
        c = DataLegion(api_key="legion_invalid_key_000000000000")
        with pytest.raises(AuthenticationError) as exc_info:
            c.person.enrich(social_url=MADE_UP_PROFILE)
        assert exc_info.value.status_code == 401
        c.close()

    async def test_async_bad_api_key_raises_authentication_error(self):
        """An async request with a bad API key raises AuthenticationError."""
        c = AsyncDataLegion(api_key="legion_invalid_key_000000000000")
        with pytest.raises(AuthenticationError) as exc_info:
            await c.person.enrich(social_url=MADE_UP_PROFILE)
        assert exc_info.value.status_code == 401
        await c.close()


# ---------------------------------------------------------------------------
# Person endpoints
# ---------------------------------------------------------------------------


@requires_api_key
@integration
class TestPersonEnrich:
    """Tests for person enrichment."""

    def test_enrich_by_social_url(self, sandbox_client):
        """Enrich a person by LinkedIn URL returns a PersonResponse (sandbox record)."""
        result = sandbox_client.person.enrich(social_url=MADE_UP_PROFILE)
        assert isinstance(result, PersonResponse)
        assert isinstance(result.legion_id, str)
        assert result.full_name is not None
        assert result.first_name is not None
        assert result.last_name is not None

    def test_enrich_multiple_results(self, sandbox_client):
        """Enrich with multiple_results returns a PersonMatchesResponse."""
        result = sandbox_client.person.enrich(social_url=MADE_UP_PROFILE, multiple_results=True)
        assert isinstance(result, PersonMatchesResponse)
        assert isinstance(result.total, int)
        assert isinstance(result.matches, list)
        assert len(result.matches) > 0
        assert isinstance(result.matches[0].person, PersonResponse)

    def test_enrich_response_headers(self, sandbox_client):
        """Response headers are populated after a request."""
        sandbox_client.person.enrich(social_url=MADE_UP_PROFILE)
        assert sandbox_client.request_id is not None
        assert isinstance(sandbox_client.request_id, str)
        assert len(sandbox_client.request_id) > 0

    async def test_async_enrich_by_social_url(self, async_sandbox_client):
        """Async enrich a person by LinkedIn URL returns a PersonResponse (sandbox record)."""
        result = await async_sandbox_client.person.enrich(social_url=MADE_UP_PROFILE)
        assert isinstance(result, PersonResponse)
        assert isinstance(result.legion_id, str)
        assert result.full_name is not None

    async def test_async_enrich_response_headers(self, async_sandbox_client):
        """Async response headers are populated after a request."""
        await async_sandbox_client.person.enrich(social_url=MADE_UP_PROFILE)
        assert async_sandbox_client.request_id is not None
        assert isinstance(async_sandbox_client.request_id, str)


class TestDynamicBulkEnrich:
    """Dynamic bulk enrich (phones/emails only) — mocked, no live API key needed."""

    _FAKE: ClassVar[dict] = {
        "results": [
            {
                "metadata": {"row": "r0"},
                "legion_id": "L1",
                "phones": [{"number": "+14255551234", "type": "mobile"}],
                "mobile_phone": "+14255551234",
            },
            {
                "metadata": {"row": "r1"},
                "legion_id": "L2",
                "emails": [{"address": "john@y.com"}],
                "work_email": "john@y.com",
            },
            {
                "metadata": {"row": "r2"},
                "legion_id": "L3",
                "phones": [{"number": "+12065559999"}],
                "mobile_phone": "+12065559999",
                "emails": [{"address": "jane@x.com"}],
                "work_email": "jane@x.com",
            },
            # No match: the URL resolved to nobody — null legion_id, no fields, no error.
            {"metadata": {"row": "r3"}, "legion_id": None},
            # Errored item: no covering pool, surfaced in its own slot with an error.
            {
                "metadata": {"row": "r4"},
                "legion_id": None,
                "error": "No contract entitles the requested fields.",
            },
        ]
    }
    # All three accepted field shapes (phones / emails / both) plus a no-match and an
    # errored item, so the response covers every per-item outcome the endpoint returns.
    _ITEMS: ClassVar[list[dict]] = [
        {
            "social_url": "https://www.linkedin.com/in/jane",
            "fields": ["phones"],
            "metadata": {"row": "r0"},
        },
        {
            "social_url": "https://www.linkedin.com/in/john",
            "fields": ["emails"],
            "metadata": {"row": "r1"},
        },
        {
            "social_url": "https://www.linkedin.com/in/jim",
            "fields": ["phones", "emails"],
            "metadata": {"row": "r2"},
        },
        {
            "social_url": "https://www.linkedin.com/in/nobody",
            "fields": ["phones"],
            "metadata": {"row": "r3"},
        },
        {
            "social_url": "https://www.linkedin.com/in/uncovered",
            "fields": ["emails"],
            "metadata": {"row": "r4"},
        },
    ]

    def test_dynamic_bulk_enrich_posts_and_parses(self):
        """Posts to /dynamic/person/enrich/bulk and parses phones + error rows."""
        c = DataLegion(api_key="legion_test")
        with patch.object(c, "_post", return_value=self._FAKE) as mock_post:
            resp = c.person.dynamic_bulk_enrich(self._ITEMS)
        mock_post.assert_called_once_with("/dynamic/person/enrich/bulk", {"items": self._ITEMS})
        assert isinstance(resp, DynamicBulkPersonEnrichResponse)
        # phones-only row
        assert resp.results[0].legion_id == "L1"
        assert resp.results[0].phones[0].number == "+14255551234"
        assert resp.results[0].mobile_phone == "+14255551234"
        assert resp.results[0].emails is None
        # emails-only row
        assert resp.results[1].legion_id == "L2"
        assert resp.results[1].emails[0].address == "john@y.com"
        assert resp.results[1].work_email == "john@y.com"
        assert resp.results[1].phones is None
        # phones + emails row (the combined group request)
        assert resp.results[2].phones[0].number == "+12065559999"
        assert resp.results[2].emails[0].address == "jane@x.com"
        assert resp.results[2].mobile_phone == "+12065559999"
        assert resp.results[2].work_email == "jane@x.com"
        # no-match row: null legion_id, no fields, no error
        assert resp.results[3].legion_id is None
        assert resp.results[3].error is None
        assert resp.results[3].phones is None
        assert resp.results[3].emails is None
        # errored row: null legion_id with an error message
        assert resp.results[4].legion_id is None
        assert resp.results[4].error == "No contract entitles the requested fields."
        c.close()

    async def test_async_dynamic_bulk_enrich_posts_and_parses(self):
        """Async variant posts to the same path and parses the same shape."""
        c = AsyncDataLegion(api_key="legion_test")
        with patch.object(c, "_post", new=AsyncMock(return_value=self._FAKE)) as mock_post:
            resp = await c.person.dynamic_bulk_enrich(self._ITEMS)
        mock_post.assert_awaited_once_with("/dynamic/person/enrich/bulk", {"items": self._ITEMS})
        assert isinstance(resp, DynamicBulkPersonEnrichResponse)
        assert resp.results[0].mobile_phone == "+14255551234"
        await c.close()


def _mock_client(handler) -> DataLegion:
    """A sync client whose transport is a MockTransport (no live API, no key)."""
    return DataLegion(
        api_key="legion_test",
        httpx_client=httpx.Client(transport=httpx.MockTransport(handler)),
    )


class TestRequestCore:
    """HTTP core: status→exception mapping, header capture, helpers — all mocked."""

    @pytest.mark.parametrize(
        "status,exc",
        [
            (400, BadRequestError),
            (401, AuthenticationError),
            (402, InsufficientCreditsError),
            (403, PermissionDeniedError),
            (404, NotFoundError),
            (408, RequestTimeoutError),
            (409, APIError),
            (422, ValidationError),
            (429, RateLimitError),
            (500, ServerError),
            (501, ServerError),
            (502, ServerError),
            (503, ServerError),
            (504, ServerError),
        ],
    )
    def test_status_maps_to_exception(self, status, exc):
        def handler(_request):
            return httpx.Response(
                status, json={"error": "e_code", "message": "boom", "details": {"k": "v"}}
            )

        with _mock_client(handler) as c, pytest.raises(exc) as ei:
            c.health()
        assert ei.value.status_code == status
        assert ei.value.error == "e_code"
        assert ei.value.details == {"k": "v"}

    @pytest.mark.parametrize(
        "exc",
        [BadRequestError, PermissionDeniedError, NotFoundError, RequestTimeoutError, ServerError],
    )
    def test_new_status_classes_stay_api_errors(self, exc):
        # These statuses raised APIError before they had their own class.
        assert issubclass(exc, APIError)

    def test_error_body_non_json_falls_back_to_text(self):
        def handler(_request):
            return httpx.Response(500, text="upstream boom")

        with _mock_client(handler) as c, pytest.raises(APIError) as ei:
            c.health()
        assert ei.value.status_code == 500
        assert "upstream boom" in ei.value.message

    def test_captures_headers_and_unlimited_is_none(self):
        def handler(_request):
            return httpx.Response(
                200,
                json={"status": "ok"},
                headers={
                    "Request-ID": "req_123",
                    "Credits-Used": "3",
                    "Credits-Remaining": "unlimited",  # non-numeric → None, not an error
                    "RateLimit-Limit": "100",
                    "Total-Count-Status": "estimate",
                    "Search-Warning": "No company_industry value matches 'x'",
                },
            )

        with _mock_client(handler) as c:
            c.health()
            assert c.request_id == "req_123"
            assert c.credits_used == 3
            assert c.credits_remaining is None
            assert c.rate_limit_limit == 100
            assert c.total_count_status == "estimate"
            assert c.search_warning == "No company_industry value matches 'x'"

    def test_search_warning_is_none_without_the_header(self):
        def handler(_request):
            return httpx.Response(200, json={"status": "ok"})

        with _mock_client(handler) as c:
            c.health()
            assert c.search_warning is None

    async def test_async_search_warning_is_read_and_reset(self):
        responses = iter(
            [
                httpx.Response(200, json={"status": "ok"}, headers={"Search-Warning": "flagged"}),
                httpx.Response(200, json={"status": "ok"}),
            ]
        )
        c = AsyncDataLegion(
            api_key="legion_test",
            httpx_client=httpx.AsyncClient(
                transport=httpx.MockTransport(lambda _r: next(responses))
            ),
        )
        await c.health()
        assert c.search_warning == "flagged"
        await c.health()
        assert c.search_warning is None
        await c.close()

    def test_single_enrich_empty_matches_raises_clean_404(self):
        # A 200 with no matches must not IndexError — it raises a clean 404.
        def handler(_request):
            return httpx.Response(200, json={"matches": [], "total": 0})

        with _mock_client(handler) as c, pytest.raises(NotFoundError) as ei:
            c.person.enrich(social_url="https://www.linkedin.com/in/x")
        assert ei.value.status_code == 404
        assert ei.value.error == "not_found"

    def test_safe_int_and_strip_none_helpers(self):
        assert _safe_int("5") == 5
        assert _safe_int("unlimited") is None
        assert _safe_int(None) is None
        assert _strip_none({"a": 1, "b": None, "c": 0}) == {"a": 1, "c": 0}
        assert _first_match({"matches": [{"person": {"legion_id": "L1"}}]}, "person") == {
            "legion_id": "L1"
        }


@requires_api_key
@integration
@pytest.mark.flaky(reruns=2, reruns_delay=10)
class TestPersonSearch:
    """Tests for person search."""

    def test_search_returns_matches(self, client):
        """Person search returns a PersonMatchesResponse."""
        result = client.person.search(
            query="SELECT * FROM people WHERE job_title ILIKE '%engineer%' AND company_name ILIKE '%google%'",
            limit=1,
        )
        assert isinstance(result, PersonMatchesResponse)
        assert isinstance(result.matches, list)
        assert isinstance(result.total, int)
        if result.matches:
            assert isinstance(result.matches[0].person, PersonResponse)

    async def test_async_search_returns_matches(self, async_client):
        """Async person search returns a PersonMatchesResponse."""
        result = await async_client.person.search(
            query="SELECT * FROM people WHERE job_title ILIKE '%engineer%' AND company_name ILIKE '%google%'",
            limit=1,
        )
        assert isinstance(result, PersonMatchesResponse)
        assert isinstance(result.matches, list)


@requires_api_key
@integration
@pytest.mark.flaky(reruns=2, reruns_delay=10)
class TestPersonDiscover:
    """Tests for person discover."""

    def test_discover_returns_matches(self, client):
        """Person discover returns a PersonMatchesResponse."""
        result = client.person.discover(query="find software engineers at google", limit=1)
        assert isinstance(result, PersonMatchesResponse)
        assert isinstance(result.matches, list)
        assert isinstance(result.total, int)
        if result.matches:
            assert isinstance(result.matches[0].person, PersonResponse)

    async def test_async_discover_returns_matches(self, async_client):
        """Async person discover returns a PersonMatchesResponse."""
        result = await async_client.person.discover(
            query="find software engineers at google", limit=1
        )
        assert isinstance(result, PersonMatchesResponse)
        assert isinstance(result.matches, list)


@requires_api_key
@integration
class TestPersonBulkEnrich:
    """Tests for person bulk enrichment."""

    def test_bulk_enrich_returns_results(self, sandbox_client):
        """Bulk person enrich returns a BulkPersonEnrichResponse."""
        result = sandbox_client.person.bulk_enrich(
            items=[{"social_url": MADE_UP_PROFILE}],
        )
        assert isinstance(result, BulkPersonEnrichResponse)
        assert isinstance(result.results, list)
        assert len(result.results) > 0

    async def test_async_bulk_enrich_returns_results(self, async_sandbox_client):
        """Async bulk person enrich returns a BulkPersonEnrichResponse."""
        result = await async_sandbox_client.person.bulk_enrich(
            items=[{"social_url": MADE_UP_PROFILE}],
        )
        assert isinstance(result, BulkPersonEnrichResponse)
        assert isinstance(result.results, list)
        assert len(result.results) > 0


# ---------------------------------------------------------------------------
# Company endpoints
# ---------------------------------------------------------------------------


@requires_api_key
@integration
class TestCompanyEnrich:
    """Tests for company enrichment."""

    def test_enrich_by_domain(self, client):
        """Enrich a company by domain returns expected fields."""
        result = client.company.enrich(domain="google.com")
        assert isinstance(result.legion_id, str)

    async def test_async_enrich_by_domain(self, async_client):
        """Async enrich a company by domain returns expected fields."""
        result = await async_client.company.enrich(domain="google.com")
        assert isinstance(result.legion_id, str)


@requires_api_key
@integration
class TestCompanyBulkEnrich:
    """Tests for company bulk enrichment."""

    def test_bulk_enrich_returns_results(self, client):
        """Bulk company enrich returns a BulkCompanyEnrichResponse."""
        result = client.company.bulk_enrich(
            items=[{"domain": "google.com"}],
        )
        assert isinstance(result, BulkCompanyEnrichResponse)
        assert isinstance(result.results, list)
        assert len(result.results) > 0

    async def test_async_bulk_enrich_returns_results(self, async_client):
        """Async bulk company enrich returns a BulkCompanyEnrichResponse."""
        result = await async_client.company.bulk_enrich(
            items=[{"domain": "google.com"}],
        )
        assert isinstance(result, BulkCompanyEnrichResponse)
        assert isinstance(result.results, list)
        assert len(result.results) > 0


@requires_api_key
@integration
@pytest.mark.flaky(reruns=2, reruns_delay=10)
class TestCompanySearch:
    """Tests for company search."""

    def test_search_returns_matches(self, client):
        """Company search returns matches list."""
        result = client.company.search(
            query="SELECT * FROM companies WHERE domain ILIKE '%google%'",
            limit=1,
        )
        assert isinstance(result.matches, list)

    async def test_async_search_returns_matches(self, async_client):
        """Async company search returns matches list."""
        result = await async_client.company.search(
            query="SELECT * FROM companies WHERE domain ILIKE '%google%'",
            limit=1,
        )
        assert isinstance(result.matches, list)


@requires_api_key
@integration
@pytest.mark.flaky(reruns=2, reruns_delay=10)
class TestCompanyDiscover:
    """Tests for company discover."""

    def test_discover_returns_matches(self, client):
        """Company discover returns matches list."""
        result = client.company.discover(
            query="enterprise software companies with over 1000 employees", limit=1
        )
        assert isinstance(result.matches, list)

    async def test_async_discover_returns_matches(self, async_client):
        """Async company discover returns matches list."""
        result = await async_client.company.discover(
            query="enterprise software companies with over 1000 employees", limit=1
        )
        assert isinstance(result.matches, list)


# ---------------------------------------------------------------------------
# Utility endpoints
# ---------------------------------------------------------------------------


@requires_api_key
@integration
class TestUtilityClean:
    """Tests for utility clean endpoint."""

    def test_clean_email(self, client):
        """Clean normalizes an email address."""
        result = client.utility.clean(fields={"email": "  JOHN@EXAMPLE.COM  "})
        assert isinstance(result, FieldCleanResponse)
        assert "email" in result.results
        email_result = result.results["email"]
        assert email_result.original == "  JOHN@EXAMPLE.COM  "
        assert email_result.cleaned is not None

    async def test_async_clean_email(self, async_client):
        """Async clean normalizes an email address."""
        result = await async_client.utility.clean(fields={"email": "  JOHN@EXAMPLE.COM  "})
        assert isinstance(result, FieldCleanResponse)
        assert "email" in result.results


@requires_api_key
@integration
class TestUtilityHashEmail:
    """Tests for utility hash email endpoint."""

    def test_hash_email(self, client):
        """Hash email returns expected hash fields."""
        result = client.utility.hash_email(email="jane.doe@gmail.com")
        assert isinstance(result, EmailHashResponse)
        assert result.email == "jane.doe@gmail.com"
        assert result.normalized_email is not None
        assert isinstance(result.hashes, dict)
        assert "sha256" in result.hashes
        assert "sha1" in result.hashes
        assert "md5" in result.hashes

    async def test_async_hash_email(self, async_client):
        """Async hash email returns expected hash fields."""
        result = await async_client.utility.hash_email(email="jane.doe@gmail.com")
        assert isinstance(result, EmailHashResponse)
        assert result.email == "jane.doe@gmail.com"
        assert isinstance(result.hashes, dict)


@requires_api_key
@integration
class TestUtilityValidate:
    """Tests for utility validate endpoint."""

    def test_validate_email(self, client):
        """Validate returns expected validation structure."""
        result = client.utility.validate(email="jane.doe@gmail.com")
        assert isinstance(result, ValidationResponse)
        assert isinstance(result.valid, bool)
        assert isinstance(result.errors, list)
        assert isinstance(result.warnings, list)
        assert isinstance(result.suggestions, list)

    async def test_async_validate_email(self, async_client):
        """Async validate returns expected validation structure."""
        result = await async_client.utility.validate(email="jane.doe@gmail.com")
        assert isinstance(result, ValidationResponse)
        assert isinstance(result.valid, bool)
        assert isinstance(result.errors, list)
        assert isinstance(result.warnings, list)
        assert isinstance(result.suggestions, list)


@requires_api_key
@integration
class TestUtilityReport:
    """Tests for utility report endpoints (no real reports are recorded)."""

    def test_invalid_combination_rejected(self, client):
        """frankenstein at field level is rejected server-side with 422."""
        with pytest.raises(ValidationError):
            client.utility.report_person(
                legion_id="abc",
                issue_type="frankenstein",
                issue_level="field",
                field="job_title",
                comment="x",
            )


class TestUtilityReportUnit:
    """Mocked unit tests for the report methods.

    The integration test above only exercises a rejection path against the
    live API. These mock the transport so we assert — offline, with no real
    reports recorded — that each method posts the right path/body and parses
    the response, for both subjects and both sync/async clients.
    """

    _RESPONSE: ClassVar[dict] = {
        "report_id": 42,
        "status": "new",
        "subject_type": "person",
        "legion_id": "abc123",
        "issue_type": "outdated",
        "issue_level": "field",
        "field": "job_title",
        "created_at": "2026-06-14T00:00:00Z",
    }

    def test_report_person_posts_correct_path_and_body(self):
        c = DataLegion(api_key="test")
        with patch.object(c, "_post", return_value=self._RESPONSE) as post:
            result = c.utility.report_person(
                legion_id="abc123",
                issue_type="outdated",
                issue_level="field",
                field="job_title",
                correct_value="Chairman",
            )
        path, body = post.call_args.args
        assert path == "/utility/report/person"
        assert body == {
            "legion_id": "abc123",
            "issue_type": "outdated",
            "issue_level": "field",
            "field": "job_title",
            "correct_value": "Chairman",
        }  # observed_value / comment are None and stripped
        assert result.report_id == 42
        assert result.status == "new"

    def test_report_company_posts_correct_path_and_strips_none(self):
        c = DataLegion(api_key="test")
        resp = {**self._RESPONSE, "subject_type": "company", "issue_level": "record", "field": None}
        with patch.object(c, "_post", return_value=resp) as post:
            result = c.utility.report_company(
                legion_id="xyz",
                issue_type="duplicate",
                issue_level="record",
                comment="dupe of abc123",
            )
        path, body = post.call_args.args
        assert path == "/utility/report/company"
        assert body == {
            "legion_id": "xyz",
            "issue_type": "duplicate",
            "issue_level": "record",
            "comment": "dupe of abc123",
        }
        assert result.subject_type == "company"

    async def test_async_report_person_posts_correct_path(self):
        c = AsyncDataLegion(api_key="test")
        with patch.object(c, "_post", new=AsyncMock(return_value=self._RESPONSE)) as post:
            result = await c.utility.report_person(
                legion_id="abc123",
                issue_type="outdated",
                issue_level="record",
            )
        path, body = post.call_args.args
        assert path == "/utility/report/person"
        assert body == {
            "legion_id": "abc123",
            "issue_type": "outdated",
            "issue_level": "record",
        }
        assert result.report_id == 42

    async def test_async_report_company_posts_correct_path(self):
        c = AsyncDataLegion(api_key="test")
        resp = {**self._RESPONSE, "subject_type": "company"}
        with patch.object(c, "_post", new=AsyncMock(return_value=resp)) as post:
            result = await c.utility.report_company(
                legion_id="xyz",
                issue_type="incorrect",
                issue_level="field",
                field="industry",
                observed_value="Retail",
                correct_value="Software Development",
            )
        assert post.call_args.args[0] == "/utility/report/company"
        assert result.subject_type == "company"


# ---------------------------------------------------------------------------
# Health endpoint
# ---------------------------------------------------------------------------


@requires_api_key
@integration
class TestHealth:
    """Tests for the health endpoint."""

    def test_health(self, client):
        """Health endpoint returns a HealthResponse."""
        result = client.health()
        assert isinstance(result, HealthResponse)
        assert result.status == "healthy"

    async def test_async_health(self, async_client):
        """Async health endpoint returns a HealthResponse."""
        result = await async_client.health()
        assert isinstance(result, HealthResponse)
        assert result.status == "healthy"


class TestCompanyLocationsParse:
    """Company `locations` parse into typed CompanyLocation objects (mocked, no key)."""

    def test_locations_are_typed_and_keep_order(self):
        body = {
            "matches": [
                {
                    "company": {
                        "legion_id": "c1",
                        "locations": [
                            {
                                "city": "south san francisco",
                                "state_code": "US-CA",
                                "country_code": "US",
                                "current": True,
                                "primary": True,
                                "raw": ["354 Oyster Point Blvd, South San Francisco, CA"],
                            },
                            {
                                "city": "dublin",
                                "country_code": "IE",
                                "current": True,
                                "primary": False,
                                "raw": [],
                            },
                        ],
                    },
                    "match_metadata": None,
                }
            ],
            "total": 1,
        }

        with _mock_client(lambda _r: httpx.Response(200, json=body)) as c:
            company = c.company.enrich(domain="stripe.com")
        from datalegion import CompanyLocation

        assert all(isinstance(loc, CompanyLocation) for loc in company.locations)
        assert [(loc.city, loc.primary, loc.current) for loc in company.locations] == [
            ("south san francisco", True, True),
            ("dublin", False, True),
        ]

    def test_a_response_without_locations_defaults_to_empty(self):
        body = {"matches": [{"company": {"legion_id": "c1"}}], "total": 1}
        with _mock_client(lambda _r: httpx.Response(200, json=body)) as c:
            assert c.company.enrich(domain="stripe.com").locations == []


class TestUserAgent:
    """Requests identify the SDK so the API can tell its traffic apart."""

    def test_builtin_client_sends_user_agent(self):
        from datalegion._client import USER_AGENT

        assert USER_AGENT.startswith("datalegion-python/")
        assert DataLegion(api_key="legion_test")._client.headers["User-Agent"] == USER_AGENT

    def test_caller_supplied_client_request_carries_user_agent(self):
        from datalegion._client import USER_AGENT

        seen: list[str] = []

        def handler(request: httpx.Request) -> httpx.Response:
            seen.append(request.headers.get("User-Agent", ""))
            return httpx.Response(200, json={"results": []})

        http = httpx.Client(transport=httpx.MockTransport(handler), base_url="https://x.test")
        c = DataLegion(api_key="legion_test", base_url="https://x.test", httpx_client=http)
        c.person.dynamic_bulk_enrich(
            [{"social_url": "https://www.linkedin.com/in/x", "fields": ["phones"]}]
        )
        assert seen == [USER_AGENT]

    async def test_async_client_sends_user_agent(self):
        from datalegion._client import USER_AGENT

        seen: list[str] = []

        def handler(request: httpx.Request) -> httpx.Response:
            seen.append(request.headers.get("User-Agent", ""))
            return httpx.Response(200, json={"results": []})

        http = httpx.AsyncClient(transport=httpx.MockTransport(handler), base_url="https://x.test")
        c = AsyncDataLegion(api_key="legion_test", base_url="https://x.test", httpx_client=http)
        await c.person.dynamic_bulk_enrich(
            [{"social_url": "https://www.linkedin.com/in/x", "fields": ["phones"]}]
        )
        assert seen == [USER_AGENT]
        assert AsyncDataLegion(api_key="legion_test")._client.headers["User-Agent"] == USER_AGENT


class TestSandbox:
    """sandbox=True sends the endpoints the API mirrors to /sandbox/ and nothing else."""

    def _record(self, seen):
        def handler(request):
            seen.append(request.url.path)
            if request.url.path.endswith("/enrich"):
                return httpx.Response(
                    200, json={"matches": [{"person": {"legion_id": "x"}}], "total": 1}
                )
            return httpx.Response(200, json={"results": {}})

        return handler

    def test_sandbox_routes_only_mirrored_paths(self):
        seen: list[str] = []
        c = DataLegion(
            api_key="legion_test",
            sandbox=True,
            httpx_client=httpx.Client(transport=httpx.MockTransport(self._record(seen))),
        )
        c.person.enrich(email="jane@example.org")
        c.utility.clean(fields={"email": "a@b.co"})
        assert seen == ["/sandbox/person/enrich", "/utility/clean"]

    def test_default_is_the_real_api(self):
        seen: list[str] = []
        c = DataLegion(
            api_key="legion_test",
            httpx_client=httpx.Client(transport=httpx.MockTransport(self._record(seen))),
        )
        c.person.enrich(email="jane@example.org")
        assert seen == ["/person/enrich"]

    @pytest.mark.asyncio
    async def test_async_client_routes_the_same(self):
        seen: list[str] = []
        c = AsyncDataLegion(
            api_key="legion_test",
            sandbox=True,
            httpx_client=httpx.AsyncClient(transport=httpx.MockTransport(self._record(seen))),
        )
        await c.person.enrich(email="jane@example.org")
        assert seen == ["/sandbox/person/enrich"]

    def test_sandbox_paths_cover_every_mirrored_endpoint(self):
        from datalegion._client import SANDBOX_PATHS

        assert sorted(SANDBOX_PATHS) == sorted(
            f"/{e}/{op}"
            for e in ("person", "company")
            for op in ("enrich", "enrich/bulk", "search", "discover")
        )

    @requires_api_key
    def test_live_sandbox_returns_sample_records(self):
        with DataLegion(api_key=API_KEY, sandbox=True) as c:
            person = c.person.enrich(email="anyone@example.org")
            company = c.company.enrich(domain="example.org")
        assert person.legion_id.startswith("sandbox_")
        assert company.legion_id.startswith("sandbox_")
