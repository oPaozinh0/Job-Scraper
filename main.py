"""
Job Scraper - Remote Positions

This script searches for remote jobs across multiple ATS platforms.

Configuration:
- Runs once per week
- Searches only jobs from the past 7 days (tbs: "qdr:w")
- Filters only legitimate job boards
- Saves results to CSV

Usage:
    python main.py --technology php --level senior
    python main.py -t python -l mid

Requests:
- Uses Google Serper API (2420 free requests/month)
- Approximately 80 requests per run
- ~26 runs per month

Scheduling (Windows Task Scheduler):
    python C:\\path\\main.py --technology php --level senior
    (Schedule to run every Monday at 9:00 AM)

Scheduling (Linux/Mac - Cron):
    0 9 * * 1 python /path/main.py --technology php --level senior
    (Every Monday at 9:00 AM UTC)
"""

import argparse
import logging
from datetime import datetime
from pathlib import Path

from decouple import config

from scraper import (
    SENIORITY_LEVELS,
    TECHNOLOGY_PRESETS,
    run_full_scrape,
    save_results_to_csv,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Job Scraper CLI - Search remote jobs across 9 ATS platforms"
    )
    parser.add_argument(
        "-t",
        "--technology",
        default="php",
        choices=TECHNOLOGY_PRESETS.keys(),
        help="Technology preset to search",
    )
    parser.add_argument(
        "-l",
        "--level",
        default="any",
        choices=SENIORITY_LEVELS.keys(),
        help="Seniority level to filter",
    )
    args = parser.parse_args()

    logging.info("Service started")
    logging.info(f"Execution time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    SERPER_API_KEY = str(config('SERPAPI_API_KEY_1'))

    logging.info(
        "Searching for jobs (past week only) | technology=%s | level=%s",
        args.technology,
        args.level,
    )

    results, stats = run_full_scrape(
        SERPER_API_KEY,
        technology=args.technology,
        level=args.level,
    )

    for origin, count in stats.items():
        logging.info(f"Found {count} results from {origin}")

    output_dir = Path(__file__).resolve().parent
    csv_path = save_results_to_csv(
        results,
        output_dir,
        technology=args.technology,
        level=args.level,
    )

    logging.info(f"Saved {len(results)} rows to {csv_path}")
    logging.info("=" * 70)
