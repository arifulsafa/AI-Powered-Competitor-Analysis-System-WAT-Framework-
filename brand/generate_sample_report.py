#!/usr/bin/env python3
"""
Generates a sample branded competitor analysis PDF using dummy data.
Used for portfolio demonstration — no API keys required.

Run from project root:
    python3 brand/generate_sample_report.py
"""

import base64, json, sys
from datetime import date
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Reuse helpers from generate_report.py
from tools.generate_report import load_brand_guide, load_logo_b64, REPORT_HTML, REPORTS_DIR

from jinja2 import Environment, BaseLoader

# ── Dummy data ────────────────────────────────────────────────────────────────

PROFILE = {
    "name": "Veltro",
    "industry": "AI Logistics Intelligence SaaS",
    "target_market": "Mid-market freight brokers & 3PLs in North America",
    "geography": "United States & Canada",
    "products": ["Real-time shipment intelligence", "Carrier performance scoring", "Predictive delay alerts"],
    "differentiators": ["No-code onboarding", "Sub-minute data refresh", "AI-native architecture"],
    "known_competitors": ["project44", "FourKites", "Descartes"],
}

COMPETITORS = [
    {
        "name": "project44",
        "url": "https://project44.com",
        "website_messaging": {
            "bullets": [
                "Positions as 'The Connected Supply Chain Platform' — broad enterprise appeal",
                "Targets large shippers and 3PLs with complex multi-modal needs",
                "Heavy emphasis on real-time visibility across 200+ countries",
                "Primary CTA drives demo bookings — classic enterprise sales motion",
                "Tone is authoritative and technical; clearly aimed at supply chain directors",
            ]
        },
        "pricing": {
            "bullets": [
                "No public pricing — all plans gated behind a sales call",
                "Rumored six-figure annual contracts for enterprise tier",
                "Custom pricing based on carrier integrations and shipment volume",
                "No self-serve or free trial — high-touch sales only",
                "Pricing opacity suggests strong negotiation leverage for buyers",
            ]
        },
        "reviews": {
            "bullets": [
                "4.3/5 on G2 across 280+ reviews — strong overall sentiment",
                "Most praised for carrier network breadth and data accuracy",
                "Common complaints: slow implementation timelines and steep learning curve",
                "Enterprise customers report high satisfaction post-onboarding",
                "SMB users frustrated by contract minimums and support responsiveness",
            ]
        },
        "content_seo": {
            "bullets": [
                "Active blog with 3–5 posts per month on supply chain visibility trends",
                "Ranks well for 'supply chain visibility software' and related head terms",
                "Heavy investment in long-form whitepapers and analyst reports (Gartner, Forrester)",
                "Podcast and webinar series targeting VP-level supply chain leaders",
                "Strong domain authority (~72) built through years of content investment",
            ]
        },
    },
    {
        "name": "FourKites",
        "url": "https://fourkites.com",
        "website_messaging": {
            "bullets": [
                "Lead message: 'The World's Largest Real-Time Supply Chain Network'",
                "Focuses on sustainability and carbon tracking as a differentiator",
                "Strong emphasis on customer logos (Nike, Kraft Heinz, Walmart) for social proof",
                "Calls to action split between demo and ROI calculator — good conversion hygiene",
                "Messaging is polished and benefit-led rather than feature-led",
            ]
        },
        "pricing": {
            "bullets": [
                "Pricing not publicly listed — requires contact with sales team",
                "Known to offer modular pricing by product (TMS, visibility, sustainability)",
                "Enterprise contracts typically $80K–$250K+ annually based on volume",
                "Pilot programs available for qualified enterprise prospects",
                "No freemium or SMB-accessible tier visible",
            ]
        },
        "reviews": {
            "bullets": [
                "4.4/5 on G2 — slightly higher rated than project44 among users",
                "Praised heavily for UI design and ease of use relative to competitors",
                "Sustainability reporting features receive consistent positive mentions",
                "Weaknesses: API documentation described as lacking by technical reviewers",
                "Customer success team rated highly — proactive onboarding noted",
            ]
        },
        "content_seo": {
            "bullets": [
                "Publishes 2–4 blog posts per month with strong SEO optimization",
                "Ranks for sustainability + supply chain keyword clusters — a unique niche",
                "Case study library is one of the most robust in the category",
                "Annual 'State of Supply Chain' report generates significant backlinks",
                "YouTube channel with product demos and customer testimonials — good mid-funnel content",
            ]
        },
    },
    {
        "name": "Descartes",
        "url": "https://descartes.com",
        "website_messaging": {
            "bullets": [
                "Positions as a broad logistics management platform — compliance, routing, visibility",
                "Messaging targets logistics operations leaders in regulated industries",
                "Value prop centers on compliance and global trade documentation",
                "Less consumer-friendly design — clearly built for logistics professionals",
                "Multiple product lines create messaging complexity on the homepage",
            ]
        },
        "pricing": {
            "bullets": [
                "No pricing listed publicly — enterprise sales model",
                "Offers a wide range of products priced separately (routing, compliance, visibility)",
                "Total cost of ownership can be high when multiple modules are needed",
                "Government and regulated-industry pricing likely custom and negotiated",
                "Some legacy modules still on perpetual license model",
            ]
        },
        "reviews": {
            "bullets": [
                "4.1/5 on G2 — lower satisfaction scores than newer entrants",
                "Long-time customers value the breadth of features and reliability",
                "Common criticism: dated UI and slow product innovation cycle",
                "Support quality described as inconsistent across regions",
                "Strong reputation in customs and trade compliance — niche authority",
            ]
        },
        "content_seo": {
            "bullets": [
                "Moderate content output — roughly 1–2 posts per week across multiple product blogs",
                "Strong SEO presence for compliance and customs brokerage keywords",
                "Resource library heavy on compliance guides and regulatory updates",
                "Less focus on thought leadership; more transactional/product content",
                "Domain authority ~65 — solid but not a content-first company",
            ]
        },
    },
]

