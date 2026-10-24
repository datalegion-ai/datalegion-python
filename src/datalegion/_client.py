"""Sync and async HTTP clients for the Data Legion API."""

from __future__ import annotations

import os
from importlib.metadata import PackageNotFoundError, version
from typing import Any, Literal, overload

import httpx

from ._exceptions import (
    APIError,
    AuthenticationError,
    BadRequestError,
    DataLegionError,
    InsufficientCreditsError,
    NotFoundError,
    PermissionDeniedError,
    RateLimitError,
    RequestTimeoutError,
    ServerError,
    ValidationError,
)
from ._types import (
    BulkCompanyEnrichResponse,
    BulkPersonEnrichResponse,
    CompanyMatchesResponse,
    CompanyResponse,
    DataIssueReportResponse,
    DynamicBulkPersonEnrichResponse,
    EmailHashResponse,
    FieldCleanResponse,
    HealthResponse,
    PersonMatchesResponse,
    PersonResponse,
    ValidationResponse,
)

try:
    _SDK_VERSION = version("datalegion")
except PackageNotFoundError:  # running from a source tree without an install
    _SDK_VERSION = "unknown"

# Identifies SDK traffic to the API (its request log classifies
# datalegion-python/* as the Python SDK, not generic python-httpx).
USER_AGENT = f"datalegion-python/{_SDK_VERSION}"

DEFAULT_BASE_URL = "https://api.datalegion.ai"
DEFAULT_TIMEOUT = 60.0

# Endpoints the API mirrors under /sandbox/: sample records (Jane Sandbox, Sandbox Corp), no credits.
# Everything else (utilities, reports, health, dynamic bulk) has no sandbox; utilities are free anyway.
SANDBOX_PATHS = frozenset(
    f"/{entity}/{op}"
    for entity in ("person", "company")
    for op in ("enrich", "enrich/bulk", "search", "discover")
)


def _route(path: str, sandbox: bool) -> str:
    """The path to call: its sandbox mirror when the client is in sandbox mode and one exists."""
    return f"/sandbox{path}" if sandbox and path in SANDBOX_PATHS else path


_STATUS_CODE_TO_EXCEPTION: dict[int, type[DataLegionError]] = {
    400: BadRequestError,
    401: AuthenticationError,
    402: InsufficientCreditsError,
    403: PermissionDeniedError,
    404: NotFoundError,
    408: RequestTimeoutError,
    422: ValidationError,
    429: RateLimitError,
}


def _build_exception(response: httpx.Response) -> DataLegionError:
    """Build the appropriate exception from an error response."""
    status_code = response.status_code

    try:
        body = response.json()
        error = body.get("error", "")
        message = body.get("message", response.text)
        details = body.get("details")
    except Exception:
        error = ""
        message = response.text
        details = None

    exc_cls = _STATUS_CODE_TO_EXCEPTION.get(
        status_code, ServerError if status_code >= 500 else APIError
    )
    return exc_cls(
        message,
        status_code=status_code,
        error=error,
        details=details,
    )


def _strip_none(d: dict[str, Any]) -> dict[str, Any]:
    """Remove keys with None values from a dict."""
    return {k: v for k, v in d.items() if v is not None}


def _first_match(data: dict[str, Any], subject: str) -> dict[str, Any]:
    """Return the first match's ``subject`` record from a single-enrich response.

    Defensive: the API returns 404 (raised as an exception before this point)
    when nothing matches, so a 200 always carries at least one match. If that
    invariant is ever broken, raise a clean 404 instead of an opaque IndexError.
    """
    matches = data.get("matches") or []
    if not matches:
        raise NotFoundError(
            f"No {subject} found matching the provided parameters.",
            status_code=404,
            error="not_found",
        )
    return matches[0][subject]


def _safe_int(value: str | None) -> int | None:
    """Parse an int-valued header, returning None for missing or non-numeric
    values (e.g. ``"unlimited"`` on unlimited contracts)."""
    if value is None:
        return None
    try:
        return int(value)
    except ValueError:
        return None


# ---------------------------------------------------------------------------
# Resource namespaces
# ---------------------------------------------------------------------------


