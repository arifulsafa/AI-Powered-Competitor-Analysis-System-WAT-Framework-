#!/usr/bin/env python3
"""
discover_competitors.py
Finds 5-8 real competitors via Serper (Google Search API) based on the business profile.
Reads business_profile.json and saves discovered competitors to .tmp/competitors.json.

Usage:
    python tools/discover_competitors.py
"""

import json
import os
import sys
import time
from pathlib import Path
from urllib.parse import urlparse

import requests
from dotenv import load_dotenv

load_dotenv()

PROJECT_ROOT = Path(__file__).parent.parent
PROFILE_FILE = PROJECT_ROOT / "business_profile.json"
OUTPUT_FILE = PROJECT_ROOT / ".tmp" / "competitors.json"
SERPER_URL = "https://google.serper.dev/search"


def serper_search(query: str, api_key: str, num: int = 10) -> list[dict]:
    headers = {"X-API-KEY": api_key, "Content-Type": "application/json"}
    payload = {"q": query, "num": num}
    resp = requests.post(SERPER_URL, headers=headers, json=payload, timeout=15)
    resp.raise_for_status()
    return resp.json().get("organic", [])


def extract_domain(url: str) -> str:
    parsed = urlparse(url)
    domain = parsed.netloc.lower()
    if domain.startswith("www."):
        domain = domain[4:]
    return domain


def is_company_homepage(url: str, result_title: str) -> bool:
    """Basic heuristic: exclude review sites, directories, and news articles."""
    exclude_domains = {
        "g2.com", "trustpilot.com", "capterra.com", "getapp.com",
        "softwareadvice.com", "reddit.com", "quora.com", "linkedin.com",
        "twitter.com", "facebook.com", "youtube.com", "wikipedia.org",
        "forbes.com", "techcrunch.com", "inc.com", "entrepreneur.com",
        "alternativeto.net", "producthunt.com", "crunchbase.com",
        # Roundup/review/media sites
        "gartner.com", "pcmag.com", "theverge.com", "wired.com",
        "businessinsider.com", "tomsguide.com", "zdnet.com", "cnet.com",
        "thedigitalprojectmanager.com", "zapier.com", "clickup.com",
        "visible.vc", "salesforce.com", "zendesk.com", "spendesk.com",
        "hubspot.com", "monday.com", "asana.com", "trello.com",
        "nytimes.com", "medium.com", "substack.com",
    }
    domain = extract_domain(url)
    return domain not in exclude_domains


def build_queries(profile: dict) -> list[str]:
    name = profile.get("name", "")
    industry = profile.get("industry", "")
    target = profile.get("target_market", "")
    geo = profile.get("geography", "")

    queries = [
        f"best {industry} software for {target}",
        f"top {industry} companies {geo}",
        f"{industry} {target} alternatives",
    ]
    if name:
        queries.append(f"{name} competitors alternatives")

    return queries


def discover(profile: dict, api_key: str) -> list[dict]:
    queries = build_queries(profile)
    seen_domains: set[str] = set()
    competitors: list[dict] = []

    # Exclude the user's own domain if present
    own_domain = None
    if profile.get("name"):
        # We don't know their URL, but we can skip exact name matches in results
        own_name_lower = profile["name"].lower()
    else:
        own_name_lower = ""

    for query in queries:
        print(f"  Searching: {query}")
        results = serper_search(query, api_key)
        time.sleep(0.5)  # be polite

        for result in results:
            url = result.get("link", "")
            title = result.get("title", "")
            snippet = result.get("snippet", "")

            if not url or not is_company_homepage(url, title):
                continue

            domain = extract_domain(url)
            if domain in seen_domains:
                continue

            # Skip if the result looks like it's about the user's own company
            if own_name_lower and own_name_lower in title.lower():
                continue

            seen_domains.add(domain)
            competitors.append({
                "name": title.split(" - ")[0].split(" | ")[0].strip(),
                "url": f"https://{domain}",
                "snippet": snippet,
                "source_query": query,
            })

            if len(competitors) >= 8:
                break

        if len(competitors) >= 8:
            break

    return competitors


def main():
    if not PROFILE_FILE.exists():
        print("ERROR: business_profile.json not found. Run save_business_profile.py first.", file=sys.stderr)
        sys.exit(1)

    api_key = os.environ.get("SERPER_API_KEY")
    if not api_key:
        print("ERROR: SERPER_API_KEY not set in .env", file=sys.stderr)
        sys.exit(1)

    profile = json.loads(PROFILE_FILE.read_text())
    print(f"Finding competitors for: {profile.get('name', 'your business')} ({profile.get('industry', '')})")

    competitors = discover(profile, api_key)

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_FILE.write_text(json.dumps(competitors, indent=2))

    print(f"\nFound {len(competitors)} competitors:")
    for c in competitors:
        print(f"  - {c['name']} ({c['url']})")
    print(f"\nSaved to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
