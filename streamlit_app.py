"""Private, cloud-hosted viewer for the unchanged PSX screener dashboard.

Deploy from a PRIVATE GitHub repository on Streamlit Community Cloud.
All scores/signals are computed by the exported engine; this wrapper does not
fabricate live prices or change any trading rule. No OpenAI API key is needed.
"""
from __future__ import annotations

import datetime as dt
import json
from pathlib import Path
from zoneinfo import ZoneInfo

import streamlit as st
import streamlit.components.v1 as components

ROOT = Path(__file__).resolve().parent
DASHBOARD = ROOT / "dashboard" / "psx-screener-single-file.html"
MARKET = ROOT / "data" / "current" / "market.json"
REPORTS = ROOT / "reports"

st.set_page_config(page_title="PSX Strategy Screener — Online", page_icon="📈", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""<style>
.block-container {padding-top: 1.2rem; padding-left: 1.4rem; padding-right: 1.4rem; max-width: 100%;}
[data-testid="stAppViewContainer"] {background-color: #faf9f7;}
</style>""", unsafe_allow_html=True)

market = []
try:
    market = json.loads(MARKET.read_text(encoding="utf-8"))
except (OSError, json.JSONDecodeError) as exc:
    st.error(f"Cannot read market snapshot: {exc}")

as_of_raw = str(market[0].get("as_of", "")) if market else ""
try:
    as_of = dt.date.fromisoformat(as_of_raw)
except ValueError:
    as_of = None
now_pkt = dt.datetime.now(ZoneInfo("Asia/Karachi"))
age_days = (now_pkt.date() - as_of).days if as_of else None

st.subheader("PSX Strategy Screener — Online")
if age_days is None:
    st.error("Data date unavailable — no live trading conclusions can be drawn.")
elif age_days == 0:
    st.info(f"Snapshot dated {as_of:%d %b %Y}. Verify exchange timing: this is NOT an independently verified live price feed.")
else:
    st.warning(f"Historical snapshot: {as_of:%d %b %Y} ({age_days} calendar days old). Signals are NOT current trading instructions.")

with st.sidebar:
    st.header("Dashboard controls")
    height = st.slider("Viewer height (pixels)", min_value=850, max_value=3000, value=1700, step=50)
    st.write(f"Source date: **{as_of_raw or 'Unknown'}**")
    st.caption("ChatGPT edits and maintains code through the connected private GitHub repository; this site does not itself call ChatGPT.")
    st.write("Latest saved research report")
    reports = sorted(REPORTS.glob("*.md"), reverse=True) if REPORTS.exists() else []
    if reports:
        report = reports[0]
        st.download_button("Download report", report.read_text(encoding="utf-8"), file_name=report.name, mime="text/markdown")
    else:
        st.caption("No report available yet")
    st.caption("Market-data collection depends on source availability, access rights, and refresh jobs. A chart signal is not an automatic trade.")

if not DASHBOARD.exists():
    st.error("Dashboard missing. Run: python dashboard/build_standalone.py")
    st.stop()

components.html(DASHBOARD.read_text(encoding="utf-8"), height=height, scrolling=True)
