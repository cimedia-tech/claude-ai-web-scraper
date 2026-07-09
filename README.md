# Claude AI Web Scraper

> Production-grade AI-powered web scraper built with **Crawl4AI + Claude Haiku 4.5 + GitHub Actions**.
> Extracted from the Anti-mediacreator Intelligence Report (INT-REPT-2025).

## Stack
| Layer | Tool |
|---|---|
| Crawler | Crawl4AI (Fit Markdown, stealth mode) |
| LLM | Claude Haiku 4.5 ($1/MTok — cheapest production model) |
| Browser | Playwright (headless Chromium) |
| Validation | Pydantic v2 |
| Cache | SQLite (aiosqlite) — prevents duplicate API calls |
| Scheduler | GitHub Actions (free, 2000 min/month) |
| CLI | Typer + Rich |

## Setup

```bash
# 1. Clone + install
pip install -r requirements.txt
playwright install chromium --with-deps
crawl4ai-setup

# 2. Configure
cp .env.example .env
# Edit .env — add your ANTHROPIC_API_KEY

# 3. Run
python main.py scrape https://example.com/directory --schema lead
```

## CLI Usage

```bash
# Scrape leads from a URL
python main.py scrape https://example.com --schema lead

# Scrape products with custom instruction
python main.py scrape https://shop.com/products \
  --schema product \
  --instruction "Extract product name, price, and availability"

# Multiple URLs
python main.py scrape https://site1.com https://site2.com --schema article

# Check total API cost
python main.py cost

# Clear expired cache
python main.py clear-cache
```

## Schemas

| Schema | Fields |
|---|---|
| `lead` | company, contact_name, email, phone, website, address, description |
| `product` | name, price, currency, availability, sku, description, url, rating |
| `article` | title, author, published_date, summary, tags, url |
| `generic` | title, content, metadata, url |

## Cost Optimization

- **Prompt caching** — system prompt marked `cache_control: ephemeral` (90% input savings on repeat calls)
- **Fit Markdown** — Crawl4AI prunes content before LLM call (50–80% token reduction)
- **Haiku model** — $1/MTok vs $3/MTok for Sonnet
- **SQLite URL cache** — prevents re-scraping same URL within TTL window
- **Token gate** — content truncated to `MAX_TOKEN_INPUT` chars before Claude

**Estimated cost:** ~$0.003–$0.005 per page with optimizations.

## GitHub Actions

Add `ANTHROPIC_API_KEY` to your repository Secrets, then the workflow runs:
- **Daily at 07:00 UTC** automatically
- **On-demand** via Actions → Run workflow button
- Results uploaded as downloadable artifact (30-day retention)

## Project Structure

```
.
├── main.py                    # CLI entry point (Typer)
├── requirements.txt
├── .env.example
├── scraper/
│   ├── config.py              # Pydantic settings from .env
│   ├── schemas.py             # Extraction data models
│   ├── cache.py               # SQLite URL cache + cost logger
│   ├── preprocessor.py        # HTML noise stripper
│   ├── claude_client.py       # Anthropic SDK wrapper
│   └── core.py                # Main scraper orchestrator
├── .github/workflows/
│   └── scraper.yml            # GitHub Actions scheduler
└── index.html                 # Intelligence report (Vercel)
```
