from __future__ import annotations

import logging
from typing import Any

import pandas as pd
from fastapi import FastAPI, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from job_scraper_manager import JobScraperManager, SUPPORTED_SITES

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

app = FastAPI(title="Job Scraper")

# Add CORS middleware to allow frontend to communicate with backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DEFAULT_LIMIT = 60


class DataFramePayload(BaseModel):
    columns: list[str]
    rows: list[dict[str, Any]]
    row_count: int = Field(ge=0)


class ScrapeResponse(BaseModel):
    country: str
    role: str
    location: str | None
    sites: list[str]
    dataframe: DataFramePayload
    errors: dict[str, str] | None = None


def _validate_sites(sites: list[str]) -> list[str]:
    normalized = []
    for site in sites:
        value = site.lower().strip()
        if value not in SUPPORTED_SITES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported site '{site}'. Choose from {', '.join(SUPPORTED_SITES)}.",
            )
        normalized.append(value)
    return normalized


def _frame_from_records(records: list[dict[str, Any]], limit: int) -> pd.DataFrame:
    dataframe = pd.DataFrame(records)
    if dataframe.empty:
        return pd.DataFrame(columns=["title", "company", "location", "url", "source"])
    dataframe = dataframe.drop_duplicates(
        subset=["title", "company", "url", "source"],
        keep="first",
    )
    
    # Proportional limiting: take records evenly from each source
    unique_sources = dataframe['source'].unique()
    if len(unique_sources) == 0:
        return dataframe.head(limit)
    
    limit_per_source = limit // len(unique_sources)
    limited_dfs = []
    for source in unique_sources:
        source_df = dataframe[dataframe['source'] == source].head(limit_per_source)
        limited_dfs.append(source_df)
    
    result = pd.concat(limited_dfs, ignore_index=True)
    logger.info(f"After proportional limiting: {result['source'].value_counts().to_dict()}")
    return result


@app.get("/scrape", response_model=ScrapeResponse)
async def scrape(
    country: str = Query(..., min_length=2, description="Country (e.g., USA, Germany)"),
    role: str = Query(..., min_length=2, description="Job title or keywords to search for."),
    location: str | None = Query(
        default=None,
        description="Optional city, state, or region filter.",
    ),
    limit: int = Query(
        default=DEFAULT_LIMIT,
        ge=1,
        le=200,
        description="Maximum number of aggregated results to return.",
    ),
    sites: list[str] = Query(
        default=list(SUPPORTED_SITES),
        description="Subset of job boards to query.",
    ),
) -> ScrapeResponse:
    country_normalized = country.strip()
    role_normalized = role.strip()
    normalized_sites = _validate_sites(sites)

    manager = JobScraperManager(country=country_normalized)
    records, errors = await manager.scrape_jobs(
        role=role_normalized,
        sites=normalized_sites,
        location=location,
        limit=limit,
    )

    logger.info(f"Total records scraped: {len(records)}")
    
    # Log records by source
    from collections import Counter
    source_counts = Counter(record.source for record in records)
    logger.info(f"Records by source: {dict(source_counts)}")

    dataframe = _frame_from_records([record.to_dict() for record in records], limit)

    if dataframe.empty and errors:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to scrape any sites: {errors}",
        )

    return ScrapeResponse(
        country=country_normalized,
        role=role_normalized,
        location=location,
        sites=normalized_sites,
        dataframe=DataFramePayload(
            columns=list(dataframe.columns),
            rows=dataframe.to_dict(orient="records"),
            row_count=len(dataframe.index),
        ),
        errors=errors or None,
    )
