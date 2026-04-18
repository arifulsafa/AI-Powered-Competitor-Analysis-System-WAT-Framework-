#!/usr/bin/env python3
"""
research_competitor.py
Researches a single competitor across four dimensions:
  1. Website & messaging
  2. Pricing & offers
  3. Reviews & reputation
  4. Content & SEO

Saves results to .tmp/research/<competitor_name>.json.

Usage:
    python tools/research_competitor.py --name "Acme" --url "https://acme.com"
"""

import argparse
import json
import os
import re
import sys
import time
from pathlib import Path
from urllib.parse import urljoin, urlparse

import anthropic
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

load_dotenv()

PROJECT_ROOT = Path(__file__).parent.parent
RESEARCH_DIR = PROJECT_ROOT / ".tmp" / "research"
SERPER_URL = "https://google.serper.dev/search"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
}


# ── Helpers ──────────────────────────────────────────────────────────────────

def fetch_page(url: str, timeout: int = 10) -> str | None:
    try:
        resp = requests.get(url, headers=HEADERS, timeout=timeout, allow_redirects=True)
        resp.raise_for_status()
        return resp.text
    except Exception as e:
        print(f"    [warn] Could not fetch {url}: {e}")
        return None


def extract_text(html: str, max_chars: int = 4000) -> str:
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "nav", "footer", "header"]):
        tag.decompose()
    text = " ".join(soup.get_text(separator=" ").split())
    return text[:max_chars]


def serper_search(query: str, api_key: str, num: int = 5) -> list[dict]:
    headers = {"X-API-KEY": api_key, "Content-Type": "application/json"}
    payload = {"q": query, "num": num}
    try:
        resp = requests.post(SERPER_URL, headers=headers, json=payload, timeout=15)
        resp.raise_for_status()
        return resp.json().get("organic", [])
    except Exception as e:
        print(f"    [warn] Serper search failed for '{query}': {e}")
        return []


def summarize(client: anthropic.Anthropic, prompt: str) -> list[str]:
    """Ask Claude Haiku to summarize content into bullet points."""
    msg = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=512,
        messages=[{"role": "user", "content": prompt}],
    )
    raw = msg.content[0].text.strip()
    # Parse bullet points (lines starting with - or •)
    bullets = [
        line.lstrip("-•* ").strip()
        for line in raw.splitlines()
        if line.strip().startswith(("-", "•", "*"))
    ]
    return bullets if bullets else [raw]


# ── Dimension 1: Website & Messaging ─────────────────────────────────────────

def research_website(name: str, url: str, claude: anthropic.Anthropic) -> dict:
    print("  [1/4] Website & messaging...")
    html = fetch_page(url)
    if not html:
        return {"bullets": ["Could not access website"], "raw": ""}

    text = extract_text(html)
    prompt = f"""You are analyzing the homepage of {name} for a competitive intelligence report.

Homepage text (truncated):
{text}

Summarize in 4-5 bullet points:
- Their main value proposition / headline message
- Who they are targeting
- Key features or benefits they highlight
- Their primary call to action
- Overall tone and positioning (premium, affordable, technical, friendly, etc.)

Use bullet points starting with -"""

    bullets = summarize(claude, prompt)
    return {"bullets": bullets, "raw": text[:500]}


# ── Dimension 2: Pricing & Offers ────────────────────────────────────────────

def research_pricing(name: str, base_url: str, claude: anthropic.Anthropic) -> dict:
    print("  [2/4] Pricing & offers...")
    pricing_url = urljoin(base_url.rstrip("/") + "/", "pricing")
    html = fetch_page(pricing_url)

    if not html:
        return {"bullets": ["Pricing page not publicly accessible"], "raw": ""}

    text = extract_text(html, max_chars=3000)

    # Quick check: if the page doesn't mention pricing-related words, skip
    pricing_keywords = ["price", "plan", "month", "year", "free", "$", "€", "£", "per user", "contact us"]
    if not any(kw in text.lower() for kw in pricing_keywords):
        return {"bullets": ["Pricing details not found on /pricing page — may require login or contact"], "raw": ""}

    prompt = f"""You are analyzing the pricing page of {name} for a competitive intelligence report.

Pricing page text (truncated):
{text}

Summarize in 4-5 bullet points:
- Pricing model (per seat, flat rate, usage-based, freemium, etc.)
- Price tiers or plans and their approximate costs if shown
- What's included in each tier (key differences)
- Free trial or free tier availability
- Any notable pricing strategy (e.g., "contact sales" for enterprise)

Use bullet points starting with -"""

    bullets = summarize(claude, prompt)
    return {"bullets": bullets, "raw": text[:500]}


