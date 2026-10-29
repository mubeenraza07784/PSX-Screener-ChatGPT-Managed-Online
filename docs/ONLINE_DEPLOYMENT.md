# ChatGPT-managed PSX screener: private cloud deployment

## What this actually gives you

- A **private URL** to your original 7-tab screener on Streamlit Community Cloud.
- **No Claude dependency**: the full original Python engine and dashboard are in this repo.
- Code changes done through ChatGPT + a **connected GitHub repository** can be reviewed and deployed without sending ZIPs each time.
- Optional **GitHub Actions** cloud data collection and after-close updates. It is **not enabled initially** and may fail due to stockanalysis.com/PSX website restrictions. No bypass of rate limits, logins or CAPTCHAs is included.
- **No OpenAI API required** to view the dashboard or let ChatGPT help edit source code. A ChatGPT Plus subscription and API usage are separate; ChatGPT is not a continuously-running process inside this site.
- The current uploaded data is a historical snapshot (28 Oct 2026). No current trade recommendation is implied.

## Security requirements

Your portfolio, broker averages, signals, and watch lists appear in files in the exported source and can be exposed by a public repository or public app. **Create a private GitHub repo** and deploy the Streamlit app with **Private** visibility. Do **not** put your API keys/passwords in the repo or this chat.

Free Streamlit Community Cloud supports private apps but has plan/account limits and the viewer permissions of its GitHub integration. Inspect your app's visibility and viewer settings after deploying.

## Setup (only once)

1. Create a private repo on https://github.com/new named e.g. `psx-strategy-screener` (choose **Private**).
2. Upload **the CONTENTS of this ZIP's `psx-strategy-screener/` folder** to the repository root, preserving directories (not an unextracted ZIP only). **Windows no-code path:** install GitHub Desktop, choose File → Add local repository → the extracted `psx-strategy-screener` folder; if prompted, create a repository there, then Publish repository, with "Keep this code private" checked. If you already made the empty repo in step 1, cloning that repo and copying the extracted contents into it is an alternative.
3. Connect GitHub to ChatGPT using Settings → Plugins (if not yet connected) and authorize access to this repository. Then in ChatGPT say: **"Manage my GitHub repository OWNER/psx-strategy-screener: inspect its issues, fix bugs, and submit changes for my approval."** This creates a practical ongoing management channel through the repo, not a direct link to the old Claude artifact.
4. Go to https://share.streamlit.io, create/sign into Streamlit Community Cloud and connect the same GitHub account (including private-repo access).
5. Create a new app using your private repository, branch `main`, entrypoint file `streamlit_app.py`, and **Private** visibility. Streamlit installs `requirements.txt`. Copy the generated `*.streamlit.app` URL.
6. Open the URL, confirm it requires your Streamlit login, and check that the "Historical snapshot" banner correctly shows the data date.
7. Test GitHub Actions → `Validate PSX screener`. This runs a schema/syntax test without using any market data site.
8. To TRY fresh collection in GitHub's cloud environment: Actions → `Refresh PSX data (cloud)` → Run workflow. **It can fail** because website data collection is rate-limited or blocked in headless cloud browsers; check the Actions logs. The old snapshot stays available. Live/real-time prices are **not guaranteed**.
9. Only after a successful test and verifying your source rights, you can opt into the weekday scheduled refresh by adding **Repository variable** `PSX_ENABLE_SCHEDULED_REFRESH=true` in Settings → Secrets and variables → Actions → Variables. This runs 17:43 Pakistan time Monday–Friday, consumes GitHub Actions minutes, and skips holidays only insofar as the freshness gate rejects stale data.

## Important constraints

- The original source **hard-codes holdings** in `engine/analyze.py`, `engine/build_ds.py`, and `monitor/report.py`. The `config/holdings.json` is for reference, **not** the authoritative input. Ask ChatGPT to centralize and reconcile holdings before trusting portfolio signals.
- `engine/alerts.py` is broken for new setup names. The cloud job uses `--fixed-alerts` (`engine/alerts_v2.py`). We preserve both files for provenance.
- The app shows historical/snapshot signals until a successful cloud refresh. Headless collection may fail; never treat a failed job as a current market feed.
- Economic readings are not automatically retrieved and remain manually maintained in `workdir/macro_src.json` and `workdir/config.json`.
- This workflow does not place trades or send WhatsApp messages. Those require separately authorized integrations and compliance checks.
- Changing GitHub source does not mean ChatGPT operates your account autonomously. Ask ChatGPT to review/modify the GitHub repo when needed, and approve any changes or actions as appropriate.

## Why Streamlit instead of a public static link?

A public Pages/static website can expose your holdings and portfolio signals to anyone with the URL. Streamlit Community Cloud provides an authenticated private viewer from a private GitHub repo, with source edits redeploying automatically. Contact Streamlit or use a paid authenticated host if private-app availability or operational needs change.
