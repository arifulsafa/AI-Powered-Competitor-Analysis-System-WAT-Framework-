#!/usr/bin/env python3
"""
save_business_profile.py
Parses a free-text business description and saves structured JSON to business_profile.json.
Uses Claude Haiku for structured extraction.

Usage:
    python tools/save_business_profile.py --description "We are a B2B SaaS company..."
"""

import argparse
import json
import os
import sys
from pathlib import Path

import anthropic
from dotenv import load_dotenv

load_dotenv()

PROJECT_ROOT = Path(__file__).parent.parent
OUTPUT_FILE = PROJECT_ROOT / "business_profile.json"

EXTRACTION_PROMPT = """Extract structured business information from the description below.

Return a JSON object with exactly these fields:
- name: company name (string, or null if not mentioned)
- industry: industry or sector (string)
- target_market: who the company serves (string)
- geography: markets or regions served (string)
- products: list of key products or services (array of strings)
- differentiators: unique selling points or competitive advantages (array of strings)
- known_competitors: any competitors explicitly mentioned (array of strings, empty if none)
- additional_context: anything else relevant for competitive research (string, or null)

Return ONLY the JSON object, no explanation or markdown.

Business description:
{description}"""


def extract_profile(description: str) -> dict:
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=1024,
        messages=[
            {
                "role": "user",
                "content": EXTRACTION_PROMPT.format(description=description),
            }
        ],
    )

    raw = message.content[0].text.strip()

    # Strip markdown code fences if present
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
        raw = raw.strip()

    return json.loads(raw)


def main():
    parser = argparse.ArgumentParser(description="Save business profile from description")
    parser.add_argument(
        "--description",
        required=True,
        help="Free-text description of your business",
    )
    args = parser.parse_args()

    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("ERROR: ANTHROPIC_API_KEY not set in .env", file=sys.stderr)
        sys.exit(1)

    print("Extracting business profile...")
    profile = extract_profile(args.description)

    OUTPUT_FILE.write_text(json.dumps(profile, indent=2))
    print(f"Saved to {OUTPUT_FILE}")
    print(json.dumps(profile, indent=2))


if __name__ == "__main__":
    main()