class _PersonResource:
    """Access person endpoints: enrich, search, discover."""

    def __init__(self, client: DataLegion) -> None:
        self._client = client

    @overload
    def enrich(
        self,
        *,
        email: str | None = ...,
        email_hash: str | None = ...,
        phone: str | None = ...,
        linkedin_id: str | None = ...,
        social_url: str | None = ...,
        legion_id: str | None = ...,
        full_name: str | None = ...,
        first_name: str | None = ...,
        last_name: str | None = ...,
        address: str | None = ...,
        city: str | None = ...,
        state: str | None = ...,
        country: str | None = ...,
        postal_code: str | None = ...,
        job_title: str | None = ...,
        company: str | None = ...,
        school: str | None = ...,
        birth_date: str | None = ...,
        multiple_results: Literal[True],
        limit: int | None = ...,
        min_confidence: str | None = ...,
        titlecase: bool | None = ...,
        required_fields: str | None = ...,
        include_fields: str | None = ...,
        exclude_fields: str | None = ...,
        pretty_print: bool | None = ...,
    ) -> PersonMatchesResponse: ...

    @overload
    def enrich(
        self,
        *,
        email: str | None = ...,
        email_hash: str | None = ...,
        phone: str | None = ...,
        linkedin_id: str | None = ...,
        social_url: str | None = ...,
        legion_id: str | None = ...,
        full_name: str | None = ...,
        first_name: str | None = ...,
        last_name: str | None = ...,
        address: str | None = ...,
        city: str | None = ...,
        state: str | None = ...,
        country: str | None = ...,
        postal_code: str | None = ...,
        job_title: str | None = ...,
        company: str | None = ...,
        school: str | None = ...,
        birth_date: str | None = ...,
        multiple_results: Literal[False] | None = ...,
        limit: int | None = ...,
        min_confidence: str | None = ...,
        titlecase: bool | None = ...,
        required_fields: str | None = ...,
        include_fields: str | None = ...,
        exclude_fields: str | None = ...,
        pretty_print: bool | None = ...,
    ) -> PersonResponse: ...

    def enrich(
        self,
        *,
        email: str | None = None,
        email_hash: str | None = None,
        phone: str | None = None,
        linkedin_id: str | None = None,
        social_url: str | None = None,
        legion_id: str | None = None,
        full_name: str | None = None,
        first_name: str | None = None,
        last_name: str | None = None,
        address: str | None = None,
        city: str | None = None,
        state: str | None = None,
        country: str | None = None,
        postal_code: str | None = None,
        job_title: str | None = None,
        company: str | None = None,
        school: str | None = None,
        birth_date: str | None = None,
        multiple_results: bool | None = None,
        limit: int | None = None,
        min_confidence: str | None = None,
        titlecase: bool | None = None,
        required_fields: str | None = None,
        include_fields: str | None = None,
        exclude_fields: str | None = None,
        pretty_print: bool | None = None,
    ) -> PersonResponse | PersonMatchesResponse:
        """Enrich a person by email, phone, social URL, name, etc.

        Returns a :class:`PersonResponse` by default, or a
        :class:`PersonMatchesResponse` when ``multiple_results=True``.

        ``required_fields`` drops matches missing those fields. Use response field
        names (``"work_email,phones"``), a list subfield (``"emails.type"``), or a
        subfield value (``"emails.type:personal"``, ``"phones.type:mobile"``).
        Unknown field names or out-of-range enum values raise a 400.
        """
        body = _strip_none(
            {
                "email": email,
                "email_hash": email_hash,
                "phone": phone,
                "linkedin_id": linkedin_id,
                "social_url": social_url,
                "legion_id": legion_id,
                "full_name": full_name,
                "first_name": first_name,
                "last_name": last_name,
                "address": address,
                "city": city,
                "state": state,
                "country": country,
                "postal_code": postal_code,
                "job_title": job_title,
                "company": company,
                "school": school,
                "birth_date": birth_date,
                "multiple_results": multiple_results,
                "limit": limit,
                "min_confidence": min_confidence,
                "titlecase": titlecase,
                "required_fields": required_fields,
                "include_fields": include_fields,
                "exclude_fields": exclude_fields,
                "pretty_print": pretty_print,
            }
        )
        data = self._client._post("/person/enrich", body)
        if multiple_results:
            return PersonMatchesResponse.model_validate(data)
        return PersonResponse.model_validate(_first_match(data, "person"))

    def bulk_enrich(
        self,
        items: list[dict[str, Any]],
        *,
        multiple_results: bool | None = None,
        limit: int | None = None,
        min_confidence: str | None = None,
        titlecase: bool | None = None,
        required_fields: str | None = None,
        include_fields: str | None = None,
        exclude_fields: str | None = None,
        pretty_print: bool | None = None,
    ) -> BulkPersonEnrichResponse:
        """Enrich multiple people in a single request.

        Each item in *items* is a dict of identifier fields (same as
        ``enrich()`` keyword arguments) plus an optional ``metadata`` dict
        that is echoed back in the response.

        Top-level keyword arguments act as defaults; per-item values
        override them.
        """
        body = _strip_none(
            {
                "items": items,
                "multiple_results": multiple_results,
                "limit": limit,
                "min_confidence": min_confidence,
                "titlecase": titlecase,
                "required_fields": required_fields,
                "include_fields": include_fields,
                "exclude_fields": exclude_fields,
                "pretty_print": pretty_print,
            }
        )
        return BulkPersonEnrichResponse.model_validate(
            self._client._post("/person/enrich/bulk", body)
        )

    def dynamic_bulk_enrich(self, items: list[dict[str, Any]]) -> DynamicBulkPersonEnrichResponse:
        """Bulk-enrich people by LinkedIn URL, returning only phones/emails.

        A focused, high-throughput contact-enrichment endpoint. Each item is a
        dict ``{"social_url": <linkedin url>, "fields": [...], "metadata": {...}}``
        where ``fields`` accepts ONLY the contact groups ``"phones"`` and/or
        ``"emails"`` (e.g. ``["phones"]``, ``["emails"]``, or
        ``["phones", "emails"]``); ``metadata`` is optional and echoed back. Up to
        50 items per request. Each item is billed to the credit pool entitling its
        requested group(s).
        """
        return DynamicBulkPersonEnrichResponse.model_validate(
            self._client._post("/dynamic/person/enrich/bulk", {"items": items})
        )

    def search(
        self,
        *,
        query: str,
        limit: int,
        offset: int | None = None,
        titlecase: bool | None = None,
        include_fields: str | None = None,
        exclude_fields: str | None = None,
        pretty_print: bool | None = None,
    ) -> PersonMatchesResponse:
        """Search for people using a SQL query."""
        body = _strip_none(
            {
                "query": query,
                "limit": limit,
                "offset": offset,
                "titlecase": titlecase,
                "include_fields": include_fields,
                "exclude_fields": exclude_fields,
                "pretty_print": pretty_print,
            }
        )
        return PersonMatchesResponse.model_validate(self._client._post("/person/search", body))

    def discover(
        self,
        *,
        query: str,
        limit: int,
        offset: int | None = None,
        titlecase: bool | None = None,
        include_fields: str | None = None,
        exclude_fields: str | None = None,
        pretty_print: bool | None = None,
    ) -> PersonMatchesResponse:
        """Discover people using a natural language query."""
        body = _strip_none(
            {
                "query": query,
                "limit": limit,
                "offset": offset,
                "titlecase": titlecase,
                "include_fields": include_fields,
                "exclude_fields": exclude_fields,
                "pretty_print": pretty_print,
            }
        )
        data = self._client._post("/person/discover", body)
        self._client._update_generated_query(data)
        return PersonMatchesResponse.model_validate(data)


