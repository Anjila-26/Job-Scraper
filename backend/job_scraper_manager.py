from __future__ import annotations

import asyncio
from typing import Iterable

import httpx

from scrapers import GlassdoorScraper, IndeedScraper, JobRecord, LinkedInScraper

REQUEST_HEADERS = {
    "user-agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "accept-language": "en-US,en;q=0.9",
}

COUNTRY_CONFIG = {
    "usa": {
        "glassdoor_domain": "www.glassdoor.com",
        "indeed_domain": "www.indeed.com",
        "indeed_api_code": "US",
    },
    "united states": {
        "glassdoor_domain": "www.glassdoor.com",
        "indeed_domain": "www.indeed.com",
        "indeed_api_code": "US",
    },
    "us": {
        "glassdoor_domain": "www.glassdoor.com",
        "indeed_domain": "www.indeed.com",
        "indeed_api_code": "US",
    },
    "canada": {
        "glassdoor_domain": "www.glassdoor.ca",
        "indeed_domain": "ca.indeed.com",
        "indeed_api_code": "CA",
    },
    "uk": {
        "glassdoor_domain": "www.glassdoor.co.uk",
        "indeed_domain": "uk.indeed.com",
        "indeed_api_code": "UK",
    },
    "united kingdom": {
        "glassdoor_domain": "www.glassdoor.co.uk",
        "indeed_domain": "uk.indeed.com",
        "indeed_api_code": "UK",
    },
    "germany": {
        "glassdoor_domain": "www.glassdoor.de",
        "indeed_domain": "de.indeed.com",
        "indeed_api_code": "DE",
    },
    "india": {
        "glassdoor_domain": "www.glassdoor.co.in",
        "indeed_domain": "in.indeed.com",
        "indeed_api_code": "IN",
    },
    "australia": {
        "glassdoor_domain": "www.glassdoor.com.au",
        "indeed_domain": "au.indeed.com",
        "indeed_api_code": "AU",
    },
}

DEFAULT_COUNTRY = "usa"
SUPPORTED_SITES = ("linkedin", "indeed", "glassdoor")


class JobScraperManager:
    """Coordinates LinkedIn/Indeed/Glassdoor scrapers for unified output."""

    def __init__(self, country: str):
        normalized = country.strip().lower()
        self.country = normalized or DEFAULT_COUNTRY
        self.country_config = COUNTRY_CONFIG.get(self.country, COUNTRY_CONFIG[DEFAULT_COUNTRY])

    async def scrape_jobs(
        self,
        *,
        role: str,
        sites: Iterable[str],
        location: str | None,
        limit: int,
    ) -> tuple[list[JobRecord], dict[str, str]]:
        async with httpx.AsyncClient(
            timeout=30,  # Increased from 20 to 30 seconds
            headers=REQUEST_HEADERS,
            follow_redirects=True,
        ) as client:
            scrapers = self._build_scrapers(client)
            selected_sites = [
                site.lower().strip()
                for site in sites
                if site.lower().strip() in scrapers
            ]
            tasks = [
                self._run_scraper(scrapers[site], role, location, limit)
                for site in selected_sites
            ]
            results = await asyncio.gather(*tasks, return_exceptions=True)

        aggregated: list[JobRecord] = []
        errors: dict[str, str] = {}
        for site, result in zip(selected_sites, results):
            if isinstance(result, Exception):
                errors[site] = str(result)
                continue
            aggregated.extend(result)
        return aggregated, errors

    def _build_scrapers(self, client: httpx.AsyncClient):
        config = self.country_config
        return {
            "linkedin": LinkedInScraper(client),
            "indeed": IndeedScraper(
                client,
                domain=config["indeed_domain"],
                api_country_code=config["indeed_api_code"],
            ),
            "glassdoor": GlassdoorScraper(
                client,
                domain=config["glassdoor_domain"],
            ),
        }

    async def _run_scraper(
        self,
        scraper,
        role: str,
        location: str | None,
        limit: int,
    ) -> list[JobRecord]:
        return await scraper.fetch(
            role=role,
            location=location,
            country=self.country,
            limit=limit,
        )