# ── Dimension 3: Reviews & Reputation ────────────────────────────────────────

def research_reviews(name: str, url: str, serper_key: str, claude: anthropic.Anthropic) -> dict:
    print("  [3/4] Reviews & reputation...")
    domain = urlparse(url).netloc.replace("www.", "")
    query = f'"{name}" reviews site:g2.com OR site:trustpilot.com OR site:reddit.com OR site:capterra.com'

    results = serper_search(query, serper_key, num=6)
    time.sleep(0.5)

    snippets = []
    for r in results:
        title = r.get("title", "")
        snippet = r.get("snippet", "")
        source = urlparse(r.get("link", "")).netloc.replace("www.", "")
        if snippet:
            snippets.append(f"[{source}] {title}: {snippet}")

    if not snippets:
        return {"bullets": ["No public reviews found in search results"], "raw": ""}

    combined = "\n".join(snippets)
    prompt = f"""You are analyzing customer reviews of {name} for a competitive intelligence report.

Review snippets from search results:
{combined}

Summarize in 4-5 bullet points:
- Overall sentiment and typical star rating if mentioned
- Most common praise from customers
- Most common complaints or weaknesses
- Types of customers who seem to love it
- Any notable reputation issues or strengths

Use bullet points starting with -"""

    bullets = summarize(claude, prompt)
    return {"bullets": bullets, "raw": combined[:500]}


# ── Dimension 4: Content & SEO ────────────────────────────────────────────────

def research_content_seo(name: str, url: str, serper_key: str, claude: anthropic.Anthropic) -> dict:
    print("  [4/4] Content & SEO...")
    domain = urlparse(url).netloc.replace("www.", "")

    # Check if they have a blog
    blog_results = serper_search(f"site:{domain} blog", serper_key, num=5)
    time.sleep(0.5)

    # Check their ranking presence
    rank_results = serper_search(f"{name} {domain}", serper_key, num=5)
    time.sleep(0.5)

    blog_titles = [r.get("title", "") for r in blog_results if r.get("title")]
    rank_snippets = [f"{r.get('title', '')}: {r.get('snippet', '')}" for r in rank_results[:3]]

    combined = (
        f"Blog content found: {'; '.join(blog_titles[:5]) if blog_titles else 'No blog content found'}\n"
        f"Search presence: {chr(10).join(rank_snippets)}"
    )

    prompt = f"""You are analyzing the content strategy and SEO presence of {name} for a competitive intelligence report.

Data gathered:
{combined}

Summarize in 4-5 bullet points:
- Whether they have an active blog or content marketing presence
- What topics or themes their content focuses on
- Their apparent SEO strategy (thought leadership, product-focused, educational, etc.)
- Estimated content volume (prolific, moderate, minimal)
- Any content gaps or strengths worth noting

Use bullet points starting with -"""

    bullets = summarize(claude, prompt)
    return {"bullets": bullets, "raw": combined[:500]}


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Research a single competitor")
    parser.add_argument("--name", required=True, help="Competitor name")
    parser.add_argument("--url", required=True, help="Competitor homepage URL")
    args = parser.parse_args()

    anthropic_key = os.environ.get("ANTHROPIC_API_KEY")
    serper_key = os.environ.get("SERPER_API_KEY")

    if not anthropic_key:
        print("ERROR: ANTHROPIC_API_KEY not set in .env", file=sys.stderr)
        sys.exit(1)
    if not serper_key:
        print("ERROR: SERPER_API_KEY not set in .env", file=sys.stderr)
        sys.exit(1)

    claude = anthropic.Anthropic(api_key=anthropic_key)
    name = args.name
    url = args.url.rstrip("/")

    print(f"\nResearching: {name} ({url})")

    result = {
        "name": name,
        "url": url,
        "website_messaging": research_website(name, url, claude),
        "pricing": research_pricing(name, url, claude),
        "reviews": research_reviews(name, url, serper_key, claude),
        "content_seo": research_content_seo(name, url, serper_key, claude),
    }

    RESEARCH_DIR.mkdir(parents=True, exist_ok=True)
    safe_name = re.sub(r"[^\w\-]", "_", name.lower())
    output_file = RESEARCH_DIR / f"{safe_name}.json"
    output_file.write_text(json.dumps(result, indent=2))

    print(f"\nSaved to {output_file}")


if __name__ == "__main__":
    main()
