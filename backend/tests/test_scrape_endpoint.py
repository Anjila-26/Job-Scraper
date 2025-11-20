from __future__ import annotations

import sys
from pathlib import Path

from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

from job_scraper_manager import JobScraperManager
from main import app
from scrapers import JobRecord

client = TestClient(app)


def test_scrape_success(monkeypatch):
    async def fake_scrape_jobs(self, *, role, sites, location, limit):
        return (
            [
                JobRecord(
                    title="Backend Engineer",
                    company="Example",
                    location="Remote",
                    url="https://example.com/job",
                    source="indeed",
                )
            ],
            {},
        )

    monkeypatch.setattr(JobScraperManager, "scrape_jobs", fake_scrape_jobs)

    response = client.get("/scrape?country=USA&role=engineer&limit=5")

    assert response.status_code == 200
    body = response.json()
    assert body["dataframe"]["row_count"] == 1
    assert body["dataframe"]["rows"][0]["company"] == "Example"


def test_scrape_failure(monkeypatch):
    async def fake_scrape_jobs(self, *, role, sites, location, limit):
        return ([], {"indeed": "timeout"})

    monkeypatch.setattr(JobScraperManager, "scrape_jobs", fake_scrape_jobs)

    response = client.get("/scrape?country=USA&role=engineer")

    assert response.status_code == 502


def test_scrape_rejects_unknown_site(monkeypatch):
    response = client.get(
        "/scrape?country=USA&role=engineer&sites=indeed&sites=unknown",
    )
    assert response.status_code == 400

