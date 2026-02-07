import http.client
import json
import csv
import time
import logging

from decouple import config

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

logging.info("Service started - TEST MODE")

# CONFIGURATION — Google Serper API
SERPER_API_KEY = config('SERPAPI_API_KEY_1')
SERPER_HOST = "google.serper.dev"

# Test with only 2 ATS platforms and 1 page each to save requests
test_queries = {
    "Lever": 'site:lever.co "remote" "PHP" OR "Laravel" "Senior" OR "Mid-Level" "LATAM" OR "global"',
    "Workable": 'site:jobs.workable.com "remote" "PHP" OR "Laravel" "Senior" OR "Mid-Level" "LATAM" OR "global"',
}

def fetch_page(query: str, origin: str, page: int = 1):
    """Fetch results from Google Serper API."""
    logging.info(f"Querying jobs in {origin} - Page: {page}...")
    
    try:
        conn = http.client.HTTPSConnection(SERPER_HOST)
        payload = json.dumps({
            "q": query,
            "num": 10,
            "page": page
        })
        headers = {
            'X-API-KEY': SERPER_API_KEY,
            'Content-Type': 'application/json'
        }
        
        conn.request("POST", "/search", payload, headers)
        res = conn.getresponse()
        data = res.read()
        return json.loads(data.decode("utf-8"))
    except Exception as e:
        logging.error(f"Error fetching from {origin} page {page}: {e}")
        return {}

def query_jobs(query: str, origin: str, max_pages=1):
    """Query jobs from Google Serper API with pagination - LIMITED TO TEST"""
    rows = []
    seen_links = set()
    page = 1

    while page <= max_pages:
        try:
            data = fetch_page(query, origin, page)
        except Exception as e:
            logging.error(f"Error fetching page {page}: {e}")
            break

        organic_results = data.get("organic", [])
        if not organic_results:
            logging.info(f"No more results for {origin}")
            break

        for result in organic_results:
            title = result.get("title", "").strip()
            snippet = result.get("snippet", "").strip()
            link = result.get("link", "").strip()

            if link and link not in seen_links:
                seen_links.add(link)
                rows.append({
                    "Job Title": title,
                    "Snippet": snippet,
                    "Link": link
                })

        # Gentle pause to avoid hitting rate limits
        time.sleep(1)
        page += 1

    return rows

if __name__ == "__main__":
    outfile = "test_results.csv"
    results = []

    logging.info("TEST: Searching for jobs with limited pages...")
    for origin, query in test_queries.items():
        rows = query_jobs(query, origin, max_pages=1)  # Only 1 page per site
        results.extend(rows)
        logging.info(f"Found {len(rows)} results from {origin}")
        time.sleep(2)

    logging.info(f"Saving {len(results)} results to csv...")
    # Write CSV
    with open(outfile, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["Job Title", "Snippet", "Link"])
        writer.writeheader()
        writer.writerows(results)
    
    logging.info(f"Saved {len(results)} rows to {outfile}")

    # Print analysis
    print("\n=== ANÁLISE DOS RESULTADOS ===\n")
    for i, row in enumerate(results[:10], 1):
        print(f"Resultado {i}:")
        print(f"  Title: {row['Job Title'][:70]}")
        print(f"  Snippet: {row['Snippet'][:100]}")
        print(f"  Link: {row['Link']}\n")
