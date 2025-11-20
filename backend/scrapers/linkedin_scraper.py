from __future__ import annotations

import logging
from typing import Any
from urllib.parse import urlencode

from bs4 import BeautifulSoup

from .base_scraper import BaseJobScraper, JobRecord

logger = logging.getLogger(__name__)

SEARCH_URL = "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search"

LINKEDIN_HEADERS = {
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9",
    "accept-language": "en-US,en;q=0.9",
    "cache-control": "no-cache",
    "user-agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
}


class LinkedInScraper(BaseJobScraper):
    """LinkedIn guest endpoint scraper."""

    def __init__(self, client):
        super().__init__("linkedin", client)

    async def fetch(
        self,
        *,
        role: str,
        location: str | None,
        country: str,
        limit: int,
    ) -> list[JobRecord]:
        start = 0
        jobs: list[JobRecord] = []
        while len(jobs) < limit and start < 1000:
            params = self._build_params(role, location, start)
            logger.info(f"LinkedIn: Requesting jobs for role='{role}', location='{location}', start={start}")
            response = await self.client.get(
                f"{SEARCH_URL}?{urlencode(params)}",
                headers=LINKEDIN_HEADERS,
                timeout=20,
            )
            response.raise_for_status()
            batch = self._parse_html(response.text, filter_location=location)
            logger.info(f"LinkedIn: Found {len(batch)} jobs at offset {start} (after filtering)")
            if not batch:
                break
            jobs.extend(batch)
            start += len(batch)
        return self._dedupe(jobs)[:limit]

    def _build_params(
        self,
        role: str,
        location: str | None,
        start: int,
    ) -> dict[str, Any]:
        params = {"keywords": role, "start": start}
        if location:
            params["location"] = location
            # Add remote filter if location contains "remote"
            if "remote" in location.lower():
                params["f_WT"] = "2"  # LinkedIn's remote filter
        return params

    def _parse_html(self, html: str, filter_location: str | None = None) -> list[JobRecord]:
        soup = BeautifulSoup(html, "html.parser")
        cards = soup.find_all("div", class_="base-search-card")
        records: list[JobRecord] = []
        
        # Extract location keywords for filtering (only if not remote/flexible)
        location_keywords = set()
        should_filter_location = False
        if filter_location:
            filter_lower = filter_location.lower()
            # Don't filter if location is remote/anywhere/flexible
            if not any(x in filter_lower for x in ["remote", "anywhere", "flexible", "worldwide"]):
                # Split location and normalize for matching
                location_keywords = {word.lower() for word in filter_location.replace(",", " ").split() if len(word) > 2}
                should_filter_location = True
        
        for card in cards:
            title = self._text_or_none(
                card.find("h3", class_="base-search-card__title")
            ) or self._text_or_none(card.find("span", class_="sr-only"))
            company = self._text_or_none(
                card.find("h4", class_="base-search-card__subtitle")
            )
            location = self._text_or_none(
                card.find("span", class_="job-search-card__location")
            )
            
            # Filter: If specific location is requested (not remote), check if job location matches
            if should_filter_location and location:
                location_lower = location.lower()
                # Check if at least one keyword from the requested location appears in the job location
                if not any(keyword in location_lower for keyword in location_keywords):
                    logger.debug(f"LinkedIn: Filtering out job in '{location}' - doesn't match '{filter_location}'")
                    continue
            
            link_tag = card.find("a", class_="base-card__full-link")
            href = link_tag["href"] if link_tag and link_tag.has_attr("href") else ""
            if href and "?" in href:
                href = href.split("?")[0]
            records.append(
                JobRecord(
                    title=title or "N/A",
                    company=company or "N/A",
                    location=location,
                    url=href or "https://www.linkedin.com/jobs",
                    source=self.site_name,
                ),
            )
        return records

    @staticmethod
    def _text_or_none(tag) -> str | None:
        if not tag:
            return None
        text = tag.get_text(strip=True)
        return text or None
