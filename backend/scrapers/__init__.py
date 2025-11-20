"""Scraper implementations for backend job sourcing."""

from .base_scraper import BaseJobScraper, JobRecord
from .glassdoor_scraper import GlassdoorScraper
from .indeed_scraper import IndeedScraper
from .linkedin_scraper import LinkedInScraper

__all__ = [
    "BaseJobScraper",
    "JobRecord",
    "GlassdoorScraper",
    "IndeedScraper",
    "LinkedInScraper",
]