class _CompanyResource:
    """Access company endpoints: enrich, search, discover."""

    def __init__(self, client: DataLegion) -> None:
        self._client = client

    @overload
    def enrich(
        self,
        *,
        legion_id: str | None = ...,
        domain: str | None = ...,
        name: str | None = ...,
        linkedin_id: str | None = ...,
        social_url: str | None = ...,
        ticker_symbol: str | None = ...,
        industry: str | None = ...,
        multiple_results: Literal[True],
        limit: int | None = ...,
        min_confidence: str | None = ...,
        titlecase: bool | None = ...,
        required_fields: str | None = ...,
        include_fields: str | None = ...,
        exclude_fields: str | None = ...,
        pretty_print: bool | None = ...,
    ) -> CompanyMatchesResponse: ...

    @overload
    def enrich(
        self,
        *,
        legion_id: str | None = ...,
        domain: str | None = ...,
        name: str | None = ...,
        linkedin_id: str | None = ...,
        social_url: str | None = ...,
        ticker_symbol: str | None = ...,
        industry: str | None = ...,
        multiple_results: Literal[False] | None = ...,
        limit: int | None = ...,
        min_confidence: str | None = ...,
        titlecase: bool | None = ...,
        required_fields: str | None = ...,
        include_fields: str | None = ...,
        exclude_fields: str | None = ...,
        pretty_print: bool | None = ...,
    ) -> CompanyResponse: ...

    def enrich(
        self,
        *,
        legion_id: str | None = None,
        domain: str | None = None,
        name: str | None = None,
        linkedin_id: str | None = None,
        social_url: str | None = None,
        ticker_symbol: str | None = None,
        industry: str | None = None,
        multiple_results: bool | None = None,
        limit: int | None = None,
        min_confidence: str | None = None,
        titlecase: bool | None = None,
        required_fields: str | None = None,
        include_fields: str | None = None,
        exclude_fields: str | None = None,
        pretty_print: bool | None = None,
    ) -> CompanyResponse | CompanyMatchesResponse:
        """Enrich a company by domain, name, LinkedIn ID, etc.

        Returns a :class:`CompanyResponse` by default, or a
        :class:`CompanyMatchesResponse` when ``multiple_results=True``.

        ``required_fields`` drops matches missing those fields. Use response field
        names (``"domain,socials"``), a list subfield (``"socials.network"``), or a
        subfield value (``"type:public"``, ``"socials.network:linkedin"``).
        Unknown field names or out-of-range enum values raise a 400.
        """
        body = _strip_none(
            {
                "legion_id": legion_id,
                "domain": domain,
                "name": name,
                "linkedin_id": linkedin_id,
                "social_url": social_url,
                "ticker_symbol": ticker_symbol,
                "industry": industry,
                "multiple_results": multiple_results,
                "limit": limit,
                "min_confidence": min_confidence,
                "titlecase": titlecase,
                "required_fields": required_fields,
                "include_fields": include_fields,
                "exclude_fields": exclude_fields,
                "pretty_print": pretty_print,
            }
        )
        data = self._client._post("/company/enrich", body)
        if multiple_results:
            return CompanyMatchesResponse.model_validate(data)
        return CompanyResponse.model_validate(_first_match(data, "company"))

    def bulk_enrich(
        self,
        items: list[dict[str, Any]],
        *,
        multiple_results: bool | None = None,
        limit: int | None = None,
        min_confidence: str | None = None,
        titlecase: bool | None = None,
        required_fields: str | None = None,
        include_fields: str | None = None,
        exclude_fields: str | None = None,
        pretty_print: bool | None = None,
    ) -> BulkCompanyEnrichResponse:
        """Enrich multiple companies in a single request.

        Each item in *items* is a dict of identifier fields (same as
        ``enrich()`` keyword arguments) plus an optional ``metadata`` dict
        that is echoed back in the response.

        Top-level keyword arguments act as defaults; per-item values
        override them.
        """
        body = _strip_none(
            {
                "items": items,
                "multiple_results": multiple_results,
                "limit": limit,
                "min_confidence": min_confidence,
                "titlecase": titlecase,
                "required_fields": required_fields,
                "include_fields": include_fields,
                "exclude_fields": exclude_fields,
                "pretty_print": pretty_print,
            }
        )
        return BulkCompanyEnrichResponse.model_validate(
            self._client._post("/company/enrich/bulk", body)
        )

    def search(
        self,
        *,
        query: str,
        limit: int,
        offset: int | None = None,
        titlecase: bool | None = None,
        include_fields: str | None = None,
        exclude_fields: str | None = None,
        pretty_print: bool | None = None,
    ) -> CompanyMatchesResponse:
        """Search for companies using a SQL query."""
        body = _strip_none(
            {
                "query": query,
                "limit": limit,
                "offset": offset,
                "titlecase": titlecase,
                "include_fields": include_fields,
                "exclude_fields": exclude_fields,
                "pretty_print": pretty_print,
            }
        )
        return CompanyMatchesResponse.model_validate(self._client._post("/company/search", body))

    def discover(
        self,
        *,
        query: str,
        limit: int,
        offset: int | None = None,
        titlecase: bool | None = None,
        include_fields: str | None = None,
        exclude_fields: str | None = None,
        pretty_print: bool | None = None,
    ) -> CompanyMatchesResponse:
        """Discover companies using a natural language query."""
        body = _strip_none(
            {
                "query": query,
                "limit": limit,
                "offset": offset,
                "titlecase": titlecase,
                "include_fields": include_fields,
                "exclude_fields": exclude_fields,
                "pretty_print": pretty_print,
            }
        )
        data = self._client._post("/company/discover", body)
        self._client._update_generated_query(data)
        return CompanyMatchesResponse.model_validate(data)


