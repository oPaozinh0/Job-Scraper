from __future__ import annotations

import csv
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Callable, Iterable

import requests

ProgressCallback = Callable[[str, dict], None]

TECHNOLOGY_PRESETS: dict[str, list[str]] = {
    "php": ['"PHP"', '"Laravel"'],
    "javascript": ['"JavaScript"', '"TypeScript"', '"React"', '"Node.js"'],
    "python": ['"Python"', '"Django"', '"FastAPI"', '"Flask"'],
    "java": ['"Java"', '"Spring"', '"Spring Boot"'],
    "csharp": ['"C#"', '".NET"', '"ASP.NET"'],
    "ruby": ['"Ruby"', '"Ruby on Rails"'],
    "go": ['"Golang"', '"Go Developer"'],
    "rust": ['"Rust"', '"Rust Developer"'],
    "devops": ['"DevOps"', '"SRE"', '"Platform Engineer"', '"Kubernetes"'],
    "data": ['"Data Engineer"', '"Data Scientist"', '"Machine Learning"', '"MLOps"'],
    "mobile": ['"iOS"', '"Android"', '"React Native"', '"Flutter"'],
}

SENIORITY_LEVELS: dict[str, list[str]] = {
    "any": [],
    "trainee": ['"Trainee"', '"Intern"', '"Internship"'],
    "junior": ['"Junior"', '"Jr"', '"Entry Level"', '"Entry-Level"'],
    "mid": ['"Mid-Level"', '"Mid Level"', '"Middle"', '"Intermediate"'],
    "senior": ['"Senior"', '"Sr"', '"Lead"'],
    "staff": ['"Staff"', '"Staff Engineer"', '"Principal"'],
    "manager": ['"Engineering Manager"', '"Tech Lead"', '"CTO"', '"VP of Engineering"'],
}

ATS_PLATFORMS: dict[str, str] = {
    "Green House": "site:greenhouse.io",
    "Lever": "site:lever.co",
    "AshBy": "site:jobs.ashbyhq.com",
    "Workable": "site:jobs.workable.com",
    "Breezy": "site:breezy.hr",
    "Jazz CO": "site:jazz.co",
    "Smart Recruiters": "site:smartrecruiters.com",
    "ICIMS": "site:icims.com",
    "PinpointHQ": "site:pinpointhq.com",
}

EXCLUDED_PATTERNS: list[str] = [
    "facebook.com",
    "linkedin.com",
    "twitter.com",
    "reddit.com",
    "hacker-news",
    "hnhiring.com",
    "glassdoor.com",
    "indeed.com",
    "ziprecruiter.com",
    "weworkremotely.com",
    "jobleads.com",
    "upwork.com",
    "/careers/?$",
    "dover.com",
    "dovercorporation.com",
    "app.dover.com/dover/careers",
]

VALID_PATTERNS: list[str] = [
    "greenhouse.io",
    "lever.co",
    "ashbyhq.com",
    "workable.com",
    "breezy.hr",
    "jazz.co",
    "smartrecruiters.com",
    "icims.com",
    "pinpointhq.com",
    "app.dover.",
]

SERPER_URL: str = "https://google.serper.dev/search"


def _emit_progress(on_progress: ProgressCallback | None, event: str, data: dict) -> None:
    """Emit a progress event if a callback is provided."""

    if on_progress is None:
        return
    try:
        on_progress(event, data)
    except Exception:  # pragma: no cover - caller-owned callback
        logging.getLogger(__name__).exception("Progress callback failed")


def is_valid_job_link(link: str, origin: str) -> bool:
    """Check whether a job link is valid for the configured ATS sources.

    Args:
        link: Job URL to validate.
        origin: ATS name (currently unused, kept for compatibility).

    Returns:
        True if link matches valid patterns and not excluded.
    """

    lowered = link.lower()
    for pattern in EXCLUDED_PATTERNS:
        if pattern in lowered:
            return False

    has_valid_pattern = any(pattern in lowered for pattern in VALID_PATTERNS)
    return has_valid_pattern


