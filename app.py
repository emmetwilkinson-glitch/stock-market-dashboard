"""Landing page — quick market snapshot."""

import os
from dotenv import load_dotenv
load_dotenv()

import streamlit as st
import plotly.graph_objects as go
from lib.config      import APP_TITLE, APP_ICON, DISCLOSURE
from lib.market_data import INDEX_TICKERS, SECTOR_ETFS, get_quotes_bulk, get_history

st.set_page_config(
    page_title="Stock Market Analyst",
    page_icon=APP_ICON,
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Global styles ─────────────────────────────────────────────────────────────
st.markdown("""
<style>
  .main .block-container { font-size: 17px; max-width: 1400px; }
  .metric-card {
    background: #1e1e2e; border: 1px solid #2a2a3e; border-radius: 10px;
    padding: 14px 18px; margin-bottom: 10px;
  }
  .up   { color: #26a69a; font-weight: 700; }
  .down { color: #ef5350; font-weight: 700; }
  div[data-testid="stSidebar"] .stMarkdown h1 { font-size: 1.3rem; }
</style>
""", unsafe_allow_html=True)

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 📈 Market Analyst")
    st.markdown("---")
    st.markdown("**Navigation**")
    st.page_link("pages/1_💹_Market_Pulse.py",   label="💹 Market Pulse")
    st.page_link("pages/2_🔍_Stock_Analyzer.py", label="🔍 Stock Analyzer")
    st.page_link("pages/3_🧺_ETF_Analyzer.py",  label="🧺 ETF Analyzer")
    st.page_link("pages/4_🌍_Macro.py",          label="🌍 Macro")
    st.page_link("pages/5_💼_Portfolio.py",      label="💼 Portfolio")
    st.page_link("pages/6_📰_News.py",           label="📰 News")

# ── Header ────────────────────────────────────────────────────────────────────
st.title("📈 Stock Market Analyst")
st.caption("Your personal financial research dashboard — educational & research use only")
st.divider()

# ── Quick market snapshot ─────────────────────────────────────────────────────
st.subheader("📊 Quick Market Snapshot")

tickers = list(INDEX_TICKERS.values())
quotes  = get_quotes_bulk(tickers)

cols = st.columns(5)
for i, (name, tkr) in enumerate(INDEX_TICKERS.items()):
    q     = quotes.get(tkr, {})
    price = q.get("price")
    pct   = q.get("pct_change")

    with cols[i % 5]:
        if price is not None and pct is not None:
            sign  = "+" if pct >= 0 else ""
            color = "#26a69a" if pct >= 0 else "#ef5350"
            arrow = "▲" if pct >= 0 else "▼"
            st.markdown(f"""
<div class="metric-card">
  <div style="font-size:12px;color:#94a3b8;margin-bottom:4px;">{name}</div>
  <div style="font-size:18px;font-weight:700;">{price:,.2f}</div>
  <div style="color:{color};font-size:14px;">{arrow} {sign}{pct:.2f}%</div>
</div>
""", unsafe_allow_html=True)
        else:
            st.markdown(f"""
<div class="metric-card">
  <div style="font-size:12px;color:#94a3b8;margin-bottom:4px;">{name}</div>
  <div style="color:#64748b;">Unavailable</div>
</div>
""", unsafe_allow_html=True)

st.divider()

# ── S&P 500 Chart ─────────────────────────────────────────────────────────────
st.subheader("S&P 500 — 1 Year")
df_sp = get_history("^GSPC", period="1y", interval="1wk")
if not df_sp.empty:
    from lib.charts import render_price_chart
    fig = render_price_chart(df_sp, "^GSPC", view="Area", show_volume=False, height=350)
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("Price data unavailable.")

st.divider()

# ── Sector snapshot ───────────────────────────────────────────────────────────
st.subheader("📊 Sector Performance Today")
sector_quotes = get_quotes_bulk(list(SECTOR_ETFS.values()))
sectors = [(n, t, sector_quotes.get(t, {}).get("pct_change"))
           for n, t in SECTOR_ETFS.items()]
sectors.sort(key=lambda x: x[2] or 0, reverse=True)

sec_cols = st.columns(4)
for i, (name, tkr, pct) in enumerate(sectors):
    if pct is None:
        continue
    sign  = "+" if pct >= 0 else ""
    color = "#26a69a" if pct >= 0 else "#ef5350"
    with sec_cols[i % 4]:
        st.markdown(f"""
<div style="padding:8px 12px;margin:4px 0;background:#1e1e2e;border-radius:8px;
     border-left:3px solid {color};">
  <span style="font-size:13px;color:#94a3b8;">{name}</span>
  <span style="float:right;color:{color};font-weight:700;">{sign}{pct:.2f}%</span>
</div>
""", unsafe_allow_html=True)

# ── Footer ────────────────────────────────────────────────────────────────────
st.divider()
st.caption(DISCLOSURE)
