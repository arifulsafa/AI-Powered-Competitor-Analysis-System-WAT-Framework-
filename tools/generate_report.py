#!/usr/bin/env python3
"""
generate_report.py
Compiles all competitor research into a branded PDF report.
Reads: business_profile.json, brand/brand_guide.md, brand/logo.png, .tmp/research/*.json
Writes: .tmp/reports/competitor_analysis_YYYY-MM-DD.pdf

Usage:
    python tools/generate_report.py
"""

import base64
import json
import os
import sys
from datetime import date
from pathlib import Path

import anthropic
import yaml
from dotenv import load_dotenv
from jinja2 import Environment, BaseLoader

load_dotenv()

PROJECT_ROOT = Path(__file__).parent.parent
PROFILE_FILE = PROJECT_ROOT / "business_profile.json"
BRAND_GUIDE_FILE = PROJECT_ROOT / "brand" / "brand_guide.md"
RESEARCH_DIR = PROJECT_ROOT / ".tmp" / "research"
REPORTS_DIR = PROJECT_ROOT / ".tmp" / "reports"


# ── Brand guide parser ────────────────────────────────────────────────────────

def load_brand_guide() -> dict:
    """Parse the YAML-style brand_guide.md into a dict."""
    if not BRAND_GUIDE_FILE.exists():
        print("WARNING: brand/brand_guide.md not found — using defaults")
        return {
            "primary": "#1A1A2E",
            "secondary": "#E94560",
            "background": "#FFFFFF",
            "text": "#333333",
            "accent": "#F5F5F5",
            "heading_font": "Inter",
            "body_font": "Inter",
            "logo_file": "brand/logo.png",
            "logo_position": "top-left",
            "logo_height": 60,
        }

    lines = BRAND_GUIDE_FILE.read_text().splitlines()
    flat: dict = {}
    for line in lines:
        if ":" in line and not line.startswith("#"):
            key, _, value = line.partition(":")
            key = key.strip().replace(" ", "_")
            value = value.split("#")[0].strip().strip('"').strip("'")
            flat[key] = value

    return {
        "primary": flat.get("primary", "#1A1A2E"),
        "secondary": flat.get("secondary", "#E94560"),
        "background": flat.get("background", "#FFFFFF"),
        "text": flat.get("text", "#333333"),
        "accent": flat.get("accent", "#F5F5F5"),
        "heading_font": flat.get("heading_font", "Inter"),
        "body_font": flat.get("body_font", "Inter"),
        "logo_file": flat.get("file", "brand/logo.png"),
        "logo_position": flat.get("position", "top-left"),
        "logo_height": int(flat.get("height", 60)),
    }


def load_logo_b64(brand: dict) -> str | None:
    logo_path = PROJECT_ROOT / brand["logo_file"]
    if not logo_path.exists():
        return None
    with open(logo_path, "rb") as f:
        data = base64.b64encode(f.read()).decode()
    suffix = logo_path.suffix.lower().lstrip(".")
    mime = "svg+xml" if suffix == "svg" else suffix
    return f"data:image/{mime};base64,{data}"


# ── AI-generated sections ─────────────────────────────────────────────────────

def generate_executive_summary(
    client: anthropic.Anthropic,
    profile: dict,
    competitors: list[dict],
) -> str:
    names = ", ".join(c["name"] for c in competitors)
    prompt = f"""Write a 2-3 sentence executive summary for a competitor analysis report.

Business being analyzed: {profile.get('name', 'the company')} — {profile.get('industry', '')} serving {profile.get('target_market', '')}.
Competitors analyzed: {names}

The summary should note the competitive landscape briefly and hint at what the report covers.
Write in professional business prose. No bullet points."""

    msg = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=256,
        messages=[{"role": "user", "content": prompt}],
    )
    return msg.content[0].text.strip()


def generate_opportunities(
    client: anthropic.Anthropic,
    profile: dict,
    competitors: list[dict],
) -> list[str]:
    all_bullets = []
    for c in competitors:
        for dim in ["website_messaging", "pricing", "reviews", "content_seo"]:
            bullets = c.get(dim, {}).get("bullets", [])
            all_bullets.extend(f"[{c['name']} - {dim}] {b}" for b in bullets)

    combined = "\n".join(all_bullets[:40])
    prompt = f"""Based on this competitive intelligence data, identify the top 3 actionable opportunities for {profile.get('name', 'the company')} to improve or differentiate.

Intelligence gathered:
{combined}

Format as exactly 3 bullet points, each starting with -. Each bullet should be a concrete, actionable insight — not generic advice."""

    msg = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=400,
        messages=[{"role": "user", "content": prompt}],
    )
    raw = msg.content[0].text.strip()
    bullets = [
        line.lstrip("-•* ").strip()
        for line in raw.splitlines()
        if line.strip().startswith(("-", "•", "*"))
    ]
    return bullets[:3] if bullets else [raw]


