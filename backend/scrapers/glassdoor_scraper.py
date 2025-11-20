from __future__ import annotations

import json
import re
from typing import Any
from urllib.parse import quote

import httpx

from .base_scraper import BaseJobScraper, JobRecord

FALLBACK_TOKEN = (
    "Ft6oHEWlRZrxDww95Cpazw:0pGUrkb2y3TyOpAIqF2vbPmUXoXVkD3oEGDVkvfeCerceQ5-n8mBg3BovySUIjmCPHCaW0H2nQVdqzbtsYqf4Q:"
    "wcqRqeegRUa9MVLJGyujVXB7vWFPjdaS1CtrrzJq-ok"
)

DEFAULT_LOCATION_ID = 11047
DEFAULT_LOCATION_TYPE = "STATE"
LOCATION_TYPE_MAP = {
    "C": "CITY",
    "S": "STATE",
    "N": "COUNTRY",
}
LOCATION_PARAM_PREFIX = {
    "CITY": "C",
    "STATE": "S",
    "COUNTRY": "N",
}

GRAPH_HEADERS = {
    "accept": "*/*",
    "accept-language": "en-US,en;q=0.9",
    "apollographql-client-name": "job-search-next",
    "apollographql-client-version": "4.65.5",
    "content-type": "application/json",
    "user-agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36"
    ),
}

QUERY_TEMPLATE = """
    query JobSearchResultsQuery(
        $keyword: String,
        $locationId: Int,
        $locationType: LocationTypeEnum,
        $numJobsToShow: Int!,
        $pageNumber: Int,
        $pageCursor: String,
        $parameterUrlInput: String
    ) {
        jobListings(
            contextHolder: {
                searchParams: {
                    keyword: $keyword,
                    locationId: $locationId,
                    locationType: $locationType,
                    numPerPage: $numJobsToShow,
                    pageNumber: $pageNumber,
                    pageCursor: $pageCursor,
                    parameterUrlInput: $parameterUrlInput,
                    searchType: SR
                }
            }
        ) {
            paginationCursors {
                cursor
                pageNumber
            }
            jobListings {
                jobview {
                    header {
                        jobTitleText
                        employerNameFromSearch
                        locationName
                        jobLink
                    }
                    job {
                        listingId
                    }
                }
            }
        }
    }
"""


