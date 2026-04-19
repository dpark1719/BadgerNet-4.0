# Data harvesting policy — aggregates and published sources only

BadgerNet ships **ETL that consumes public aggregates or files you export yourself**. The goal is high-signal statistics without building a surveillance-style dataset of individuals.

## Allowed

- **Official aggregates:** IPEDS, College Scorecard (API key optional), UW Common Data Set / fact books / First Destination Survey **tables you download** (PDF, Excel, Tableau CSV export).
- **Curated public knowledge graphs:** Wikidata / Wikipedia for **notable** lists with links for verification — not exhaustive career surveillance.
- **LinkedIn (and similar) only as roll-ups you control:** e.g. counts by employer, industry, country, after applying LinkedIn’s own filters, exported to CSV — **not** automated scraping of every profile or mass collection of Reddit accounts.

## Not allowed in this repository

- Mass crawling of LinkedIn, Reddit, or other social profiles to infer “every person’s pathway.”
- Storing or publishing raw profile dumps, URLs to private profiles as data products, or PII keyed to individuals.
- Circumventing site Terms of Service or rate limits.

If you need more granularity, work from **UW-published tables**, **survey microdata under license**, or **vendor datasets** with a lawful basis — then document the source in each bundle’s `meta`.

## Rankings harvest (`harvest_rankings.py`)

- **Shipped automation** uses the **Wikidata Action API** and **IPEDS** downloads (no publisher HTML scraping).
- **Optional** `data/raw/major_ranks.csv` lets you merge publisher ranks you are entitled to use.
- **Headless scraping** of sites like US News or Niche often violates their Terms of Service and is brittle; if you add Playwright scripts locally, keep them **out of CI**, run them only where permitted, and still **commit static JSON** for the app.