class _UtilityResource:
    """Access utility endpoints: clean, hash_email, validate, report."""

    def __init__(self, client: DataLegion) -> None:
        self._client = client

    def clean(
        self,
        *,
        fields: dict[str, str],
        default_region: str | None = None,
    ) -> FieldCleanResponse:
        """Clean and normalize fields."""
        body: dict[str, Any] = {"fields": fields}
        if default_region is not None:
            body["default_region"] = default_region
        return FieldCleanResponse.model_validate(self._client._post("/utility/clean", body))

    def hash_email(self, *, email: str) -> EmailHashResponse:
        """Hash an email address (SHA-256, SHA-1, MD5)."""
        return EmailHashResponse.model_validate(
            self._client._post("/utility/hash/email", {"email": email})
        )

    def validate(
        self,
        *,
        email: str | None = None,
        phone: str | None = None,
        first_name: str | None = None,
        last_name: str | None = None,
        full_name: str | None = None,
        social_url: str | None = None,
        address: str | None = None,
        state: str | None = None,
        country: str | None = None,
        company: str | None = None,
        school: str | None = None,
        birth_date: str | None = None,
        domain: str | None = None,
        ticker_symbol: str | None = None,
        linkedin_company_url: str | None = None,
    ) -> ValidationResponse:
        """Validate input data fields."""
        body = _strip_none(
            {
                "email": email,
                "phone": phone,
                "first_name": first_name,
                "last_name": last_name,
                "full_name": full_name,
                "social_url": social_url,
                "address": address,
                "state": state,
                "country": country,
                "company": company,
                "school": school,
                "birth_date": birth_date,
                "domain": domain,
                "ticker_symbol": ticker_symbol,
                "linkedin_company_url": linkedin_company_url,
            }
        )
        return ValidationResponse.model_validate(self._client._post("/utility/validate", body))

    def report_person(
        self,
        *,
        legion_id: str,
        issue_type: str,
        issue_level: str,
        field: str | None = None,
        observed_value: str | None = None,
        correct_value: str | None = None,
        comment: str | None = None,
    ) -> DataIssueReportResponse:
        """Report a data-quality issue with a person record.

        ``issue_type``: incorrect, outdated, misattributed, frankenstein,
        not_a_real_person, or duplicate. ``issue_level``: record, group, or
        field (``field`` names the group or field for the latter two).
        Include at least one of ``correct_value`` or ``comment``.
        """
        body = _strip_none(
            {
                "legion_id": legion_id,
                "issue_type": issue_type,
                "issue_level": issue_level,
                "field": field,
                "observed_value": observed_value,
                "correct_value": correct_value,
                "comment": comment,
            }
        )
        return DataIssueReportResponse.model_validate(
            self._client._post("/utility/report/person", body)
        )

    def report_company(
        self,
        *,
        legion_id: str,
        issue_type: str,
        issue_level: str,
        field: str | None = None,
        observed_value: str | None = None,
        correct_value: str | None = None,
        comment: str | None = None,
    ) -> DataIssueReportResponse:
        """Report a data-quality issue with a company record.

        Same rules as :meth:`report_person`; ``not_a_real_person`` is not
        valid for company reports.
        """
        body = _strip_none(
            {
                "legion_id": legion_id,
                "issue_type": issue_type,
                "issue_level": issue_level,
                "field": field,
                "observed_value": observed_value,
                "correct_value": correct_value,
                "comment": comment,
            }
        )
        return DataIssueReportResponse.model_validate(
            self._client._post("/utility/report/company", body)
        )


# ---------------------------------------------------------------------------
# Async resource namespaces
# ---------------------------------------------------------------------------


