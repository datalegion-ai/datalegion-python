<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://www.datalegion.ai/logo-light.svg">
    <source media="(prefers-color-scheme: light)" srcset="https://www.datalegion.ai/logo-dark.svg">
    <img alt="Data Legion" src="https://www.datalegion.ai/logo-dark.svg" width="260">
  </picture>
</p>

<h1 align="center">Data Legion Python SDK</h1>

<p align="center">
  <a href="https://github.com/datalegion-ai/datalegion-python/actions/workflows/test.yml"><img src="https://github.com/datalegion-ai/datalegion-python/actions/workflows/test.yml/badge.svg" alt="Tests"></a>&nbsp;&nbsp;
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-blue.svg" alt="License: MIT"></a>&nbsp;&nbsp;
  <a href="https://www.python.org"><img src="https://img.shields.io/badge/python-%3E%3D3.11-brightgreen.svg" alt="Python"></a>
</p>

The official Python client for the [Data Legion API](https://www.datalegion.ai/docs).

## Installation

```bash
pip install datalegion
```

## Quick Start

```python
from datalegion import DataLegion

client = DataLegion(api_key="legion_...")
```

Or set the `DATALEGION_API_KEY` environment variable and omit the `api_key` argument:

```python
client = DataLegion()
```

## Person Enrichment

Look up a person by email, phone, social URL, name, or other identifiers. Returns a `PersonResponse` with full type hints and dot access.

```python
person = client.person.enrich(email="john@example.com")
print(person.full_name)
print(person.job_title)
print(person.company_name)

# Multiple results
results = client.person.enrich(
    email="john@example.com",
    multiple_results=True,
    limit=5,
)
for match in results.matches:
    print(match.person.full_name, match.match_metadata.match_confidence)

# Enrich by name + company
person = client.person.enrich(
    first_name="John",
    last_name="Doe",
    company="Google",
)

# Enrich by LinkedIn URL
person = client.person.enrich(social_url="https://linkedin.com/in/johndoe")
```

## Person Search

Search for people using SQL queries.

```python
results = client.person.search(
    query="SELECT * FROM people WHERE company_name ILIKE '%google%' AND city = 'San Francisco'",
    limit=10,
)
for match in results.matches:
    print(match.person.full_name)
```

## Person Discover

Search for people using natural language.

```python
results = client.person.discover(
    query="engineers in San Francisco who worked at Google",
    limit=10,
)
for match in results.matches:
    print(match.person.full_name)
```

## Company Enrichment

Look up a company by domain, name, LinkedIn ID, or ticker symbol. Returns a `CompanyResponse` with dot access.

```python
# By domain
company = client.company.enrich(domain="google.com")
print(company.name.cleaned)
print(company.industry)
print(company.legion_employee_count)

# By name
company = client.company.enrich(name="Google")

# Multiple results
results = client.company.enrich(name="Apple", multiple_results=True, limit=3)
for match in results.matches:
    print(match.company.name.cleaned)
```

## Company Search

Search for companies using SQL queries.

```python
results = client.company.search(
    query="SELECT * FROM companies WHERE industry = 'software development'",
    limit=10,
)
for match in results.matches:
    print(match.company.name.cleaned)
```

## Company Discover

Search for companies using natural language.

```python
results = client.company.discover(
    query="AI companies with more than 100 employees",
    limit=10,
)
for match in results.matches:
    print(match.company.name.cleaned)
```

## Utilities

### Clean & Normalize Fields

```python
cleaned = client.utility.clean(
    fields={
        "email": "John.Doe+tag@gmail.com",
        "phone": "(555) 123-4567",
        "domain": "https://www.Google.com/about",
    }
)
for field, result in cleaned.results.items():
    print(f"{field}: {result.original} -> {result.cleaned}")
```

### Hash Email

```python
hashed = client.utility.hash_email(email="john@example.com")
print(hashed.hashes["sha256"])
print(hashed.hashes["md5"])
```

### Validate Data

```python
validated = client.utility.validate(
    email="john@example.com",
    phone="+15551234567",
    first_name="John",
)
print(validated.valid)
for error in validated.errors:
    print(f"{error.field}: {error.error}")
```

### Report a Data Issue

Report an inaccuracy in a person or company record against its `legion_id`. Free; see the [docs](https://www.datalegion.ai/docs/api-reference/utility-report) for the `issue_type`/`issue_level` rules.

```python
report = client.utility.report_person(
    legion_id="abc123",
    issue_type="incorrect",
    issue_level="field",
    field="job_title",
    observed_value="CEO",
    correct_value="CTO",
)
print(report.report_id, report.status)
```

Company records use `client.utility.report_company()` with the same parameters.

## Health Check

```python
health = client.health()
print(health.status)
```

## Async Usage

```python
import asyncio
from datalegion import AsyncDataLegion

async def main():
    client = AsyncDataLegion(api_key="legion_...")

    person = await client.person.enrich(email="john@example.com")
    print(person.full_name)

    company = await client.company.enrich(domain="google.com")
    print(company.name.cleaned)

    await client.close()

asyncio.run(main())
```

Or use as a context manager:

```python
async with AsyncDataLegion(api_key="legion_...") as client:
    person = await client.person.enrich(email="john@example.com")
```

## Response Types

All responses are [Pydantic](https://docs.pydantic.dev/) models with full type hints and autocomplete support. Import them directly:

```python
from datalegion import PersonResponse, CompanyResponse, PersonMatchesResponse
```

## Response Headers

After each request, these attributes are updated on the client:

```python
person = client.person.enrich(email="john@example.com")
print(client.request_id)             # unique request ID
print(client.credits_used)           # credits consumed
print(client.credits_remaining)      # credits remaining
print(client.contract_id)            # contract ID
print(client.rate_limit_limit)       # requests quota in current window
print(client.rate_limit_remaining)   # remaining requests in current window
print(client.rate_limit_reset)       # unix timestamp when window resets
print(client.rate_limit_policy)      # rate limit policy (e.g. "100/min")
print(client.retry_after)            # seconds to wait (on 429 responses)
print(client.generated_query)        # SQL from discover endpoints
print(client.correlation_id)         # echoed Correlation-ID
print(client.total_count_status)     # search/discover: "exact" | "estimate" | "page"
print(client.search_warning)         # search/discover: why a filter was flagged, or None
```

On `search`/`discover`, `total_count_status` tells you how the response `total` was derived: `exact` (true count), `estimate` (the query planner's row estimate — returned on broad queries where an exact count is too expensive, so treat it as a magnitude), or `page` (count unavailable; `total` is just the returned page size).

`search_warning` is set when a search flags one of its filters: for example an industry name that no stored value matches (the page comes back empty without being charged), or a pattern too short to search efficiently. It says what to change.

## Error Handling

```python
from datalegion import (
    DataLegion,
    AuthenticationError,
    InsufficientCreditsError,
    NotFoundError,
    RateLimitError,
    BadRequestError,
    ValidationError,
    APIError,
)

client = DataLegion(api_key="legion_...")

try:
    person = client.person.enrich(email="john@example.com")
except NotFoundError:
    print("No match (no credits used)")
except AuthenticationError as e:
    print(f"Invalid API key: {e.message}")
except InsufficientCreditsError as e:
    print(f"Out of credits: {e.message}")
except RateLimitError as e:
    print(f"Rate limited, retry after {client.retry_after}s: {e.message}")
except (BadRequestError, ValidationError) as e:
    print(f"Invalid request: {e.message}, details: {e.details}")
except APIError as e:
    print(f"API error ({e.status_code}): {e.message}")
```

| Status | Exception                                   |
| ------ | ------------------------------------------- |
| 400    | `BadRequestError`                           |
| 401    | `AuthenticationError`                       |
| 402    | `InsufficientCreditsError`                  |
| 403    | `PermissionDeniedError`                     |
| 404    | `NotFoundError` (no match; no credits used) |
| 408    | `RequestTimeoutError`                       |
| 422    | `ValidationError`                           |
| 429    | `RateLimitError`                            |
| 5xx    | `ServerError`                               |
| other  | `APIError`                                  |

`BadRequestError`, `PermissionDeniedError`, `NotFoundError`, `RequestTimeoutError` and `ServerError` subclass `APIError`. The client doesn't retry; on a 429, `client.retry_after` holds the seconds to wait.

All exceptions inherit from `DataLegionError` and include these attributes:

- `message` - Human-readable error message
- `status_code` - HTTP status code
- `error` - Error type/code from the API
- `details` - Additional error details (if any)

## Sandbox

Pass `sandbox=True` to try the SDK without spending credits. Enrich, bulk enrich, search and discover then return sample records (Jane Sandbox, Sandbox Corp) with every field a real record has; the utilities, which are free anyway, call the real API.

```python
client = DataLegion(api_key="legion_...", sandbox=True)
person = client.person.enrich(email="anyone@example.com")
print(person.legion_id)  # "sandbox_person_001"
```

Sandbox discover answers only a few fixed example queries; the error lists them. If your API key is limited to certain endpoints, add the `/sandbox/...` ones.

## Configuration

| Parameter      | Default                      | Description                             |
| -------------- | ---------------------------- | --------------------------------------- |
| `api_key`      | `DATALEGION_API_KEY` env var | Your API key                            |
| `base_url`     | `https://api.datalegion.ai`  | API base URL                            |
| `timeout`      | `60.0`                       | Request timeout in seconds              |
| `sandbox`      | `False`                      | Return sample records, use no credits   |
| `httpx_client` | None                         | Custom httpx.Client / httpx.AsyncClient |

## Documentation

For full API documentation, visit [https://www.datalegion.ai/docs](https://www.datalegion.ai/docs).