def fetch_page(query: str, origin: str, page: int, api_key: str) -> dict:
    """Fetch a page of results from Serper.

    Args:
        query: Search query to execute.
        origin: ATS origin for logging context.
        page: Page number to retrieve.
        api_key: Serper API key.

    Returns:
        Parsed JSON response as a dictionary, or empty dict on failure.
    """

    logger = logging.getLogger(__name__)
    logger.info("Querying jobs in %s - Page: %s...", origin, page)

    if not api_key:
        logger.error("Missing Serper API key")
        return {}

    headers = {"X-API-KEY": api_key, "Content-Type": "application/json"}
    payload = {"q": query, "num": 10, "page": page, "tbs": "qdr:w"}
    try:
        response = requests.post(SERPER_URL, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as exc:
        logger.error("Error fetching from %s page %s: %s", origin, page, exc)
        return {}


def build_ats_queries(technology: str = "php", level: str = "any") -> dict[str, str]:
    """Build ATS queries dynamically for a given technology and seniority level.

    Args:
        technology: Technology preset key from TECHNOLOGY_PRESETS.
        level: Seniority level key from SENIORITY_LEVELS.

    Returns:
        Dictionary mapping ATS names to their search queries.

    Raises:
        ValueError: If technology or level is not a valid preset key.
    """

    if technology not in TECHNOLOGY_PRESETS:
        raise ValueError(
            f"Unknown technology '{technology}'. Valid values: {sorted(TECHNOLOGY_PRESETS)}"
        )
    if level not in SENIORITY_LEVELS:
        raise ValueError(
            f"Unknown level '{level}'. Valid values: {sorted(SENIORITY_LEVELS)}"
        )

    tech_keywords = TECHNOLOGY_PRESETS[technology]
    level_keywords = SENIORITY_LEVELS[level]
    tech_string = " OR ".join(tech_keywords)
    level_string = " OR ".join(level_keywords)

    queries: dict[str, str] = {}
    for origin, site_prefix in ATS_PLATFORMS.items():
        parts = [site_prefix, '"remote"', tech_string]
        if origin == "PinpointHQ":
            queries[origin] = " ".join(parts)
            continue

        if level_string:
            parts.append(level_string)

        if origin != "ICIMS":
            parts.append('"LATAM" OR "global"')

        queries[origin] = " ".join(parts)

    return queries


def query_jobs(
    query: str,
    origin: str,
    api_key: str,
    target_min: int = 50,
    on_progress: ProgressCallback | None = None,
) -> list[dict[str, str]]:
    """Query job results from Serper across multiple pages.

    Args:
        query: Search query to execute.
        origin: ATS origin for progress reporting.
        api_key: Serper API key.
        target_min: Target minimum number of results to collect.
        on_progress: Optional progress callback.

    Returns:
        List of normalized job result dictionaries.
    """

    rows: list[dict[str, str]] = []
    seen_links: set[str] = set()
    page = 1
    max_pages = 5
    logger = logging.getLogger(__name__)

    while len(rows) < target_min and page <= max_pages:
        try:
            data = fetch_page(query, origin, page, api_key)
        except Exception as exc:
            logger.error("Error fetching page %s: %s", page, exc)
            _emit_progress(
                on_progress, "error", {"origin": origin, "message": str(exc)}
            )
            break

        organic_results = data.get("organic", [])
        _emit_progress(
            on_progress,
            "page_fetched",
            {"origin": origin, "page": page, "results": len(organic_results)},
        )

        if not organic_results:
            logger.info("No more results for %s", origin)
            break

        for result in organic_results:
            title = str(result.get("title", "")).strip()
            snippet = str(result.get("snippet", "")).strip()
            link = str(result.get("link", "")).strip()
            if link and link not in seen_links and is_valid_job_link(link, origin):
                seen_links.add(link)
                rows.append({"Job Title": title, "Snippet": snippet, "Link": link})

        time.sleep(1)
        page += 1

    return rows


def run_full_scrape(
    api_key: str,
    technology: str = "php",
    level: str = "any",
    on_progress: ProgressCallback | None = None,
) -> tuple[list[dict[str, str]], dict[str, int]]:
    """Run the full scrape across all configured ATS sources.

    Args:
        api_key: Serper API key.
        technology: Technology preset key.
        level: Seniority level key.
        on_progress: Optional progress callback.

    Returns:
        Tuple with list of all rows and per-origin counts.
    """

    queries = build_ats_queries(technology=technology, level=level)
    all_rows: list[dict[str, str]] = []
    stats: dict[str, int] = {}
    total = len(queries)

    for index, (origin, query) in enumerate(queries.items()):
        _emit_progress(
            on_progress,
            "ats_start",
            {"origin": origin, "index": index, "total": total},
        )

        rows = query_jobs(
            query=query,
            origin=origin,
            api_key=api_key,
            target_min=50,
            on_progress=on_progress,
        )
        all_rows.extend(rows)
        stats[origin] = len(rows)

        _emit_progress(
            on_progress,
            "ats_complete",
            {"origin": origin, "count": len(rows), "index": index, "total": total},
        )

        time.sleep(2)

    return all_rows, stats


def save_results_to_csv(
    results: Iterable[dict[str, str]],
    output_dir: str | Path,
    technology: str = "php",
    level: str = "any",
) -> Path:
    """Save job results to a date-stamped CSV file.

    Args:
        results: Iterable of job result dictionaries.
        output_dir: Directory to save the CSV file in.
        technology: Technology preset key.
        level: Seniority level key.

    Returns:
        Path to the created CSV file.
    """

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    date_stamp = datetime.now().strftime("%Y-%m-%d")
    filename = f"jobs_{technology}_{level}_{date_stamp}.csv"
    file_path = output_path / filename

    fieldnames = ["Job Title", "Snippet", "Link"]
    with file_path.open("w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for row in results:
            writer.writerow(row)

    return file_path