class _AsyncPersonResource:
    """Access person endpoints (async): enrich, search, discover."""

    def __init__(self, client: AsyncDataLegion) -> None:
        self._client = client

    @overload
    async def enrich(
        self,
        *,
        email: str | None = ...,
        email_hash: str | None = ...,
        phone: str | None = ...,
        linkedin_id: str | None = ...,
        social_url: str | None = ...,
        legion_id: str | None = ...,
        full_name: str | None = ...,
        first_name: str | None = ...,
        last_name: str | None = ...,
        address: str | None = ...,
        city: str | None = ...,
        state: str | None = ...,
        country: str | None = ...,
        postal_code: str | None = ...,
        job_title: str | None = ...,
        company: str | None = ...,
        school: str | None = ...,
        birth_date: str | None = ...,
        multiple_results: Literal[True],
        limit: int | None = ...,
        min_confidence: str | None = ...,
        titlecase: bool | None = ...,
        required_fields: str | None = ...,
        include_fields: str | None = ...,
        exclude_fields: str | None = ...,
        pretty_print: bool | None = ...,
    ) -> PersonMatchesResponse: ...

    @overload
    async def enrich(
        self,
        *,
        email: str | None = ...,
        email_hash: str | None = ...,
        phone: str | None = ...,
        linkedin_id: str | None = ...,
        social_url: str | None = ...,
        legion_id: str | None = ...,
        full_name: str | None = ...,
        first_name: str | None = ...,
        last_name: str | None = ...,
        address: str | None = ...,
        city: str | None = ...,
        state: str | None = ...,
        country: str | None = ...,
        postal_code: str | None = ...,
        job_title: str | None = ...,
        company: str | None = ...,
        school: str | None = ...,
        birth_date: str | None = ...,
        multiple_results: Literal[False] | None = ...,
        limit: int | None = ...,
        min_confidence: str | None = ...,
        titlecase: bool | None = ...,
        required_fields: str | None = ...,
        include_fields: str | None = ...,
        exclude_fields: str | None = ...,
        pretty_print: bool | None = ...,
    ) -> PersonResponse: ...

    async def enrich(
        self,
        *,
        email: str | None = None,
        email_hash: str | None = None,
        phone: str | None = None,
        linkedin_id: str | None = None,
        social_url: str | None = None,
        legion_id: str | None = None,
        full_name: str | None = None,
        first_name: str | None = None,
        last_name: str | None = None,
        address: str | None = None,
        city: str | None = None,
        state: str | None = None,
        country: str | None = None,
        postal_code: str | None = None,
        job_title: str | None = None,
        company: str | None = None,
        school: str | None = None,
        birth_date: str | None = None,
        multiple_results: bool | None = None,
        limit: int | None = None,
        min_confidence: str | None = None,
        titlecase: bool | None = None,
        required_fields: str | None = None,
        include_fields: str | None = None,
        exclude_fields: str | None = None,
        pretty_print: bool | None = None,
    ) -> PersonResponse | PersonMatchesResponse:
        """Enrich a person by email, phone, social URL, name, etc.

        Returns a :class:`PersonResponse` by default, or a
        :class:`PersonMatchesResponse` when ``multiple_results=True``.

        ``required_fields`` drops matches missing those fields. Use response field
        names (``"work_email,phones"``), a list subfield (``"emails.type"``), or a
        subfield value (``"emails.type:personal"``, ``"phones.type:mobile"``).
        Unknown field names or out-of-range enum values raise a 400.
        """
        body = _strip_none(
            {
                "email": email,
                "email_hash": email_hash,
                "phone": phone,
                "linkedin_id": linkedin_id,
                "social_url": social_url,
                "legion_id": legion_id,
                "full_name": full_name,
                "first_name": first_name,
                "last_name": last_name,
                "address": address,
                "city": city,
                "state": state,
                "country": country,
                "postal_code": postal_code,
                "job_title": job_title,
                "company": company,
                "school": school,
                "birth_date": birth_date,
                "multiple_results": multiple_results,
                "limit": limit,
                "min_confidence": min_confidence,
                "titlecase": titlecase,
                "required_fields": required_fields,
                "include_fields": include_fields,
                "exclude_fields": exclude_fields,
                "pretty_print": pretty_print,
            }
        )
        data = await self._client._post("/person/enrich", body)
        if multiple_results:
            return PersonMatchesResponse.model_validate(data)
        return PersonResponse.model_validate(_first_match(data, "person"))

    async def bulk_enrich(
        self,
        items: list[dict[str, Any]],
        *,
        multiple_results: bool | None = None,
        limit: int | None = None,
        min_confidence: str | None = None,
        titlecase: bool | None = None,
        required_fields: str | None = None,
        include_fields: str | None = None,
        exclude_fields: str | None = None,
        pretty_print: bool | None = None,
    ) -> BulkPersonEnrichResponse:
        """Enrich multiple people in a single request.

        Each item in *items* is a dict of identifier fields (same as
        ``enrich()`` keyword arguments) plus an optional ``metadata`` dict
        that is echoed back in the response.

        Top-level keyword arguments act as defaults; per-item values
        override them.
        """
        body = _strip_none(
            {
                "items": items,
                "multiple_results": multiple_results,
                "limit": limit,
                "min_confidence": min_confidence,
                "titlecase": titlecase,
                "required_fields": required_fields,
                "include_fields": include_fields,
                "exclude_fields": exclude_fields,
                "pretty_print": pretty_print,
            }
        )
        return BulkPersonEnrichResponse.model_validate(
            await self._client._post("/person/enrich/bulk", body)
        )

    async def dynamic_bulk_enrich(
        self, items: list[dict[str, Any]]
    ) -> DynamicBulkPersonEnrichResponse:
        """Bulk-enrich people by LinkedIn URL, returning only phones/emails.

        A focused, high-throughput contact-enrichment endpoint. Each item is a
        dict ``{"social_url": <linkedin url>, "fields": [...], "metadata": {...}}``
        where ``fields`` accepts ONLY the contact groups ``"phones"`` and/or
        ``"emails"`` (e.g. ``["phones"]``, ``["emails"]``, or
        ``["phones", "emails"]``); ``metadata`` is optional and echoed back. Up to
        50 items per request. Each item is billed to the credit pool entitling its
        requested group(s).
        """
        return DynamicBulkPersonEnrichResponse.model_validate(
            await self._client._post("/dynamic/person/enrich/bulk", {"items": items})
        )

    async def search(
        self,
        *,
        query: str,
        limit: int,
        offset: int | None = None,
        titlecase: bool | None = None,
        include_fields: str | None = None,
        exclude_fields: str | None = None,
        pretty_print: bool | None = None,
    ) -> PersonMatchesResponse:
        """Search for people using a SQL query."""
        body = _strip_none(
            {
                "query": query,
                "limit": limit,
                "offset": offset,
                "titlecase": titlecase,
                "include_fields": include_fields,
                "exclude_fields": exclude_fields,
                "pretty_print": pretty_print,
            }
        )
        return PersonMatchesResponse.model_validate(
            await self._client._post("/person/search", body)
        )

    async def discover(
        self,
        *,
        query: str,
        limit: int,
        offset: int | None = None,
        titlecase: bool | None = None,
        include_fields: str | None = None,
        exclude_fields: str | None = None,
        pretty_print: bool | None = None,
    ) -> PersonMatchesResponse:
        """Discover people using a natural language query."""
        body = _strip_none(
            {
                "query": query,
                "limit": limit,
                "offset": offset,
                "titlecase": titlecase,
                "include_fields": include_fields,
                "exclude_fields": exclude_fields,
                "pretty_print": pretty_print,
            }
        )
        data = await self._client._post("/person/discover", body)
        self._client._update_generated_query(data)
        return PersonMatchesResponse.model_validate(data)


