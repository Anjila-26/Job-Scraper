from __future__ import annotations

import sys
from pathlib import Path

import httpx
import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

from scrapers.glassdoor_scraper import GlassdoorScraper
from scrapers.indeed_scraper import IndeedScraper
from scrapers.linkedin_scraper import LinkedInScraper


@pytest.mark.asyncio
async def test_linkedin_scraper_parses_jobs():
    html = """
    <div class="base-search-card">
        <a class="base-card__full-link" href="https://www.linkedin.com/jobs/view/12345/" />
        <h3 class="base-search-card__title">Senior Engineer</h3>
        <h4 class="base-search-card__subtitle">Acme Corp</h4>
        <span class="job-search-card__location">Remote</span>
    </div>
    """
    request_count = {"value": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        request_count["value"] += 1
        body = html if request_count["value"] == 1 else ""
        return httpx.Response(200, text=body)

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        scraper = LinkedInScraper(client)
        jobs = await scraper.fetch(
            role="engineer",
            location="Remote",
            country="usa",
            limit=5,
        )

    assert len(jobs) == 1
    assert jobs[0].title == "Senior Engineer"
    assert jobs[0].company == "Acme Corp"


@pytest.mark.asyncio
async def test_indeed_scraper_parses_jobs():
    payload = {
        "data": {
            "jobSearch": {
                "pageInfo": {"nextCursor": None},
                "results": [
                    {
                        "job": {
                            "key": "abc123",
                            "title": "Data Scientist",
                            "employer": {"name": "Example Inc"},
                            "location": {"formatted": {"long": "New York, NY"}},
                        },
                    }
                ],
            }
        }
    }

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path.endswith("/graphql")
        return httpx.Response(200, json=payload)

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        scraper = IndeedScraper(
            client,
            domain="www.indeed.com",
            api_country_code="US",
        )
        jobs = await scraper.fetch(
            role="data scientist",
            location="New York, NY",
            country="usa",
            limit=5,
        )

    assert len(jobs) == 1
    assert jobs[0].company == "Example Inc"
    assert jobs[0].url.endswith("jk=abc123")


@pytest.mark.asyncio
async def test_glassdoor_scraper_parses_jobs():
    responses = {
        "token": httpx.Response(200, text='{"token":"mock-token"}'),
        "location": httpx.Response(
            200,
            json=[{"locationId": 1, "locationType": "C"}],
        ),
        "graph": httpx.Response(
            200,
            json=[
                {
                    "data": {
                        "jobListings": {
                            "jobListings": [
                                {
                                    "jobview": {
                                        "job": {"listingId": "789"},
                                        "header": {
                                            "jobTitleText": "ML Engineer",
                                            "employerNameFromSearch": "Glassdoor Labs",
                                            "locationName": "San Francisco, CA",
                                            "jobLink": "/job-listing/j?jl=789",
                                            "locId": 1,
                                        },
                                    }
                                },
                                {
                                    "jobview": {
                                        "job": {"listingId": "000"},
                                        "header": {
                                            "jobTitleText": "Remote Role",
                                            "employerNameFromSearch": "Remote Only Inc",
                                            "locationName": "Remote",
                                            "jobLink": "/job-listing/j?jl=000",
                                            "locId": 999,
                                        },
                                    }
                                }
                            ],
                            "paginationCursors": [],
                        }
                    }
                }
            ],
        ),
    }

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/Job/jobs.htm"):
            return responses["token"]
        if request.url.path.endswith("findPopularLocationAjax.htm"):
            return responses["location"]
        if request.url.path.endswith("/graph"):
            return responses["graph"]
        raise AssertionError(f"Unexpected request: {request.url}")

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        scraper = GlassdoorScraper(client, domain="www.glassdoor.com")
        jobs = await scraper.fetch(
            role="ml engineer",
            location="San Francisco, CA",
            country="usa",
            limit=5,
        )

    assert len(jobs) == 1
    assert jobs[0].title == "ML Engineer"
    assert jobs[0].source == "glassdoor"
    assert "glassdoor.com" in jobs[0].url

