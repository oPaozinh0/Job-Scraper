# Job Scraper

A comprehensive Python/Flask application for searching remote job positions across 9 Applicant Tracking System (ATS) platforms using the Google Serper API. Search by technology and seniority level to find relevant positions across multiple job boards.

## Features

- **11 Technology Presets**: PHP, JavaScript, Python, Java, C#, Ruby, Go, Rust, DevOps, Data, Mobile
- **7 Seniority Levels**: Any, Trainee, Junior, Mid-Level, Senior, Staff, Manager
- **9 ATS Platform Support**: Greenhouse, Lever, Ashby, Workable, BreezyHR, JazzHR, SmartRecruiters, ICIMS, PinpointHQ
- **Dual Interface**: Command-line tool and web dashboard with real-time progress tracking
- **Dynamic Query Builder**: Intelligent search queries with platform-specific optimizations
- **CSV Export**: Results automatically saved to date-stamped CSV files
- **REST API**: Full-featured API for programmatic access
- **Server-Sent Events (SSE)**: Real-time scraping progress updates via streaming
- **Comprehensive Testing**: 143+ unit tests with pytest

## Project Structure

```
.
├── scraper.py                # Core scraping logic with query builder
├── server.py                 # Flask backend with REST API
├── main.py                   # CLI entry point with argparse
├── templates/
│   └── index.html            # Frontend dashboard (single-page HTML)
├── test_scraper.py          # Unit tests for scraper module
├── test_server.py           # Unit tests for Flask API
├── test_queries.py          # Unit tests for query building
├── pyproject.toml           # Project metadata and dependencies
├── .env.example             # Environment variable template
└── README.md                # This file
```

## Getting Started

### Prerequisites

