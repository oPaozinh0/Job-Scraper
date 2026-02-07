"""Flask server for Job Scraper frontend and APIs."""

from __future__ import annotations

import csv
import json
import logging
import threading
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse

import requests
from decouple import config
from flask import Flask, Response, jsonify, render_template, request

from scraper import (
    SENIORITY_LEVELS,
    TECHNOLOGY_PRESETS,
    run_full_scrape,
    save_results_to_csv,
)


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent
SCRAPE_URL = "https://scrape.serper.dev"
SERPER_API_KEY = str(config("SERPAPI_API_KEY_1"))

# Simple cache to avoid re-reading CSV on every request
_csv_cache: Dict[str, Any] = {"path": None, "mtime": 0.0, "data": []}

_scrape_lock = threading.Lock()
_scrape_status: Dict[str, Any] = {
    "running": False,
    "events": [],
    "completed": False,
}

ORIGIN_MAP: Dict[str, str] = {
    "greenhouse.io": "Greenhouse",
    "lever.co": "Lever",
    "ashbyhq.com": "AshBy",
    "workable.com": "Workable",
    "breezy.hr": "Breezy",
    "jazz.co": "Jazz CO",
    "smartrecruiters.com": "Smart Recruiters",
    "icims.com": "ICIMS",
    "pinpointhq.com": "PinpointHQ",
}


def get_latest_csv() -> str:
    """Find the most recent CSV file in the project directory."""
    try:
        dated_files = sorted(
            BASE_DIR.glob("jobs_*_*_*.csv"),
            key=lambda path: path.stat().st_mtime,
            reverse=True,
        )
        if dated_files:
            return str(dated_files[0])

        # Legacy fallback for old format
        legacy_files = sorted(
            BASE_DIR.glob("php_backend_jobs_*.csv"),
            key=lambda path: path.stat().st_mtime,
            reverse=True,
        )
        if legacy_files:
            return str(legacy_files[0])

        fallback = BASE_DIR / "php_backend_jobs.csv"
        if fallback.exists():
            return str(fallback)

        raise FileNotFoundError("No CSV file found in project directory.")
    except FileNotFoundError:
        raise
    except Exception as exc:
        logger.error("Error locating CSV: %s", exc)
        raise


def detect_origin(link: str) -> str:
    """Detect the job origin based on the link domain."""
    try:
        netloc = urlparse(link).netloc.lower()
        if netloc.startswith("www."):
            netloc = netloc[4:]

        for domain, origin in ORIGIN_MAP.items():
            if netloc.endswith(domain):
                return origin
    except Exception as exc:
        logger.warning("Error detecting origin for link '%s': %s", link, exc)

    return "Unknown"


def load_jobs(csv_path: str) -> List[Dict[str, str]]:
    """Load jobs from CSV and infer origin by domain."""
    jobs: List[Dict[str, str]] = []
    try:
        with open(csv_path, "r", encoding="utf-8", newline="") as file:
            reader = csv.DictReader(file)
            for row in reader:
                title = (row.get("Job Title") or "").strip()
                snippet = (row.get("Snippet") or "").strip()
                link = (row.get("Link") or "").strip()
                origin = detect_origin(link)
                jobs.append(
                    {
                        "title": title,
                        "snippet": snippet,
                        "link": link,
                        "origin": origin,
                    }
                )
    except Exception as exc:
        logger.error("Error reading CSV '%s': %s", csv_path, exc)
        raise

    return jobs


def load_jobs_cached(csv_path: str) -> List[Dict[str, str]]:
    """Load jobs with cache; re-read only if the file changes."""
    try:
        mtime = Path(csv_path).stat().st_mtime
    except OSError:
        mtime = 0.0

    if _csv_cache["path"] == csv_path and _csv_cache["mtime"] == mtime:
        logger.info("Using cache for %s", csv_path)
        return _csv_cache["data"]

    logger.info("Reading CSV and refreshing cache: %s", csv_path)
    data = load_jobs(csv_path)
    _csv_cache["path"] = csv_path
    _csv_cache["mtime"] = mtime
    _csv_cache["data"] = data
    return data


