"""Data Legion Python SDK.

Usage::

    from datalegion import DataLegion

    client = DataLegion(api_key="legion_...")
    person = client.person.enrich(email="john@example.com")
    print(person.full_name)

Async usage::

    from datalegion import AsyncDataLegion

    client = AsyncDataLegion(api_key="legion_...")
    person = await client.person.enrich(email="john@example.com")
    print(person.full_name)
"""

from ._client import AsyncDataLegion, DataLegion
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
    BulkCompanyItemResult,
    BulkPersonEnrichResponse,
    BulkPersonItemResult,
    Certification,
    CleanedName,
    CleanedRaw,
    CompanyDomain,
    CompanyLocation,
    CompanyMatch,
    CompanyMatchesResponse,
    CompanyResponse,
    CompanySocial,
    DataIssueReportResponse,
    DynamicBulkPersonEnrichResponse,
    DynamicBulkPersonResult,
    Education,
    EducationOrganization,
    Email,
    EmailDomainCheck,
    EmailHashResponse,
    EmployeeCountByMonth,
    Experience,
    ExperienceOrganization,
    FieldCleanResponse,
    FieldCleanResult,
    HealthResponse,
    Language,
    Location,
    MatchMetadata,
    PersonMatch,
    PersonMatchesResponse,
    PersonResponse,
    Phone,
    Skill,
    Social,
    Ticker,
    TimeBucketFloat,
    TimeBucketInt,
    ValidationErrorDetail,
    ValidationResponse,
    ValidationSuggestion,
    ValidationWarning,
)

__all__ = [
    "APIError",
    "AsyncDataLegion",
    "AuthenticationError",
    "BadRequestError",
    "BulkCompanyEnrichResponse",
    "BulkCompanyItemResult",
    "BulkPersonEnrichResponse",
    "BulkPersonItemResult",
    "Certification",
    "CleanedName",
    "CleanedRaw",
    "CompanyDomain",
    "CompanyLocation",
    "CompanyMatch",
    "CompanyMatchesResponse",
    "CompanyResponse",
    "CompanySocial",
    "DataIssueReportResponse",
    "DataLegion",
    "DataLegionError",
    "DynamicBulkPersonEnrichResponse",
    "DynamicBulkPersonResult",
    "Education",
    "EducationOrganization",
    "Email",
    "EmailDomainCheck",
    "EmailHashResponse",
    "EmployeeCountByMonth",
    "Experience",
    "ExperienceOrganization",
    "FieldCleanResponse",
    "FieldCleanResult",
    "HealthResponse",
    "InsufficientCreditsError",
    "Language",
    "Location",
    "MatchMetadata",
    "NotFoundError",
    "PermissionDeniedError",
    "PersonMatch",
    "PersonMatchesResponse",
    "PersonResponse",
    "Phone",
    "RateLimitError",
    "RequestTimeoutError",
    "ServerError",
    "Skill",
    "Social",
    "Ticker",
    "TimeBucketFloat",
    "TimeBucketInt",
    "ValidationError",
    "ValidationErrorDetail",
    "ValidationResponse",
    "ValidationSuggestion",
    "ValidationWarning",
]