class _AsyncCompanyResource:
    """Access company endpoints (async): enrich, search, discover."""

    def __init__(self, client: AsyncDataLegion) -> None:
        self._client = client

    @overload
    async def enrich(
        self,
        *,
        legion_id: str | None = ...,
        domain: str | None = ...,
        name: str | None = ...,
        linkedin_id: str | None = ...,
        social_url: str | None = ...,
        ticker_symbol: str | None = ...,
        industry: str | None = ...,
        multiple_results: Literal[True],
        limit: int | None = ...,
        min_confidence: str | None = ...,
        titlecase: bool | None = ...,
        required_fields: str | None = ...,
        include_fields: str | None = ...,
        exclude_fields: str | None = ...,
        pretty_print: bool | None = ...,
    ) -> CompanyMatchesResponse: ...

    @overload
    async def enrich(
        self,
        *,
        legion_id: str | None = ...,
        domain: str | None = ...,
        name: str | None = ...,
        linkedin_id: str | None = ...,
        social_url: str | None = ...,
        ticker_symbol: str | None = ...,
        industry: str | None = ...,
        multiple_results: Literal[False] | None = ...,
        limit: int | None = ...,
        min_confidence: str | None = ...,
        titlecase: bool | None = ...,
        required_fields: str | None = ...,
        include_fields: str | None = ...,
        exclude_fields: str | None = ...,
        pretty_print: bool | None = ...,
    ) -> CompanyResponse: ...

    async def enrich(
        self,
        *,
        legion_id: str | None = None,
        domain: str | None = None,
        name: str | None = None,
        linkedin_id: str | None = None,
        social_url: str | None = None,
        ticker_symbol: str | None = None,
        industry: str | None = None,
        multiple_results: bool | None = None,
        limit: int | None = None,
        min_confidence: str | None = None,
        titlecase: bool | None = None,
        required_fields: str | None = None,
        include_fields: str | None = None,
        exclude_fields: str | None = None,
        pretty_print: bool | None = None,
    ) -> CompanyResponse | CompanyMatchesResponse:
        """Enrich a company by domain, name, LinkedIn ID, etc.

        Returns a :class:`CompanyResponse` by default, or a
        :class:`CompanyMatchesResponse` when ``multiple_results=True``.

        ``required_fields`` drops matches missing those fields. Use response field
        names (``"domain,socials"``), a list subfield (``"socials.network"``), or a
        subfield value (``"type:public"``, ``"socials.network:linkedin"``).
        Unknown field names or out-of-range enum values raise a 400.
        """
        body = _strip_none(
            {
                "legion_id": legion_id,
                "domain": domain,
                "name": name,
                "linkedin_id": linkedin_id,
                "social_url": social_url,
                "ticker_symbol": ticker_symbol,
                "industry": industry,
                "multiple_results": multiple_results,
                "limit": limit,
                "min_confidence": min_confidence,
                "titlecase": titlecase,
                "required_fields": required_fields,
                "include_fields": include_fields,
                "exclude_fields": exclude_fields,
                "pretty_print": pretty_print,
            }
        )
        data = await self._client._post("/company/enrich", body)
        if multiple_results:
            return CompanyMatchesResponse.model_validate(data)
        return CompanyResponse.model_validate(_first_match(data, "company"))

    async def bulk_enrich(
        self,
        items: list[dict[str, Any]],
        *,
        multiple_results: bool | None = None,
        limit: int | None = None,
        min_confidence: str | None = None,
        titlecase: bool | None = None,
        required_fields: str | None = None,
        include_fields: str | None = None,
        exclude_fields: str | None = None,
        pretty_print: bool | None = None,
    ) -> BulkCompanyEnrichResponse:
        """Enrich multiple companies in a single request.

        Each item in *items* is a dict of identifier fields (same as
        ``enrich()`` keyword arguments) plus an optional ``metadata`` dict
        that is echoed back in the response.

        Top-level keyword arguments act as defaults; per-item values
        override them.
        """
        body = _strip_none(
            {
                "items": items,
                "multiple_results": multiple_results,
                "limit": limit,
                "min_confidence": min_confidence,
                "titlecase": titlecase,
                "required_fields": required_fields,
                "include_fields": include_fields,
                "exclude_fields": exclude_fields,
                "pretty_print": pretty_print,
            }
        )
        return BulkCompanyEnrichResponse.model_validate(
            await self._client._post("/company/enrich/bulk", body)
        )

    async def search(
        self,
        *,
        query: str,
        limit: int,
        offset: int | None = None,
        titlecase: bool | None = None,
        include_fields: str | None = None,
        exclude_fields: str | None = None,
        pretty_print: bool | None = None,
    ) -> CompanyMatchesResponse:
        """Search for companies using a SQL query."""
        body = _strip_none(
            {
                "query": query,
                "limit": limit,
                "offset": offset,
                "titlecase": titlecase,
                "include_fields": include_fields,
                "exclude_fields": exclude_fields,
                "pretty_print": pretty_print,
            }
        )
        return CompanyMatchesResponse.model_validate(
            await self._client._post("/company/search", body)
        )

    async def discover(
        self,
        *,
        query: str,
        limit: int,
        offset: int | None = None,
        titlecase: bool | None = None,
        include_fields: str | None = None,
        exclude_fields: str | None = None,
        pretty_print: bool | None = None,
    ) -> CompanyMatchesResponse:
        """Discover companies using a natural language query."""
        body = _strip_none(
            {
                "query": query,
                "limit": limit,
                "offset": offset,
                "titlecase": titlecase,
                "include_fields": include_fields,
                "exclude_fields": exclude_fields,
                "pretty_print": pretty_print,
            }
        )
        data = await self._client._post("/company/discover", body)
        self._client._update_generated_query(data)
        return CompanyMatchesResponse.model_validate(data)