EXECUTIVE_SUMMARY = (
    "The AI logistics visibility market is dominated by three well-funded incumbents — project44, FourKites, and Descartes — "
    "each targeting large enterprise shippers with high-touch sales, opaque pricing, and complex implementations. "
    "This report analyzes their positioning, pricing strategy, customer sentiment, and content presence to surface clear "
    "opportunities for Veltro to differentiate and capture underserved segments of the market."
)

OPPORTUNITIES = [
    "Transparent, self-serve pricing with a free tier would immediately differentiate Veltro from all three competitors "
    "and capture the mid-market segment that competitors actively ignore due to high contract minimums.",
    "All three incumbents receive consistent complaints about slow onboarding and steep learning curves — Veltro's "
    "'no-code onboarding' positioning directly addresses this gap and should be the centerpiece of head-to-head messaging.",
    "FourKites is winning on content and UI, but none of the three publish developer-focused content. "
    "An API-first content strategy (docs, tutorials, integration guides) would own an uncontested search and community niche.",
]


def main():
    brand = load_brand_guide()
    logo_b64 = load_logo_b64(brand)

    env = Environment(loader=BaseLoader())
    template = env.from_string(REPORT_HTML)
    html = template.render(
        profile=PROFILE,
        brand=brand,
        logo_b64=logo_b64,
        competitors=COMPETITORS,
        executive_summary=EXECUTIVE_SUMMARY,
        opportunities=OPPORTUNITIES,
        report_date=date.today().strftime("%B %d, %Y"),
    )

    try:
        from weasyprint import HTML as WP
    except ImportError:
        print("WeasyPrint not installed. Run: pip install weasyprint")
        sys.exit(1)

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    out = REPORTS_DIR / "veltro_sample_competitor_analysis.pdf"
    WP(string=html, base_url=str(PROJECT_ROOT)).write_pdf(str(out))
    print(f"Sample report saved to: {out}")


if __name__ == "__main__":
    main()
