from __future__ import annotations

import html
import logging
from typing import Any

from .base_scraper import BaseJobScraper, JobRecord

logger = logging.getLogger(__name__)

JOB_SEARCH_QUERY = """
    query GetJobData {{
        jobSearch(
            {what}
            {location}
            limit: 100
            {cursor}
            sort: RELEVANCE
            {filters}
        ) {{
            pageInfo {{
                nextCursor
            }}
            results {{
                job {{
                    key
                    title
                    employer {{
                        name
                    }}
                    location {{
                        formatted {{
                            long
                        }}
                    }}
                    description {{
                        html
                    }}
                }}
            }}
        }}
    }}
"""

API_HEADERS = {
    "Host": "apis.indeed.com",
    "content-type": "application/json",
    "indeed-api-key": "161092c2017b5bbab13edb12461a62d5a833871e7cad6d9d475304573de67ac8",
    "accept": "application/json",
    "indeed-locale": "en-US",
    "accept-language": "en-US,en;q=0.9",
    "user-agent": (
        "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6_1 like Mac OS X) "
        "AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 Indeed App 193.1"
    ),
    "indeed-app-info": "appv=193.1; appid=com.indeed.jobsearch; osv=16.6.1; os=ios; dtype=phone",
}


class IndeedScraper(BaseJobScraper):
    """Minimal GraphQL client for the Indeed job search API."""

    API_URL = "https://apis.indeed.com/graphql"

    def __init__(
        self,
        client,
        *,
        domain: str,
        api_country_code: str,
    ):
        super().__init__("indeed", client)
        self.base_url = f"https://{domain}"
        self.api_country_code = api_country_code.upper()

    async def fetch(
        self,
        *,
        role: str,
        location: str | None,
        country: str,
        limit: int,
    ) -> list[JobRecord]:
        cursor: str | None = None
        collected: list[JobRecord] = []
        pages = 0
        try:
            while len(collected) < limit and pages < 5:
                query = self._build_query(role, location, cursor)
                headers = API_HEADERS.copy()
                headers["indeed-co"] = self.api_country_code
                
                logger.info(f"Indeed: Requesting jobs for role='{role}', country={self.api_country_code}, page={pages}")
                
                response = await self.client.post(
                    self.API_URL,
                    json={"query": query},
                    headers=headers,
                    timeout=20,
                )
                
                logger.info(f"Indeed: Response status={response.status_code}")
                
                if response.status_code != 200:
                    logger.error(f"Indeed API error: status={response.status_code}, body={response.text[:500]}")
                    response.raise_for_status()
                
                payload = response.json()
                
                # Check for GraphQL errors
                if "errors" in payload:
                    error_msg = payload["errors"][0].get("message", "Unknown error") if payload["errors"] else "Unknown error"
                    logger.error(f"Indeed GraphQL error: {error_msg}")
                    raise Exception(f"Indeed API returned error: {error_msg}")
                
                jobs, cursor = self._parse_results(payload, role=role)
                logger.info(f"Indeed: Found {len(jobs)} jobs on page {pages} (after filtering)")
                
                if not jobs:
                    break
                collected.extend(jobs)
                if not cursor:
                    break
                pages += 1

            logger.info(f"Indeed: Total collected {len(collected)} jobs")
            return self._dedupe(collected)[:limit]
            
        except Exception as e:
            logger.error(f"Indeed scraper failed: {type(e).__name__}: {str(e)}")
            raise

    def _build_query(
        self,
        role: str,
        location: str | None,
        cursor: str | None,
    ) -> str:
        encoded_role = html.escape(role or "")
        encoded_location = html.escape(location or "") if location else ""
        what = f'what: "{encoded_role}"' if encoded_role else ""
        loc = (
            'location: {{where: "{location}", radius: 25, radiusUnit: MILES}}'.format(
                location=encoded_location
            )
            if encoded_location
            else ""
        )
        cursor_clause = f'cursor: "{cursor}"' if cursor else ""
        return JOB_SEARCH_QUERY.format(
            what=what,
            location=loc,
            cursor=cursor_clause,
            filters="",
        )

    def _parse_results(
        self,
        payload: dict[str, Any],
        role: str | None = None,
    ) -> tuple[list[JobRecord], str | None]:
        data = payload.get("data", {}).get("jobSearch", {})
        results = data.get("results", []) or []
        next_cursor = data.get("pageInfo", {}).get("nextCursor")
        records: list[JobRecord] = []
        
        # Extract key terms from the requested role for filtering
        # Exclude common generic words that would match too broadly
        generic_words = {"engineer", "developer", "manager", "analyst", "specialist", "consultant", "lead", "senior", "junior", "staff"}
        # Allow important short acronyms
        important_short_words = {"ai", "ml", "qa", "ui", "ux", "ar", "vr"}
        role_keywords = set()
        if role:
            # Split role into words and convert to lowercase for matching
            words = [word.lower() for word in role.split()]
            # Filter words: keep if length > 2 OR if it's an important short word
            words = [word for word in words if len(word) > 2 or word in important_short_words]
            # Only use specific keywords, not generic ones (unless it's the only word)
            if len(words) > 1:
                role_keywords = {word for word in words if word not in generic_words}
            else:
                role_keywords = set(words)  # Use all words if only one keyword
            
            # If no keywords remain after filtering, use the original role as-is
            if not role_keywords:
                role_keywords = {role.lower()}
        
        for entry in results:
            job = entry.get("job") or {}
            job_id = job.get("key")
            if not job_id:
                continue
            title = job.get("title") or "N/A"
            
            # Filter: If role is specified, check if job title contains relevant keywords
            if role_keywords:
                title_lower = title.lower()
                # Check if at least one significant keyword from the role appears in the title
                if not any(keyword in title_lower for keyword in role_keywords):
                    logger.debug(f"Indeed: Filtering out '{title}' - doesn't match role '{role}'")
                    continue
            
            employer = (job.get("employer") or {}).get("name") or "N/A"
            location_data = (job.get("location") or {}).get("formatted") or {}
            location = location_data.get("long")
            job_url = f"{self.base_url}/viewjob?jk={job_id}"
            records.append(
                JobRecord(
                    title=title.strip(),
                    company=employer.strip(),
                    location=location.strip() if location else None,
                    url=job_url,
                    source=self.site_name,
                ),
            )
        return records, next_cursor