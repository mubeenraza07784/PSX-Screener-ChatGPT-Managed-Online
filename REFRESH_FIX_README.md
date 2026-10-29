# ChatGPT PSX Cloud Refresh fix — 29 October 2026

## Diagnosed issue
Both GitHub Actions runs (40849542870 and 40849742626) installed Chromium successfully. The collector then encountered StockAnalysis.com's browser verification page and exited before engine recomputation. This is a cloud-automation access issue, not an error in the calculations or Streamlit deployment.

## What changed
- `.github/workflows/refresh.yml`: removed unsupported recurring headless scraping. Added a safe `validate_only` mode and an `import_approved` mode using supplied full technical features. No automatic publishing of stale or partial data.
- `cloud/import_approved.py`: validates provider self-attestation, date, full-column technical features, source coverage, symbol and price integrity **before** merging with the original engine. It never bypasses bot checks or automatically fetches restricted sources.
- `imports/README.md`: complete import instructions and source schema; includes `source.example.json`.
- `.github/workflows/validate.yml`: upgrades GitHub Actions to Node 24-compatible versions and adds import unit tests.
- `tests/test_approved_import.py`: importer tests.

## Limitations
There is no functioning automatic market feed in this patch. To get automatic daily updates, you need an **approved API/feed** for fresh daily OHLCV AND a calculation adapter for the bot's full Alligator/CWT/RSI/MACD/chart fields. Until then, the Streamlit banner correctly displays the historical snapshot.

## Installation
Extract this ZIP and copy the patched files and folders into the root of your existing local Git repository, preserving paths. From your repository folder run:

```bat
git add .github/workflows/refresh.yml .github/workflows/validate.yml cloud/import_approved.py imports/README.md imports/source.example.json tests/test_approved_import.py REFRESH_FIX_README.md
git commit -m "Replace blocked collector with safe approved-data refresh"
git push origin main
```

The validation workflow should then run automatically. GitHub Actions → `Refresh PSX data (approved import)` → Run workflow → `validate_only` checks the existing engine without publishing.

## GitHub access
ChatGPT can read the repository but GitHub returned HTTP 403 when asked to create a branch through the connector. The user must push these files (or enable repo write authorization through the connection UI). The repo is still public; make it private before sharing any licensed input or portfolio details.