- Python 3.12 or higher
- Poetry (for dependency management)
- Serper API key (get free at [https://serper.dev](https://serper.dev))

### Installation

1. Clone or download the project:
```bash
git clone <repository-url>
cd job-scraper
```

2. Install dependencies using Poetry:
```bash
poetry install
```

3. Create a `.env` file based on the template:
```bash
cp .env.example .env
```

4. Add your Serper API key to the `.env` file:
```env
SERPAPI_API_KEY_1=your_serper_api_key_here
```

## Usage

### Command-Line Interface (CLI)

Search for jobs using the command line:

```bash
# Search for Python jobs at any level
poetry run python main.py --technology python --level any

# Search for senior-level JavaScript positions
poetry run python main.py -t javascript -l senior

# Search for junior DevOps engineers
poetry run python main.py --technology devops --level junior

# View available options
poetry run python main.py --help
```

#### Available Technologies
`php`, `javascript`, `python`, `java`, `csharp`, `ruby`, `go`, `rust`, `devops`, `data`, `mobile`

#### Available Levels
`any`, `trainee`, `junior`, `mid`, `senior`, `staff`, `manager`

### Web Server & Dashboard

Start the Flask development server:

```bash
poetry run python server.py
```

The dashboard will be available at `http://127.0.0.1:8000`

The web interface provides:
- Interactive job search and filtering
- Real-time scraping progress with live updates
- Job count by ATS platform
- Technology and seniority level selection
- CSV export functionality

## API Reference

### Endpoints

#### Dashboard
```
GET /
```
Returns the frontend dashboard HTML page.

#### List Jobs
```
GET /api/jobs?origin=Greenhouse&search=Python
```
Retrieve jobs from the latest CSV file with optional filters.

**Query Parameters:**
- `origin` (optional): Filter by ATS platform name (e.g., "Greenhouse", "Lever")
- `search` (optional): Filter by job title substring (case-insensitive)

**Response:**
```json
{
  "jobs": [
    {
      "title": "Senior Python Developer",
      "snippet": "...",
      "link": "https://...",
      "origin": "Greenhouse"
    }
  ],
  "total": 150,
  "file": "jobs_python_senior_2026-02-07.csv"
}
```

#### List Origins
```
GET /api/origins
```
Get job counts grouped by ATS platform.

**Response:**
```json
{
  "origins": [
    {"name": "Greenhouse", "count": 45},
    {"name": "Lever", "count": 38},
    {"name": "Ashby", "count": 32}
  ]
}
```

#### Available Technologies
```
GET /api/technologies
```
Get all available technology presets with their keywords.

**Response:**
```json
{
  "technologies": [
    {
      "key": "python",
      "label": "Python",
      "keywords": ["\"Python\"", "\"Django\"", "\"FastAPI\"", "\"Flask\""]
    }
  ]
}
```

#### Available Levels
```
GET /api/levels
```
Get all available seniority levels with their keywords.

**Response:**
```json
{
  "levels": [
    {
      "key": "senior",
      "label": "Senior",
      "keywords": ["\"Senior\"", "\"Sr\"", "\"Lead\""]
    }
  ]
}
```

#### Start Scraping
```
POST /api/fetch-jobs
Content-Type: application/json

{
  "technology": "python",
  "level": "senior"
}
```
Begin a full scrape across all 9 ATS platforms for the specified technology and level.

**Response:**
```json
{
  "status": "started",
  "stream_url": "/api/fetch-jobs/stream"
}
```

#### Scrape Status
```
GET /api/fetch-jobs/status
```
Get current scrape status without events.

**Response:**
```json
{
  "running": true,
  "completed": false,
  "events_count": 5
}
```

#### Scrape Progress Stream (SSE)
```
GET /api/fetch-jobs/stream
```
Server-Sent Events (SSE) stream for real-time scraping progress. Connect this endpoint after starting a scrape with `POST /api/fetch-jobs`.

**Event Types:**
- `ats_start`: ATS platform scrape started
- `page_fetched`: Page of results retrieved
- `ats_complete`: ATS platform scrape completed
- `complete`: Full scrape completed with results
- `error`: Error occurred during scrape

**Example Event:**
```json
{
  "event": "ats_complete",
  "origin": "Greenhouse",
  "count": 45,
  "index": 0,
  "total": 9
}
```

#### Reset Scraping
```
POST /api/fetch-jobs/reset
```
Reset the scraping state to allow a new scrape to begin.

**Response:**
```json
{
  "status": "reset"
}
```

#### Scrape Job Description
```
POST /api/scrape
Content-Type: application/json

{
  "url": "https://job-boards.greenhouse.io/company/jobs/123"
}
```
Scrape and extract content from a specific job URL using the Serper Scrape API.

**Response:**
```json
{
  "markdown": "# Job Title\n...",
  "text": "Job Title\n..."
}
```

## Output Files

CSV files are automatically saved with the following naming pattern:
```
jobs_{technology}_{level}_{date}.csv
```

Example:
- `jobs_python_senior_2026-02-07.csv`
- `jobs_javascript_junior_2026-02-08.csv`

### CSV Columns
- **Job Title**: Position title from job listing
- **Snippet**: Summary/description from search results
- **Link**: Direct URL to the job posting

## Testing

Run the complete test suite:

```bash
poetry run pytest
```

Run tests with coverage:

```bash
poetry run pytest --cov=. --cov-report=html
```

Run specific test file:

```bash
poetry run pytest test_scraper.py -v
poetry run pytest test_server.py -v
```

The project includes 143+ tests covering:
- Query builder functionality
- ATS platform-specific rules
- Job link validation
- CSV export
- Flask API endpoints
- SSE streaming
- Filter operations
- Cache behavior

## Architecture

### Scraper Module (`scraper.py`)

The core scraping engine with the following key functions:

**`build_ats_queries(technology, level)`**
Generates search queries for each ATS platform with intelligent filtering:
- PinpointHQ: Excludes level and location filters
- ICIMS: Excludes location filter
- Others: Full filtering with level and location

**`query_jobs(query, origin, api_key, target_min=50, on_progress=None)`**
Executes searches across multiple pages and collects unique, validated job listings.

**`run_full_scrape(api_key, technology, level, on_progress=None)`**
Orchestrates the complete scrape across all 9 ATS platforms with progress callbacks.

**`save_results_to_csv(results, output_dir, technology, level)`**
Exports results to a date-stamped CSV file.

### Server Module (`server.py`)

Flask application providing:
- REST API endpoints for job data and filtering
- Real-time SSE streaming for scrape progress
- CSV caching with automatic invalidation
- Background thread management for long-running scrapes
- Origin detection from job URLs

### Technology Presets

Each technology preset maps to related keywords for comprehensive searches:

| Technology | Keywords |
|------------|----------|
| PHP | PHP, Laravel |
| JavaScript | JavaScript, TypeScript, React, Node.js |
| Python | Python, Django, FastAPI, Flask |
| Java | Java, Spring, Spring Boot |
| C# | C#, .NET, ASP.NET |
| Ruby | Ruby, Ruby on Rails |
| Go | Golang, Go Developer |
| Rust | Rust, Rust Developer |
| DevOps | DevOps, SRE, Platform Engineer, Kubernetes |
| Data | Data Engineer, Data Scientist, Machine Learning, MLOps |
| Mobile | iOS, Android, React Native, Flutter |

## Configuration

### Environment Variables

Create a `.env` file in the project root:

```env
SERPAPI_API_KEY_1=your_serper_api_key_here
GOOGLE_API_KEY_1=your_google_api_key_here
GOOGLE_SEARCH_ENGINE_ID_1=your_search_engine_id_here
```

### Serper API

- Sign up at [https://serper.dev](https://serper.dev)
- Free tier provides 2,420 requests per month
- This project uses approximately 80 requests per run
- Supports up to 26 runs per month on the free tier

## Scheduling

### Windows Task Scheduler

Run weekly job searches:

1. Open Task Scheduler
2. Create Basic Task with:
   - **Action:** Start a program
   - **Program:** `C:\path\to\python.exe`
   - **Arguments:** `C:\path\main.py --technology php --level senior`
   - **Trigger:** Every Monday at 9:00 AM

### Linux/macOS Cron

Add to crontab for Monday 9:00 AM UTC:

```bash
0 9 * * 1 /path/to/python /path/to/main.py --technology php --level senior
```

## Limitations & Behavior

- Searches limited to jobs posted in the past 7 days (Google Serper `qdr:w` filter)
- Maximum 5 pages per ATS platform per search
- Results filtered to exclude non-ATS job aggregators (LinkedIn, Indeed, Glassdoor, etc.)
- Platform-specific query adaptations based on ATS capabilities
- 1-2 second delays between requests to respect API rate limits

## Performance

- Single technology/level scrape: ~90 seconds (9 ATS platforms)
- Average results: 300-500 jobs per scrape
- API calls per scrape: ~80 requests
- CSV file size: 50-150 KB

## Dependencies

Core dependencies:
- **requests**: HTTP client for API calls
- **flask**: Web framework for dashboard and API
- **python-decouple**: Environment variable management
- **weasyprint**: PDF generation (optional)

See `pyproject.toml` for complete dependency list.

## License

This project is provided as-is for educational and development purposes.

## Credits

- **Original Project**: [Marcelo Andriolli](https://github.com/marceloandriolli) - [Gist: Job Scraper in PHP](https://gist.github.com/marceloandriolli/d098fc65546c722394cd546b06687489)
- **Refactoring and Extension**: Davi Oliveira

The original PHP-based scraper has been refactored and significantly extended with:
- Python/Flask backend with REST API
- Multi-technology and multi-seniority support
- Real-time web dashboard with SSE streaming
- Comprehensive test coverage
- Production-ready architecture

## Support & Contributions

For issues, feature requests, or contributions, please open an issue or submit a pull request.

For questions about the Serper API, visit their [documentation](https://serper.dev/docs).