# ── HTML template ─────────────────────────────────────────────────────────────

REPORT_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<style>
  @import url('https://fonts.googleapis.com/css2?family={{ brand.heading_font | replace(' ', '+') }}:wght@400;600;700&family={{ brand.body_font | replace(' ', '+') }}:wght@400;500&display=swap');

  :root {
    --primary:    {{ brand.primary }};
    --secondary:  {{ brand.secondary }};
    --background: {{ brand.background }};
    --text:       {{ brand.text }};
    --accent:     {{ brand.accent }};
  }

  * { box-sizing: border-box; margin: 0; padding: 0; }

  body {
    font-family: '{{ brand.body_font }}', sans-serif;
    background: var(--background);
    color: var(--text);
    font-size: 10pt;
    line-height: 1.6;
  }

  /* ── Header ── */
  .report-header {
    background: var(--primary);
    color: #fff;
    padding: 28px 36px;
    display: flex;
    align-items: center;
    justify-content: {% if brand.logo_position == 'top-right' %}space-between{% elif brand.logo_position == 'top-center' %}center{% else %}space-between{% endif %};
    flex-direction: {% if brand.logo_position == 'top-center' %}column{% else %}row{% endif %};
    gap: 12px;
  }

  .header-text h1 {
    font-family: '{{ brand.heading_font }}', sans-serif;
    font-size: 22pt;
    font-weight: 700;
    letter-spacing: -0.5px;
  }

  .header-text .subtitle {
    font-size: 9pt;
    opacity: 0.75;
    margin-top: 4px;
  }

  .logo img {
    height: {{ brand.logo_height }}px;
    {% if brand.logo_position == 'top-right' %}order: 2;{% endif %}
  }

  /* ── Body ── */
  .content { padding: 32px 36px; }

  .section {
    margin-bottom: 32px;
  }

  h2 {
    font-family: '{{ brand.heading_font }}', sans-serif;
    font-size: 14pt;
    font-weight: 700;
    color: var(--primary);
    border-bottom: 2px solid var(--secondary);
    padding-bottom: 6px;
    margin-bottom: 14px;
  }

  h3 {
    font-family: '{{ brand.heading_font }}', sans-serif;
    font-size: 11pt;
    font-weight: 600;
    color: var(--primary);
    margin-bottom: 8px;
  }

  p { margin-bottom: 10px; }

  /* ── Competitor cards ── */
  .competitor-block {
    background: var(--accent);
    border-left: 4px solid var(--secondary);
    border-radius: 4px;
    padding: 16px 20px;
    margin-bottom: 20px;
  }

  .competitor-block h3 {
    font-size: 12pt;
    margin-bottom: 4px;
  }

  .competitor-url {
    font-size: 8pt;
    color: var(--secondary);
    margin-bottom: 12px;
  }

  /* Use table layout instead of grid — WeasyPrint handles tables reliably */
  .dimensions { width: 100%; border-collapse: separate; border-spacing: 8px; display: table; }
  .dimensions-row { display: table-row; }

  .dim-card {
    display: table-cell;
    width: 50%;
    background: white;
    border-radius: 4px;
    padding: 12px 14px;
    border: 1px solid #e0e0e0;
    vertical-align: top;
  }

  .dim-title {
    font-family: '{{ brand.heading_font }}', sans-serif;
    font-size: 8pt;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    color: var(--secondary);
    margin-bottom: 8px;
  }

  ul { padding-left: 16px; }
  ul li { margin-bottom: 4px; font-size: 9pt; }

  /* ── Opportunities ── */
  .opportunities-list li {
    background: var(--accent);
    border-left: 3px solid var(--secondary);
    padding: 8px 12px;
    margin-bottom: 8px;
    list-style: none;
    border-radius: 2px;
    font-size: 10pt;
  }

  /* ── Footer ── */
  .report-footer {
    background: var(--accent);
    border-top: 2px solid var(--primary);
    padding: 12px 36px;
    font-size: 8pt;
    color: #888;
    display: flex;
    justify-content: space-between;
  }
</style>
</head>
<body>

