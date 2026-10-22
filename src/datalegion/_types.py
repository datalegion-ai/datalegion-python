"""Pydantic response models for the Data Legion API."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class _Base(BaseModel):
    """Base model that allows extra fields from the API."""

    model_config = ConfigDict(extra="allow")


# ---------------------------------------------------------------------------
# Shared / Nested Types
# ---------------------------------------------------------------------------


class CleanedRaw(_Base):
    cleaned: str | None = None
    raw: list[str] = []


class CleanedName(CleanedRaw):
    """Company name: ``CleanedRaw`` plus a presentational ``display`` form."""

    display: str | None = None


class Phone(_Base):
    type: str | None = None
    number: str | None = None
    current: bool | None = None
    confidence: str | None = None
    last_seen: str | None = None
    num_sources: int | None = None


class Email(_Base):
    address: str | None = None
    type: str | None = None
    current: bool | None = None
    validated: bool | None = None
    confidence: str | None = None
    last_seen: str | None = None
    num_sources: int | None = None
    validation_status: str | None = None
    hash_sha256: str | None = None
    hash_sha1: str | None = None
    hash_md5: str | None = None


class Location(_Base):
    street_address: str | None = None
    address_line_2: str | None = None
    city: str | None = None
    state: str | None = None
    state_code: str | None = None
    country: str | None = None
    country_code: str | None = None
    continent: str | None = None
    continent_code: str | None = None
    postal_code: str | None = None
    postal_code_4: str | None = None
    geo: str | None = None
    raw: list[str] = []
    current: bool | None = None
    num_sources: int | None = None
    confidence: str | None = None
    last_seen: str | None = None


class ExperienceOrganization(_Base):
    legion_id: str | None = None
    name: CleanedRaw | None = None
    website: str | None = None
    linkedin_url: str | None = None
    linkedin_id: str | None = None
    industry: str | None = None
    size: str | None = None


class Experience(_Base):
    title: CleanedRaw | None = None
    seniority_level: str | None = None
    job_function: str | None = None
    expense_category: str | None = None
    is_decision_maker: bool | None = None
    is_platform_worker: bool | None = None
    organization: ExperienceOrganization | None = None
    start_date: str | None = None
    end_date: str | None = None
    current: bool | None = None
    tenure_months: int | None = None
    description: CleanedRaw | None = None


class EducationOrganization(_Base):
    name: CleanedRaw | None = None
    website: str | None = None
    linkedin_url: str | None = None


class Education(_Base):
    organization: EducationOrganization | None = None
    degree: CleanedRaw | None = None
    degree_level: str | None = None
    field_of_study: CleanedRaw | None = None
    start_date: str | None = None
    end_date: str | None = None
    current: bool | None = None


class Social(_Base):
    network: str | None = None
    url: str | None = None
    username: str | None = None
    id: str | None = None
    current: bool | None = None
    num_sources: int | None = None
    confidence: str | None = None
    last_seen: str | None = None


class Skill(_Base):
    cleaned: str | None = None
    raw: list[str] = []


class Language(_Base):
    cleaned: str | None = None
    raw: list[str] = []
    proficiency: str | None = None


class Certification(_Base):
    name: CleanedRaw | None = None
    institution: CleanedRaw | None = None
    credential_id: str | None = None
    issue_date: str | None = None
    expiration_date: str | None = None


# ---------------------------------------------------------------------------
# Person Response
# ---------------------------------------------------------------------------


class PersonResponse(_Base):
    """A single person record."""

    legion_id: str

    # Name
    full_name: str | None = None
    first_name: str | None = None
    middle_name: str | None = None
    middle_initial: str | None = None
    last_name: str | None = None
    last_initial: str | None = None
    suffix: str | None = None
    prefix: str | None = None

    # Demographics
    sex: str | None = None
    birth_date: str | None = None
    birth_year: int | None = None
    birth_month: int | None = None
    birth_day: int | None = None
    age: int | None = None

    # Contact
    work_email: str | None = None
    mobile_phone: str | None = None
    linkedin_url: str | None = None
    linkedin_id: str | None = None

    # Location
    city: str | None = None
    state: str | None = None
    state_code: str | None = None
    country: str | None = None
    country_code: str | None = None

    # Professional
    job_title: str | None = None
    company_legion_id: str | None = None
    company_name: str | None = None
    company_domain: str | None = None
    company_linkedin_url: str | None = None
    company_linkedin_id: str | None = None
    company_industry: str | None = None
    company_size: str | None = None
    seniority_level: str | None = None
    job_function: str | None = None
    expense_category: str | None = None
    is_decision_maker: bool | None = None
    is_platform_worker: bool | None = None
    years_of_experience: int | None = None
    avg_tenure_months: float | None = None
    highest_degree_level: str | None = None

    # LinkedIn
    linkedin_followers: int | None = None
    linkedin_connections: int | None = None

    # Narrative
    headline: CleanedRaw | None = None
    summary: CleanedRaw | None = None

    # Metadata
    num_sources: int | None = None
    current_jobs_last_updated: str | None = None
    current_jobs_last_confirmed: str | None = None
    current_location_last_updated: str | None = None
    current_location_last_confirmed: str | None = None
    last_seen: str | None = None
    build_version: str | None = None

    # Arrays
    phones: list[Phone] = []
    emails: list[Email] = []
    locations: list[Location] = []
    experience: list[Experience] = []
    education: list[Education] = []
    certifications: list[Certification] = []
    socials: list[Social] = []
    skills: list[Skill] = []
    languages: list[Language] = []


class MatchMetadata(_Base):
    """Metadata about how a match was found."""

    matched_on: list[str] = []
    match_type: str | None = None
    match_confidence: str | None = None


class PersonMatch(_Base):
    """A single person match with optional match metadata."""

    person: PersonResponse
    match_metadata: MatchMetadata | None = None


class PersonMatchesResponse(_Base):
    """Response wrapper for multiple person matches."""

    matches: list[PersonMatch] = []
    total: int = 0


class BulkPersonItemResult(_Base):
    """A single result from a bulk person enrichment request."""

    matches: list[PersonMatch] | None = None
    total: int | None = None
    error: str | None = None
    metadata: dict[str, str | int | float | bool] | None = None


class BulkPersonEnrichResponse(_Base):
    """Response from a bulk person enrichment request."""

    results: list[BulkPersonItemResult] = []


class DynamicBulkPersonResult(_Base):
    """One item's result from a dynamic bulk enrichment.

    ``/dynamic`` returns only the requested contact groups, so only the phones
    and/or emails fields are populated (plus the echoed ``metadata`` and the
    matched ``legion_id``, or ``error`` when nothing was returned for the item).
    """

    metadata: dict[str, str | int | float | bool] | None = None
    legion_id: str | None = None
    phones: list[Phone] | None = None
    mobile_phone: str | None = None
    emails: list[Email] | None = None
    work_email: str | None = None
    error: str | None = None


class DynamicBulkPersonEnrichResponse(_Base):
    """Response from a dynamic bulk person enrichment request (phones/emails only)."""

    results: list[DynamicBulkPersonResult] = []


# ---------------------------------------------------------------------------
# Company Response
# ---------------------------------------------------------------------------


class Ticker(_Base):
    symbol: str | None = None
    exchange: str | None = None


class CompanySocial(_Base):
    network: str | None = None
    url: str | None = None
    username: str | None = None
    id: str | None = None


class CompanyDomain(_Base):
    domain: str | None = None


class CompanyLocation(_Base):
    """A company office. ``primary`` marks the primary location (at most one, always current);
    ``current`` is whether the office is still operating."""

    street_address: str | None = None
    address_line_2: str | None = None
    city: str | None = None
    state: str | None = None
    state_code: str | None = None
    country: str | None = None
    country_code: str | None = None
    continent: str | None = None
    continent_code: str | None = None
    postal_code: str | None = None
    geo: str | None = None
    raw: list[str] = []
    current: bool | None = None
    primary: bool | None = None
    num_sources: int | None = None
    last_seen: str | None = None


class EmployeeCountByMonth(_Base):
    month: str | None = None
    count: int | None = None
    net_change: int | None = None
    growth_rate: float | None = None
    hires: int | None = None
    departures: int | None = None


class TimeBucketInt(_Base):
    model_config = ConfigDict(extra="allow", populate_by_name=True)

    m1: int | None = Field(None, alias="1m")
    m3: int | None = Field(None, alias="3m")
    m6: int | None = Field(None, alias="6m")
    m12: int | None = Field(None, alias="12m")


class TimeBucketFloat(_Base):
    model_config = ConfigDict(extra="allow", populate_by_name=True)

    m1: float | None = Field(None, alias="1m")
    m3: float | None = Field(None, alias="3m")
    m6: float | None = Field(None, alias="6m")
    m12: float | None = Field(None, alias="12m")


class CompanyResponse(_Base):
    """A single company record."""

    legion_id: str

    # Base
    name: CleanedName | None = None
    headline: CleanedRaw | None = None
    description: CleanedRaw | None = None
    domain: str | None = None
    linkedin_url: str | None = None
    linkedin_id: str | None = None
    linkedin_followers: int | None = None
    linkedin_employee_count: int | None = None
    industry: str | None = None
    type: str | None = None
    size: str | None = None
    founded: int | None = None

    # Legion workforce analytics
    legion_employee_count: int | None = None
    legion_average_tenure: float | None = None

    # Time-bucketed metrics
    legion_new_hire_count: TimeBucketInt | None = None
    legion_attrition_count: TimeBucketInt | None = None
    legion_turnover_rate: TimeBucketFloat | None = None
    legion_employee_growth_rate: TimeBucketFloat | None = None

    # Distribution maps
    legion_seniority_distribution: dict[str, int] | None = None
    legion_job_function_distribution: dict[str, int] | None = None
    legion_expense_category_distribution: dict[str, int] | None = None
    legion_tenure_distribution: dict[str, int] | None = None
    legion_education_distribution: dict[str, int] | None = None

    # Growth rate maps
    legion_seniority_growth_rate: dict[str, TimeBucketFloat] | None = None
    legion_job_function_growth_rate: dict[str, TimeBucketFloat] | None = None
    legion_expense_category_growth_rate: dict[str, TimeBucketFloat] | None = None

    # Arrays
    tickers: list[Ticker] = []
    socials: list[CompanySocial] = []
    domains: list[CompanyDomain] = []
    locations: list[CompanyLocation] = []
    legion_employee_count_by_month: list[EmployeeCountByMonth] = []

    # Metadata
    num_sources: int | None = None
    last_seen: str | None = None
    build_version: str | None = None


class CompanyMatch(_Base):
    """A single company match with optional match metadata."""

    company: CompanyResponse
    match_metadata: MatchMetadata | None = None


class CompanyMatchesResponse(_Base):
    """Response wrapper for multiple company matches."""

    matches: list[CompanyMatch] = []
    total: int = 0


class BulkCompanyItemResult(_Base):
    """A single result from a bulk company enrichment request."""

    matches: list[CompanyMatch] | None = None
    total: int | None = None
    error: str | None = None
    metadata: dict[str, str | int | float | bool] | None = None


class BulkCompanyEnrichResponse(_Base):
    """Response from a bulk company enrichment request."""

    results: list[BulkCompanyItemResult] = []


# ---------------------------------------------------------------------------
# Utility Response Types
# ---------------------------------------------------------------------------


class FieldCleanResult(_Base):
    original: str
    cleaned: str | dict[str, str] | None = None
    normalized: bool = False


class FieldCleanResponse(_Base):
    results: dict[str, FieldCleanResult] = {}


class EmailHashResponse(_Base):
    email: str
    normalized_email: str
    hashes: dict[str, str] = {}


class ValidationErrorDetail(_Base):
    field: str
    value: str | None = None
    error: str
    suggestion: str | None = None


class ValidationWarning(_Base):
    field: str
    value: str | None = None
    warning: str
    suggestion: str | None = None


class ValidationSuggestion(_Base):
    field: str
    cleaned: str | dict[str, str] | None = None


class ValidationResponse(_Base):
    valid: bool
    errors: list[ValidationErrorDetail] = []
    warnings: list[ValidationWarning] = []
    suggestions: list[ValidationSuggestion] = []


# ---------------------------------------------------------------------------
# Data Issue Report Response
# ---------------------------------------------------------------------------


class DataIssueReportResponse(_Base):
    report_id: int
    status: str
    subject_type: str
    legion_id: str
    issue_type: str
    issue_level: str
    field: str | None = None
    created_at: str


# ---------------------------------------------------------------------------
# Health Response
# ---------------------------------------------------------------------------


class HealthResponse(_Base):
    status: str
    database: str | None = None