class GlassdoorScraper(BaseJobScraper):
    """GraphQL-focused scraper for the Glassdoor jobs endpoint."""

    def __init__(self, client, *, domain: str):
        super().__init__("glassdoor", client)
        self.base_url = f"https://{domain}"

    async def fetch(
        self,
        *,
        role: str,
        location: str | None,
        country: str,
        limit: int,
    ) -> list[JobRecord]:
        csrf_token = await self._fetch_csrf_token()
        location_id, location_type = await self._resolve_location(location, csrf_token)
        if not location_type:
            raise RuntimeError("Glassdoor location lookup failed")

        headers = self._build_headers(csrf_token)
        location_filter = location.strip() if location else None
        filter_location_id = location_id if location_filter else None
        cursor = None
        page = 1
        jobs: list[JobRecord] = []

        while len(jobs) < limit and page <= 5:
            payload = self._build_payload(
                keyword=role,
                location_id=location_id,
                location_type=location_type,
                location_name=location,
                page_number=page,
                cursor=cursor,
            )
            response = await self.client.post(
                f"{self.base_url}/graph",
                headers=headers,
                content=json.dumps([payload]),
                timeout=20,
            )
            response.raise_for_status()
            parsed = response.json()[0]
            if "errors" in parsed:
                raise RuntimeError("Glassdoor GraphQL response contained errors")
            listings = (
                parsed.get("data", {})
                .get("jobListings", {})
                .get("jobListings", [])
            )
            cursor = self._next_cursor(
                parsed.get("data", {}).get("jobListings", {}).get("paginationCursors", []),
                page + 1,
            )
            if not listings:
                break
            jobs.extend(
                self._parse_listings(
                    listings,
                    location_filter=location_filter,
                    location_id=filter_location_id,
                ),
            )
            page += 1

        return self._dedupe(jobs)[:limit]

    async def _fetch_csrf_token(self) -> str:
        try:
            response = await self.client.get(
                f"{self.base_url}/Job/jobs.htm",
                timeout=15,
            )
            response.raise_for_status()
            matches = re.findall(r'"token":\s*"([^"]+)"', response.text)
            return matches[0] if matches else FALLBACK_TOKEN
        except httpx.HTTPError:
            return FALLBACK_TOKEN

    async def _resolve_location(self, location: str | None, token: str) -> tuple[int, str | None]:
        default = (DEFAULT_LOCATION_ID, DEFAULT_LOCATION_TYPE)
        if not location:
            return default
        encoded = quote(location)
        headers = self._build_location_headers(token)
        try:
            response = await self.client.get(
                f"{self.base_url}/findPopularLocationAjax.htm?maxLocationsToReturn=1&term={encoded}",
                headers=headers,
                timeout=10,
            )
            response.raise_for_status()
        except httpx.HTTPError:
            return default
        data = response.json()
        if not data:
            return default
        item = data[0]
        location_type = LOCATION_TYPE_MAP.get(item.get("locationType")) or DEFAULT_LOCATION_TYPE
        location_id = int(item.get("locationId", DEFAULT_LOCATION_ID))
        return location_id, location_type

    def _build_headers(self, token: str) -> dict[str, str]:
        headers = GRAPH_HEADERS.copy()
        headers["origin"] = self.base_url
        headers["referer"] = f"{self.base_url}/Job/jobs.htm"
        headers["gd-csrf-token"] = token or FALLBACK_TOKEN
        return headers

    def _build_location_headers(self, token: str) -> dict[str, str]:
        return {
            "accept": "application/json, text/javascript, */*; q=0.01",
            "user-agent": GRAPH_HEADERS["user-agent"],
            "referer": f"{self.base_url}/Job/jobs.htm",
            "x-requested-with": "XMLHttpRequest",
            "gd-csrf-token": token or FALLBACK_TOKEN,
        }

    def _build_payload(
        self,
        *,
        keyword: str,
        location_id: int,
        location_type: str,
        location_name: str | None,
        page_number: int,
        cursor: str | None,
    ) -> dict[str, Any]:
        parameter_url = self._build_parameter_url(
            location_name=location_name,
            location_type=location_type,
            location_id=location_id,
        )
        return {
            "operationName": "JobSearchResultsQuery",
            "variables": {
                "keyword": keyword,
                "locationId": location_id,
                "locationType": location_type,
                "numJobsToShow": 30,
                "pageNumber": page_number,
                "pageCursor": cursor,
                "parameterUrlInput": parameter_url,
            },
            "query": QUERY_TEMPLATE,
        }

    def _build_parameter_url(
        self,
        *,
        location_name: str | None,
        location_type: str,
        location_id: int,
    ) -> str:
        normalized = (location_name or "").strip()
        length = max(len(normalized), 1)
        type_prefix = LOCATION_PARAM_PREFIX.get(location_type.upper(), "S")
        return f"IL.0,{length}_I{type_prefix}{location_id}"

    def _parse_listings(
        self,
        listings: list[dict[str, Any]],
        *,
        location_filter: str | None,
        location_id: int | None,
    ) -> list[JobRecord]:
        records: list[JobRecord] = []
        normalized_filter = (
            self._normalize_location(location_filter) if location_filter else None
        )
        for listing in listings:
            jobview = listing.get("jobview") or {}
            header = jobview.get("header") or {}
            job = jobview.get("job") or {}
            job_id = job.get("listingId")
            if not job_id:
                continue
            if normalized_filter and not self._matches_location(
                header,
                normalized_filter,
                location_id,
            ):
                continue
            job_title = header.get("jobTitleText") or "N/A"
            company = header.get("employerNameFromSearch") or "N/A"
            location = header.get("locationName")
            job_link = header.get("jobLink") or ""
            if job_link and not job_link.startswith("http"):
                job_link = f"{self.base_url}{job_link}"
            records.append(
                JobRecord(
                    title=job_title.strip(),
                    company=company.strip(),
                    location=location.strip() if location else None,
                    url=job_link or f"{self.base_url}/job-listing/j?jl={job_id}",
                    source=self.site_name,
                ),
            )
        return records

    def _matches_location(
        self,
        header: dict[str, Any],
        normalized_filter: str,
        location_id: int | None,
    ) -> bool:
        loc_id = header.get("locId")
        if location_id and loc_id:
            try:
                if int(loc_id) == location_id:
                    return True
            except (TypeError, ValueError):
                pass
        location_value = header.get("locationName")
        if not location_value:
            return False
        normalized_location = self._normalize_location(location_value)
        if normalized_location == normalized_filter:
            return True
        return normalized_location.startswith(normalized_filter) or normalized_filter.startswith(
            normalized_location,
        )

    @staticmethod
    def _normalize_location(value: str) -> str:
        return re.sub(r"[^a-z0-9]", "", value.lower())

    @staticmethod
    def _next_cursor(cursors: list[dict[str, Any]], target_page: int) -> str | None:
        for cursor in cursors or []:
            if cursor.get("pageNumber") == target_page:
                return cursor.get("cursor")
        return None