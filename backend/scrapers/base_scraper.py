from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass
from typing import Any, Iterable

import httpx


@dataclass
class JobRecord:
    title: str
    company: str
    location: str | None
    url: str
    source: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class BaseJobScraper(ABC):
    """Async job scraper contract for normalizing board-specific data."""

    def __init__(self, site_name: str, client: httpx.AsyncClient):
        self.site_name = site_name
        self.client = client

    @abstractmethod
    async def fetch(
        self,
        *,
        role: str,
        location: str | None,
        country: str,
        limit: int,
    ) -> list[JobRecord]:
        """Return up to `limit` JobRecord entries for the given query."""

    @staticmethod
    def _dedupe(records: Iterable[JobRecord]) -> list[JobRecord]:
        """Remove duplicate entries using (title, company, url)."""
        seen: set[tuple[str, str, str]] = set()
        unique: list[JobRecord] = []
        for record in records:
            key = (record.title, record.company, record.url)
            if key in seen:
                continue
            seen.add(key)
            unique.append(record)
        return unique