def apply_filters(
    jobs: List[Dict[str, str]],
    origin: str | None,
    search: str | None,
) -> List[Dict[str, str]]:
    """Apply origin and title search filters."""
    filtered = jobs
    if origin:
        origin_lower = origin.lower()
        filtered = [job for job in filtered if job["origin"].lower() == origin_lower]

    if search:
        search_lower = search.lower()
        filtered = [
            job
            for job in filtered
            if search_lower in job["title"].lower()
        ]

    return filtered


def count_origins(jobs: List[Dict[str, str]]) -> List[Dict[str, Any]]:
    """Count jobs by origin and sort by volume."""
    counts: Dict[str, int] = {}
    for job in jobs:
        origin = job["origin"]
        counts[origin] = counts.get(origin, 0) + 1

    ordered = sorted(counts.items(), key=lambda item: item[1], reverse=True)
    return [{"name": name, "count": count} for name, count in ordered]


def build_serper_payload(url: str) -> Tuple[Dict[str, Any], Dict[str, str]]:
    """Build payload and headers for Serper Scrape."""
    payload = {"url": url, "includeMarkdown": True}
    headers = {
        "X-API-KEY": SERPER_API_KEY,
        "Content-Type": "application/json",
    }
    return payload, headers


def _run_scrape_background(technology: str = "php", level: str = "any") -> None:
    """Run full scrape in background with SSE events."""

    def on_progress(event: str, data: dict) -> None:
        with _scrape_lock:
            _scrape_status["events"].append({"event": event, **data})

    try:
        results, stats = run_full_scrape(
            SERPER_API_KEY, technology=technology, level=level, on_progress=on_progress
        )
        csv_path = save_results_to_csv(
            results, BASE_DIR, technology=technology, level=level
        )
        _csv_cache["path"] = None
        _csv_cache["mtime"] = 0.0
        _csv_cache["data"] = []
        with _scrape_lock:
            _scrape_status["events"].append(
                {
                    "event": "complete",
                    "total_jobs": len(results),
                    "file": Path(csv_path).name,
                    "origins": stats,
                }
            )
    except Exception as exc:
        logger.error("Scrape failed: %s", exc)
        with _scrape_lock:
            _scrape_status["events"].append({"event": "error", "message": str(exc)})
    finally:
        with _scrape_lock:
            _scrape_status["running"] = False
            _scrape_status["completed"] = True


app = Flask(__name__, template_folder="templates")


@app.get("/")
def index() -> str:
    """Render the main template."""
    return render_template("index.html")


@app.get("/api/jobs")
def list_jobs() -> Any:
    """List jobs with optional origin and search filters."""
    try:
        origin = request.args.get("origin")
        search = request.args.get("search")
        csv_path = get_latest_csv()
        jobs = load_jobs_cached(csv_path)
        filtered = apply_filters(jobs, origin, search)
        return jsonify({"jobs": filtered, "total": len(filtered), "file": Path(csv_path).name})
    except Exception as exc:
        logger.error("Error in /api/jobs: %s", exc)
        return jsonify({"error": "Failed to list jobs"}), 500


@app.get("/api/origins")
def list_origins() -> Any:
    """List origins with job counts."""
    try:
        csv_path = get_latest_csv()
        jobs = load_jobs_cached(csv_path)
        origins = count_origins(jobs)
        return jsonify({"origins": origins})
    except Exception as exc:
        logger.error("Error in /api/origins: %s", exc)
        return jsonify({"error": "Failed to list origins"}), 500


@app.get("/api/technologies")
def list_technologies() -> Any:
    """Return available technology presets."""
    technologies = [
        {
            "key": key,
            "label": key.replace("csharp", "C#").title(),
            "keywords": keywords,
        }
        for key, keywords in TECHNOLOGY_PRESETS.items()
    ]
    return jsonify({"technologies": technologies})


@app.get("/api/levels")
def list_levels() -> Any:
    """Return available seniority levels."""
    levels = [
        {
            "key": key,
            "label": key.title() if key != "any" else "Any Level",
            "keywords": keywords,
        }
        for key, keywords in SENIORITY_LEVELS.items()
    ]
    return jsonify({"levels": levels})


