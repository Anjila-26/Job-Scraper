## Job Scraper API

The FastAPI backend exposes a single `/scrape` endpoint that scrapes Glassdoor,
Indeed, and LinkedIn in parallel, merges the results into a pandas DataFrame,
and returns the serialized rows plus metadata.

### Running the server

```bash
uv run uvicorn main:app --reload
```

### Request parameters

| Query      | Required | Description                                         |
|------------|----------|-----------------------------------------------------|
| `country`  | Yes      | Country name or code (e.g., `USA`, `Germany`)       |
| `role`     | Yes      | Keywords/job title to search for                    |
| `location` | No       | City/state/region filter applied to each scraper    |
| `limit`    | No       | Max rows to return (default `60`, max `200`)        |
| `sites`    | No       | Repeated query param to limit boards (default all)  |

### Sample request

```
GET /scrape?country=USA&role=data%20scientist&location=New%20York
```

### Response body

```json
{
  "country": "USA",
  "role": "data scientist",
  "location": "New York",
  "sites": ["glassdoor", "indeed", "linkedin"],
  "dataframe": {
    "columns": ["title", "company", "location", "url", "source"],
    "rows": [
      {
        "title": "Data Scientist",
        "company": "Example Corp",
        "location": "New York, NY",
        "url": "https://www.indeed.com/viewjob?jk=...",
        "source": "indeed"
      }
    ],
    "row_count": 1
  },
  "errors": null
}
```

`row_count` reflects the shape of the pandas DataFrame that was built on the
server before serialization. If one or more scrapers fail, the `errors` field
lists the site along with the captured exception message.

### Tests

All scraper and endpoint behavior is covered via pytest:

```bash
uv run pytest
```
