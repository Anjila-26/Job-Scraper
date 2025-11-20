# Job Chatbot Platform

## Overview

This project is a smart job search platform that scrapes listings from multiple sources and presents them in a conversational, chatbot-like interface. It combines robust backend scraping with a modern frontend for an efficient and enjoyable job search experience.

## Features

- Scrapes jobs from Glassdoor, Indeed, and LinkedIn
- Unified API for fetching job results
- Interactive UI for submitting queries and viewing results
- Conversational chatbot-like guidance
- Sortable, filterable job results table
- Automated backend and frontend tests

## Technology Stack

**Backend:** Python, custom scrapers, FastAPI (or similar), Pytest
**Frontend:** Next.js, React, TypeScript, Tailwind CSS

## Project Structure

- `backend/`: Python scrapers, API, and tests
- `frontend/`: Next.js app, UI components, and utilities
- `.cursor/rules/`: Project rules and documentation

## How It Works

1. User submits a job search query via the frontend
2. Backend scrapers fetch job listings from selected sources
3. Results are returned and displayed in a table
4. User can interact with results, filter, and sort them
5. Chatbot-like features guide users through the job search process

## Usage

1. Install backend and frontend dependencies
2. Run backend API server
3. Start frontend development server
4. Access the app in your browser and start searching for jobs!

## Challenges and Solutions

- Anti-scraping measures: Implemented error handling and request throttling
- Data normalization: Unified job data from different sources
- Scalability: Modular scraper design for easy extension
- User experience: Focused on clean UI and fast, responsive interactions

## Final Thoughts

This project combines web scraping, API design, and modern frontend development into a cohesive platform. The modular structure makes it easy to add new job sources or features. The chatbot-like interface and unified job search make the process more efficient and user-friendly.
# GigGenie