class _AsyncUtilityResource:
    """Access utility endpoints (async): clean, hash_email, validate, report."""

    def __init__(self, client: AsyncDataLegion) -> None:
        self._client = client

    async def clean(
        self,
        *,
        fields: dict[str, str],
        default_region: str | None = None,
    ) -> FieldCleanResponse:
        """Clean and normalize fields."""
        body: dict[str, Any] = {"fields": fields}
        if default_region is not None:
            body["default_region"] = default_region
        return FieldCleanResponse.model_validate(await self._client._post("/utility/clean", body))

    async def hash_email(self, *, email: str) -> EmailHashResponse:
        """Hash an email address (SHA-256, SHA-1, MD5)."""
        return EmailHashResponse.model_validate(
            await self._client._post("/utility/hash/email", {"email": email})
        )

    async def validate(
        self,
        *,
        email: str | None = None,
        phone: str | None = None,
        first_name: str | None = None,
        last_name: str | None = None,
        full_name: str | None = None,
        social_url: str | None = None,
        address: str | None = None,
        state: str | None = None,
        country: str | None = None,
        company: str | None = None,
        school: str | None = None,
        birth_date: str | None = None,
        domain: str | None = None,
        ticker_symbol: str | None = None,
        linkedin_company_url: str | None = None,
    ) -> ValidationResponse:
        """Validate input data fields."""
        body = _strip_none(
            {
                "email": email,
                "phone": phone,
                "first_name": first_name,
                "last_name": last_name,
                "full_name": full_name,
                "social_url": social_url,
                "address": address,
                "state": state,
                "country": country,
                "company": company,
                "school": school,
                "birth_date": birth_date,
                "domain": domain,
                "ticker_symbol": ticker_symbol,
                "linkedin_company_url": linkedin_company_url,
            }
        )
        return ValidationResponse.model_validate(
            await self._client._post("/utility/validate", body)
        )

    async def report_person(
        self,
        *,
        legion_id: str,
        issue_type: str,
        issue_level: str,
        field: str | None = None,
        observed_value: str | None = None,
        correct_value: str | None = None,
        comment: str | None = None,
    ) -> DataIssueReportResponse:
        """Report a data-quality issue with a person record.

        ``issue_type``: incorrect, outdated, misattributed, frankenstein,
        not_a_real_person, or duplicate. ``issue_level``: record, group, or
        field (``field`` names the group or field for the latter two).
        Include at least one of ``correct_value`` or ``comment``.
        """
        body = _strip_none(
            {
                "legion_id": legion_id,
                "issue_type": issue_type,
                "issue_level": issue_level,
                "field": field,
                "observed_value": observed_value,
                "correct_value": correct_value,
                "comment": comment,
            }
        )
        return DataIssueReportResponse.model_validate(
            await self._client._post("/utility/report/person", body)
        )

    async def report_company(
        self,
        *,
        legion_id: str,
        issue_type: str,
        issue_level: str,
        field: str | None = None,
        observed_value: str | None = None,
        correct_value: str | None = None,
        comment: str | None = None,
    ) -> DataIssueReportResponse:
        """Report a data-quality issue with a company record.

        Same rules as :meth:`report_person`; ``not_a_real_person`` is not
        valid for company reports.
        """
        body = _strip_none(
            {
                "legion_id": legion_id,
                "issue_type": issue_type,
                "issue_level": issue_level,
                "field": field,
                "observed_value": observed_value,
                "correct_value": correct_value,
                "comment": comment,
            }
        )
        return DataIssueReportResponse.model_validate(
            await self._client._post("/utility/report/company", body)
        )


# ---------------------------------------------------------------------------
# Sync client
# ---------------------------------------------------------------------------


class DataLegion:
    """Synchronous client for the Data Legion API.

    Usage::

        from datalegion import DataLegion

        client = DataLegion(api_key="legion_...")
        person = client.person.enrich(email="john@example.com")
        print(person.full_name)
    """

    person: _PersonResource
    company: _CompanyResource
    utility: _UtilityResource

    def __init__(
        self,
        *,
        api_key: str | None = None,
        base_url: str | None = None,
        timeout: float | None = None,
        sandbox: bool = False,
        httpx_client: httpx.Client | None = None,
    ) -> None:
        # Trimmed: a key read from a file or pasted with a newline is otherwise rejected by httpx.
        self._api_key = (api_key or os.environ.get("DATALEGION_API_KEY", "")).strip()
        if not self._api_key:
            raise AuthenticationError(
                "No API key provided. Pass api_key= or set the DATALEGION_API_KEY environment variable.",
                status_code=401,
                error="missing_api_key",
            )
        self._base_url = (base_url or DEFAULT_BASE_URL).rstrip("/")
        self._timeout = timeout or DEFAULT_TIMEOUT
        # Sandbox mode: enrich, bulk enrich, search and discover return sample records, free.
        self._sandbox = sandbox

        if httpx_client is not None:
            self._client = httpx_client
            self._owns_client = False
        else:
            self._client = httpx.Client(
                base_url=self._base_url,
                timeout=self._timeout,
                headers=self._default_headers(),
            )
            self._owns_client = True

        # Response header values from the most recent request
        self.request_id: str | None = None
        self.credits_used: int | None = None
        self.credits_remaining: int | None = None
        self.contract_id: str | None = None
        self.rate_limit_limit: int | None = None
        self.rate_limit_remaining: int | None = None
        self.rate_limit_reset: int | None = None
        self.rate_limit_policy: str | None = None
        self.retry_after: int | None = None
        self.generated_query: str | None = None
        self.correlation_id: str | None = None
        self.total_count_status: str | None = None
        self.search_warning: str | None = None

        # Resource namespaces
        self.person = _PersonResource(self)
        self.company = _CompanyResource(self)
        self.utility = _UtilityResource(self)

    def _default_headers(self) -> dict[str, str]:
        return {
            "API-Key": self._api_key,
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": USER_AGENT,
        }

    def _update_response_headers(self, response: httpx.Response) -> None:
        self.request_id = response.headers.get("Request-ID")
        self.credits_used = _safe_int(response.headers.get("Credits-Used"))
        self.credits_remaining = _safe_int(response.headers.get("Credits-Remaining"))
        self.contract_id = response.headers.get("Contract-ID")
        self.rate_limit_limit = _safe_int(response.headers.get("RateLimit-Limit"))
        self.rate_limit_remaining = _safe_int(response.headers.get("RateLimit-Remaining"))
        self.rate_limit_reset = _safe_int(response.headers.get("RateLimit-Reset"))
        self.rate_limit_policy = response.headers.get("RateLimit-Policy")
        self.retry_after = _safe_int(response.headers.get("Retry-After"))
        self.correlation_id = response.headers.get("Correlation-ID")
        # search/discover only: "exact" | "estimate" | "page" — how `total` was
        # derived. `estimate` means broad-query planner estimate (magnitude only).
        self.total_count_status = response.headers.get("Total-Count-Status")
        # search/discover only: why a filter was judged empty or slow, or what was
        # searched instead of it. None when the search had nothing to say.
        self.search_warning = response.headers.get("Search-Warning")

    def _update_generated_query(self, data: dict[str, Any]) -> None:
        """Extract generated_query from response body (discover endpoints)."""
        self.generated_query = data.get("generated_query")

    def _post(self, path: str, body: dict[str, Any]) -> dict[str, Any]:
        """Send a POST request and return the parsed JSON response."""
        path = _route(path, self._sandbox)
        if self._owns_client:
            response = self._client.post(path, json=body)
        else:
            response = self._client.post(
                f"{self._base_url}{path}",
                json=body,
                headers=self._default_headers(),
            )
        self._update_response_headers(response)
        if response.status_code >= 400:
            raise _build_exception(response)
        return response.json()

    def _get(self, path: str) -> dict[str, Any]:
        """Send a GET request and return the parsed JSON response."""
        path = _route(path, self._sandbox)
        if self._owns_client:
            response = self._client.get(path)
        else:
            response = self._client.get(
                f"{self._base_url}{path}",
                headers=self._default_headers(),
            )
        self._update_response_headers(response)
        if response.status_code >= 400:
            raise _build_exception(response)
        return response.json()

    def health(self) -> HealthResponse:
        """Check API health status."""
        return HealthResponse.model_validate(self._get("/health"))

    def close(self) -> None:
        """Close the underlying HTTP client."""
        if self._owns_client:
            self._client.close()

    def __enter__(self) -> DataLegion:
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()