@app.post("/api/scrape")
def scrape_job() -> Any:
    """Scrape a job description via Serper Scrape API."""
    try:
        data = request.get_json(silent=True) or {}
        url = data.get("url", "").strip()
        if not url:
            return jsonify({"error": "URL is required"}), 400

        payload, headers = build_serper_payload(url)
        response = requests.post(
            SCRAPE_URL,
            headers=headers,
            json=payload,
            timeout=30,
        )
        response.raise_for_status()
        content = response.json()

        return jsonify(
            {
                "markdown": content.get("markdown", ""),
                "text": content.get("text", ""),
            }
        )
    except requests.RequestException as exc:
        logger.error("Serper request error: %s", exc)
        return jsonify({"error": "Scrape failed"}), 500
    except Exception as exc:
        logger.error("Error in /api/scrape: %s", exc)
        return jsonify({"error": "Scrape failed"}), 500


@app.post("/api/fetch-jobs")
def fetch_jobs() -> Any:
    """Start full scrape and return streaming URL."""
    with _scrape_lock:
        if _scrape_status["running"]:
            return jsonify({"error": "Scrape already running"}), 409
        _scrape_status["running"] = True
        _scrape_status["completed"] = False
        _scrape_status["events"] = []

    data = request.get_json(silent=True) or {}
    technology = data.get("technology", "php")
    level = data.get("level", "any")

    if technology not in TECHNOLOGY_PRESETS:
        with _scrape_lock:
            _scrape_status["running"] = False
        return jsonify({"error": f"Invalid technology: {technology}"}), 400
    if level not in SENIORITY_LEVELS:
        with _scrape_lock:
            _scrape_status["running"] = False
        return jsonify({"error": f"Invalid level: {level}"}), 400

    thread = threading.Thread(
        target=_run_scrape_background, args=(technology, level), daemon=True
    )
    thread.start()
    return jsonify({"status": "started", "stream_url": "/api/fetch-jobs/stream"})


SSE_TIMEOUT_SECONDS = 600  # 10 minutes max for SSE stream


@app.get("/api/fetch-jobs/stream")
def stream_fetch_jobs() -> Any:
    """SSE endpoint that streams scrape progress.

    This endpoint only reads events; the scrape must be started
    via POST /api/fetch-jobs before connecting here.

    Returns 204 if no scrape is active and no events exist.
    Includes a safety timeout to prevent infinite loops.
    """
    with _scrape_lock:
        has_events = bool(_scrape_status["events"])
        is_running = _scrape_status["running"]
        is_completed = _scrape_status["completed"]

    if not has_events and not is_running and not is_completed:
        return jsonify({"error": "No active scrape. Start one via POST /api/fetch-jobs"}), 409

    def generate():
        last_index = 0
        start_time = time.monotonic()
        while True:
            elapsed = time.monotonic() - start_time
            if elapsed > SSE_TIMEOUT_SECONDS:
                yield f"data: {json.dumps({'event': 'error', 'message': 'SSE stream timed out after 10 minutes'})}\n\n"
                return

            with _scrape_lock:
                events = list(_scrape_status["events"])
                running = _scrape_status["running"]

            # Handle reset/new scrape: events list was cleared while streaming
            if len(events) < last_index:
                last_index = 0

            while last_index < len(events):
                event_data = events[last_index]
                yield f"data: {json.dumps(event_data)}\n\n"
                last_index += 1
                if event_data.get("event") in ("complete", "error"):
                    return

            # If scrape finished but no terminal event, exit to avoid infinite loop
            if not running and last_index >= len(events):
                yield f"data: {json.dumps({'event': 'error', 'message': 'Scrape ended without terminal event'})}\n\n"
                return

            time.sleep(0.5)

    return Response(
        generate(),
        mimetype="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@app.get("/api/fetch-jobs/status")
def fetch_jobs_status() -> Any:
    """Return current status of the full scrape."""
    with _scrape_lock:
        return jsonify(
            {
                "running": _scrape_status["running"],
                "completed": _scrape_status["completed"],
                "events_count": len(_scrape_status["events"]),
            }
        )


@app.post("/api/fetch-jobs/reset")
def fetch_jobs_reset() -> Any:
    """Reset scrape status to allow a new run."""
    with _scrape_lock:
        _scrape_status["running"] = False
        _scrape_status["completed"] = False
        _scrape_status["events"] = []
    return jsonify({"status": "reset"})


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8000, debug=True, use_reloader=False)
