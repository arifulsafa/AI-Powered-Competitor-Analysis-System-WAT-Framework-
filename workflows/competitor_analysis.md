# Workflow: Competitor Analysis & Branded PDF Report

## Objective

Produce a branded PDF competitor analysis report for the user's business.
The report covers up to 8 competitors across four dimensions: website & messaging, pricing & offers, reviews & reputation, and content & SEO.

---

## Required Inputs (Before Starting)

Before running any tools, confirm all of the following are in place:

1. **Business description** — user provides this in chat (or `business_profile.json` already exists from a prior run)
2. **Logo** — `brand/logo.png` exists (ask the user to drop it in if missing)
3. **Brand guide** — `brand/brand_guide.md` has been filled in with real colors and fonts
4. **API keys in `.env`**:
   - `ANTHROPIC_API_KEY`
   - `SERPER_API_KEY` (get one free at https://serper.dev)

If any of these are missing, stop and ask the user before proceeding.

---

## Execution Sequence

### Step 1 — Save Business Profile

Run if the user provides a new or updated business description, or if `business_profile.json` does not exist.

```bash
python tools/save_business_profile.py --description "<user's description>"
```

- Output: `business_profile.json`
- Verify: file exists and contains sensible values for name, industry, target_market

### Step 2 — Discover Competitors

```bash
python tools/discover_competitors.py
```

- Output: `.tmp/competitors.json` (list of 5–8 competitors with names and URLs)
- Verify: file exists with at least 3 entries
- If fewer than 3 are found: report what was found and ask the user if they want to add specific competitors manually

### Step 3 — Research Each Competitor

Run once per competitor. Loop through all entries in `.tmp/competitors.json`.

```bash
python tools/research_competitor.py --name "<name>" --url "<url>"
```

- Output: `.tmp/research/<competitor_name>.json`
- Runs 4 sub-tasks per competitor (website, pricing, reviews, content/SEO)
- If a competitor's site is unreachable: note it in the JSON and continue — do not stop the loop
- Add a 1-second pause between competitors to avoid rate limits

### Step 4 — Generate Branded PDF

```bash
python tools/generate_report.py
```

- Output: `.tmp/reports/competitor_analysis_YYYY-MM-DD.pdf`
- Report file path is printed to the terminal on success
- Tell the user the full path so they can open it

---

## Edge Cases & Known Issues

| Situation | How to Handle |
|---|---|
| Competitor blocks scraping | `research_competitor.py` will catch the error and use search snippet as fallback. Note in output. |
| Pricing page requires login | Script detects missing pricing keywords and notes "pricing not public". Normal behavior. |
| Logo file missing | `generate_report.py` continues without a logo and logs a warning. Remind user to add `brand/logo.png`. |
| Serper rate limit hit (429) | Wait 30 seconds and retry once. If it fails again, note it and continue with partial data. |
| WeasyPrint missing | Script will error with install instructions. Run `pip install weasyprint`. |
| Google Fonts not loading (offline) | PDF will fall back to system fonts. Not a blocking issue. |
| `business_profile.json` already exists | Skip Step 1 unless the user wants to update their profile. Ask if unsure. |

---

## Output

- **Primary**: `.tmp/reports/competitor_analysis_YYYY-MM-DD.pdf`
- **Intermediates** (disposable): `.tmp/competitors.json`, `.tmp/research/*.json`
- **Persistent**: `business_profile.json` (reused on future runs)

Tell the user the PDF path when done. The file is local — no cloud upload unless the user requests it.

---

## Re-running the Workflow

- To refresh competitor research with the same business: skip Step 1, run Steps 2–4
- To update business profile only: run Step 1 only, then continue from Step 2
- To add a specific competitor manually: run `research_competitor.py` with their name/URL directly, then re-run Step 4

---

## Self-Improvement Notes

- Serper free tier: ~2,500 searches. Each full run uses ~20–25 searches (3 discovery + 4 per competitor × up to 8).
- **Discovery quality issue (2026-04-18):** For broad SaaS categories, the first query ("best Productivity / SaaS software for...") returns roundup/review articles (Gartner, PCMag, ZDNet) instead of actual product homepages. The `is_company_homepage` filter only excludes a hardlist of domains. Fix: (1) expanded the exclude_domains list in `discover_competitors.py` to cover common media/roundup sites; (2) if competitor list still looks wrong, manually curate `.tmp/competitors.json` with known product URLs before running research. The `{name} competitors alternatives` query is the most reliable — run it first.
- WeasyPrint requires system libraries on some OS — if install fails on Linux, user may need `libpango`, `libcairo` packages.
- **WeasyPrint on macOS (2026-04-18):** WeasyPrint looks for `libgobject-2.0-0` but Homebrew installs it as `libgobject-2.0.0.dylib`. Fix: run with `DYLD_LIBRARY_PATH=/opt/homebrew/lib python3 tools/generate_report.py`. If pango is not installed: `brew install pango`.
- Some enterprise SaaS sites heavily use JavaScript rendering; `requests` + `beautifulsoup4` will only get static content. If a site is important and returns mostly empty, note it and use Serper snippets as the data source instead.