# ---------------------------------------------------------------------------
# Async client
# ---------------------------------------------------------------------------


class AsyncDataLegion:
    """Asynchronous client for the Data Legion API.

    Usage::

        from datalegion import AsyncDataLegion

        client = AsyncDataLegion(api_key="legion_...")
        person = await client.person.enrich(email="john@example.com")
        print(person.full_name)
    """

    person: _AsyncPersonResource
    company: _AsyncCompanyResource
    utility: _AsyncUtilityResource

    def __init__(
        self,
        *,
        api_key: str | None = None,
        base_url: str | None = None,
        timeout: float | None = None,
        sandbox: bool = False,
        httpx_client: httpx.AsyncClient | None = None,
    ) -> None:
        # Trimmed: a key read from a file or pasted with a newline is otherwise rejected by httpx.
        self._api_key = (api_key or os.environ.get("DATALEGION_API_KEY", "")).strip()
        if not self._api_key:
            raise AuthenticationError(
                "No API key provided. Pass api_key= or set the DATALEGION_API_KEY environment variable.",
                status_code=401,
                error="missing_api_key",
            )
        self._base_url = (base_url or DEFAULT_BASE_URL).rstrip("/")
        self._timeout = timeout or DEFAULT_TIMEOUT
        # Sandbox mode: enrich, bulk enrich, search and discover return sample records, free.
        self._sandbox = sandbox

        if httpx_client is not None:
            self._client = httpx_client
            self._owns_client = False
        else:
            self._client = httpx.AsyncClient(
                base_url=self._base_url,
                timeout=self._timeout,
                headers=self._default_headers(),
            )
            self._owns_client = True

        # Response header values from the most recent request
        self.request_id: str | None = None
        self.credits_used: int | None = None
        self.credits_remaining: int | None = None
        self.contract_id: str | None = None
        self.rate_limit_limit: int | None = None
        self.rate_limit_remaining: int | None = None
        self.rate_limit_reset: int | None = None
        self.rate_limit_policy: str | None = None
        self.retry_after: int | None = None
        self.generated_query: str | None = None
        self.correlation_id: str | None = None
        self.total_count_status: str | None = None
        self.search_warning: str | None = None

        # Resource namespaces
        self.person = _AsyncPersonResource(self)
        self.company = _AsyncCompanyResource(self)
        self.utility = _AsyncUtilityResource(self)

    def _default_headers(self) -> dict[str, str]:
        return {
            "API-Key": self._api_key,
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": USER_AGENT,
        }

    def _update_response_headers(self, response: httpx.Response) -> None:
        self.request_id = response.headers.get("Request-ID")
        self.credits_used = _safe_int(response.headers.get("Credits-Used"))
        self.credits_remaining = _safe_int(response.headers.get("Credits-Remaining"))
        self.contract_id = response.headers.get("Contract-ID")
        self.rate_limit_limit = _safe_int(response.headers.get("RateLimit-Limit"))
        self.rate_limit_remaining = _safe_int(response.headers.get("RateLimit-Remaining"))
        self.rate_limit_reset = _safe_int(response.headers.get("RateLimit-Reset"))
        self.rate_limit_policy = response.headers.get("RateLimit-Policy")
        self.retry_after = _safe_int(response.headers.get("Retry-After"))
        self.correlation_id = response.headers.get("Correlation-ID")
        # search/discover only: "exact" | "estimate" | "page" — how `total` was
        # derived. `estimate` means broad-query planner estimate (magnitude only).
        self.total_count_status = response.headers.get("Total-Count-Status")
        # search/discover only: why a filter was judged empty or slow, or what was
        # searched instead of it. None when the search had nothing to say.
        self.search_warning = response.headers.get("Search-Warning")

    def _update_generated_query(self, data: dict[str, Any]) -> None:
        """Extract generated_query from response body (discover endpoints)."""
        self.generated_query = data.get("generated_query")

    async def _post(self, path: str, body: dict[str, Any]) -> dict[str, Any]:
        """Send a POST request and return the parsed JSON response."""
        path = _route(path, self._sandbox)
        if self._owns_client:
            response = await self._client.post(path, json=body)
        else:
            response = await self._client.post(
                f"{self._base_url}{path}",
                json=body,
                headers=self._default_headers(),
            )
        self._update_response_headers(response)
        if response.status_code >= 400:
            raise _build_exception(response)
        return response.json()

    async def _get(self, path: str) -> dict[str, Any]:
        """Send a GET request and return the parsed JSON response."""
        path = _route(path, self._sandbox)
        if self._owns_client:
            response = await self._client.get(path)
        else:
            response = await self._client.get(
                f"{self._base_url}{path}",
                headers=self._default_headers(),
            )
        self._update_response_headers(response)
        if response.status_code >= 400:
            raise _build_exception(response)
        return response.json()

    async def health(self) -> HealthResponse:
        """Check API health status."""
        return HealthResponse.model_validate(await self._get("/health"))

    async def close(self) -> None:
        """Close the underlying HTTP client."""
        if self._owns_client:
            await self._client.aclose()

    async def __aenter__(self) -> AsyncDataLegion:
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self.close()