<!-- Header -->
<div class="report-header">
  {% if logo_b64 and brand.logo_position != 'top-right' %}
  <div class="logo"><img src="{{ logo_b64 }}" alt="Logo"></div>
  {% endif %}
  <div class="header-text">
    <h1>Competitor Analysis Report</h1>
    <div class="subtitle">{{ profile.name }} &nbsp;·&nbsp; Generated {{ report_date }}</div>
  </div>
  {% if logo_b64 and brand.logo_position == 'top-right' %}
  <div class="logo"><img src="{{ logo_b64 }}" alt="Logo"></div>
  {% endif %}
</div>

<div class="content">

  <!-- Executive Summary -->
  <div class="section">
    <h2>Executive Summary</h2>
    <p>{{ executive_summary }}</p>
  </div>

  <!-- Competitors -->
  <div class="section">
    <h2>Competitor Profiles</h2>
    {% for c in competitors %}
    <div class="competitor-block">
      <h3>{{ c.name }}</h3>
      <div class="competitor-url">{{ c.url }}</div>
      <div class="dimensions">
        <div class="dimensions-row">
          <div class="dim-card">
            <div class="dim-title">Website &amp; Messaging</div>
            <ul>{% for b in c.website_messaging.bullets %}<li>{{ b }}</li>{% endfor %}</ul>
          </div>
          <div class="dim-card">
            <div class="dim-title">Pricing &amp; Offers</div>
            <ul>{% for b in c.pricing.bullets %}<li>{{ b }}</li>{% endfor %}</ul>
          </div>
        </div>
        <div class="dimensions-row">
          <div class="dim-card">
            <div class="dim-title">Reviews &amp; Reputation</div>
            <ul>{% for b in c.reviews.bullets %}<li>{{ b }}</li>{% endfor %}</ul>
          </div>
          <div class="dim-card">
            <div class="dim-title">Content &amp; SEO</div>
            <ul>{% for b in c.content_seo.bullets %}<li>{{ b }}</li>{% endfor %}</ul>
          </div>
        </div>
      </div>
    </div>
    {% endfor %}
  </div>

  <!-- Opportunities -->
  <div class="section">
    <h2>Top Opportunities for {{ profile.name }}</h2>
    <ul class="opportunities-list">
      {% for opp in opportunities %}
      <li>{{ opp }}</li>
      {% endfor %}
    </ul>
  </div>

</div>

<!-- Footer -->
<div class="report-footer">
  <span>{{ profile.name }} — Confidential</span>
  <span>Generated {{ report_date }} via WAT Competitor Analysis Workflow</span>
</div>

</body>
</html>"""


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    # Validate inputs
    for path, label in [
        (PROFILE_FILE, "business_profile.json"),
        (RESEARCH_DIR, ".tmp/research/"),
    ]:
        if not path.exists():
            print(f"ERROR: {label} not found. Make sure earlier steps have run.", file=sys.stderr)
            sys.exit(1)

    research_files = list(RESEARCH_DIR.glob("*.json"))
    if not research_files:
        print("ERROR: No research files found in .tmp/research/. Run research_competitor.py first.", file=sys.stderr)
        sys.exit(1)

    anthropic_key = os.environ.get("ANTHROPIC_API_KEY")
    if not anthropic_key:
        print("ERROR: ANTHROPIC_API_KEY not set in .env", file=sys.stderr)
        sys.exit(1)

    # Load data
    profile = json.loads(PROFILE_FILE.read_text())
    brand = load_brand_guide()
    logo_b64 = load_logo_b64(brand)
    competitors = [json.loads(f.read_text()) for f in sorted(research_files)]

    client = anthropic.Anthropic(api_key=anthropic_key)

    print("Generating executive summary...")
    executive_summary = generate_executive_summary(client, profile, competitors)

    print("Generating opportunities section...")
    opportunities = generate_opportunities(client, profile, competitors)

    # Render HTML
    print("Rendering HTML report...")
    env = Environment(loader=BaseLoader())
    template = env.from_string(REPORT_HTML)
    html = template.render(
        profile=profile,
        brand=brand,
        logo_b64=logo_b64,
        competitors=competitors,
        executive_summary=executive_summary,
        opportunities=opportunities,
        report_date=date.today().strftime("%B %d, %Y"),
    )

    # Convert to PDF
    print("Converting to PDF...")
    try:
        from weasyprint import HTML as WeasyprintHTML
    except ImportError:
        print("ERROR: weasyprint not installed. Run: pip install weasyprint", file=sys.stderr)
        sys.exit(1)

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    output_path = REPORTS_DIR / f"competitor_analysis_{date.today().isoformat()}.pdf"

    WeasyprintHTML(string=html, base_url=str(PROJECT_ROOT)).write_pdf(str(output_path))

    print(f"\nReport saved to: {output_path}")


if __name__ == "__main__":
    main()
