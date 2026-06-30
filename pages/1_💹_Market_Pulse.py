"""Market Pulse — comprehensive market overview."""

import os
from dotenv import load_dotenv
load_dotenv()

import streamlit as st
import plotly.graph_objects as go
import pandas as pd

from lib.config      import DISCLOSURE, APP_ICON
from lib.market_data import (
    INDEX_TICKERS, SECTOR_ETFS, PERIOD_MAP,
    get_quotes_bulk, get_history, get_history_bulk,
    get_quote, get_prev_close,
)
from lib.charts      import render_price_chart, render_sparkline
from lib.news        import market_news
from lib.logos       import logo_img_tag

st.set_page_config(page_title="Market Pulse | Stock Market Analyst",
                   page_icon=APP_ICON, layout="wide")

st.markdown("""
<style>
  .main .block-container { font-size:17px; max-width:1400px; }
  .index-card {
    background:#1e1e2e; border:1px solid #2a2a3e; border-radius:10px;
    padding:12px 14px; text-align:center; margin-bottom:8px;
  }
  .up   { color:#26a69a; } .down { color:#ef5350; }
  .mover-row { display:flex; align-items:center; gap:10px; padding:6px 0;
                border-bottom:1px solid #1e1e2e; }
  .news-card { background:#1e1e2e; border-radius:8px; padding:12px 14px; margin-bottom:8px; }
</style>
""", unsafe_allow_html=True)

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 📈 Market Analyst")
    st.markdown("---")
    st.page_link("app.py",                        label="🏠 Home")
    st.page_link("pages/1_💹_Market_Pulse.py",    label="💹 Market Pulse")
    st.page_link("pages/2_🔍_Stock_Analyzer.py",  label="🔍 Stock Analyzer")
    st.page_link("pages/3_🧺_ETF_Analyzer.py",   label="🧺 ETF Analyzer")
    st.page_link("pages/4_🌍_Macro.py",           label="🌍 Macro")
    st.page_link("pages/5_💼_Portfolio.py",       label="💼 Portfolio")
    st.page_link("pages/6_📰_News.py",            label="📰 News")

st.title("💹 Market Pulse")

# ── Period selector ───────────────────────────────────────────────────────────
periods     = list(PERIOD_MAP.keys())
sel_period  = st.segmented_control("Period", periods, default="1D", key="mp_period")
if not sel_period:
    sel_period = "1D"
p_cfg = PERIOD_MAP[sel_period]

st.divider()

# ── Index cards with sparklines ───────────────────────────────────────────────
st.subheader("📈 Global Markets")

all_tickers = list(INDEX_TICKERS.values())
quotes      = get_quotes_bulk(all_tickers)
histories   = get_history_bulk(all_tickers, period=p_cfg["period"], interval=p_cfg["interval"])

cols = st.columns(5)
for i, (name, tkr) in enumerate(INDEX_TICKERS.items()):
    q       = quotes.get(tkr, {})
    price   = q.get("price")
    pct     = q.get("pct_change")
    df_hist = histories.get(tkr, pd.DataFrame())

    with cols[i % 5]:
        sign  = ("+" if pct >= 0 else "") if pct is not None else ""
        color = "#26a69a" if (pct or 0) >= 0 else "#ef5350"
        arrow = "▲" if (pct or 0) >= 0 else "▼"
        price_str = f"{price:,.2f}" if price else "—"
        pct_str   = f"{arrow} {sign}{pct:.2f}%" if pct is not None else "—"

        # Sparkline
        spark_html = ""
        if not df_hist.empty and "Close" in df_hist.columns:
            closes = df_hist["Close"].dropna().tolist()
            dates  = df_hist.index.tolist()
            if sel_period == "1D":
                prev = get_prev_close(tkr) or (closes[0] if closes else 1)
                # Prepend yesterday's close as baseline
                if dates and closes:
                    dates  = [dates[0] - pd.Timedelta(minutes=5)] + dates
                    closes = [prev] + closes
                baseline = prev
            else:
                baseline = closes[0] if closes else 1
            if closes:
                spark_fig = render_sparkline(dates, closes, baseline, height=55, width=140)
                spark_html = spark_fig.to_html(
                    full_html=False, include_plotlyjs=False,
                    config={"displayModeBar": False}
                )

        st.markdown(f"""
<div class="index-card">
  <div style="font-size:11px;color:#94a3b8;margin-bottom:2px;">{name}</div>
  <div style="font-size:17px;font-weight:700;">{price_str}</div>
  <div style="color:{color};font-size:13px;">{pct_str}</div>
  {spark_html}
</div>
""", unsafe_allow_html=True)

st.divider()

# ── S&P 500 Main Chart ────────────────────────────────────────────────────────
st.subheader("S&P 500 (^GSPC)")
view_opts = ["Performance", "Price", "Candlestick", "Area"]
view_sel  = st.segmented_control("Chart view", view_opts, default="Performance", key="mp_chart_view")
if not view_sel:
    view_sel = "Performance"

df_sp = get_history("^GSPC", period=p_cfg["period"], interval=p_cfg["interval"])
baseline_sp = None
if sel_period == "1D":
    baseline_sp = get_prev_close("^GSPC")

if not df_sp.empty:
    fig = render_price_chart(df_sp, "^GSPC", view=view_sel, show_volume=True,
                             baseline_price=baseline_sp, height=480)
    st.plotly_chart(fig, use_container_width=True, key="mp_sp_chart")
else:
    st.info("S&P 500 data unavailable.")

st.divider()

# ── Sector Heatmap ────────────────────────────────────────────────────────────
st.subheader("🗺️ Sector Performance")
sector_tickers = list(SECTOR_ETFS.values())
sec_quotes     = get_quotes_bulk(sector_tickers)
sec_data = []
for name, tkr in SECTOR_ETFS.items():
    q   = sec_quotes.get(tkr, {})
    pct = q.get("pct_change")
    if pct is not None:
        sec_data.append({"Sector": name, "Ticker": tkr, "Change %": pct})

if sec_data:
    df_sec = pd.DataFrame(sec_data).sort_values("Change %", ascending=True)
    colors = ["#26a69a" if v >= 0 else "#ef5350" for v in df_sec["Change %"]]
    fig_sec = go.Figure(go.Bar(
        x=df_sec["Change %"],
        y=df_sec["Sector"],
        orientation="h",
        marker_color=colors,
        text=[f"{v:+.2f}%" for v in df_sec["Change %"]],
        textposition="outside",
        hovertemplate="%{y}: %{x:+.2f}%<extra></extra>",
    ))
    fig_sec.update_layout(
        template="plotly_dark",
        height=380,
        margin=dict(l=10, r=60, t=20, b=10),
        xaxis=dict(ticksuffix="%", zeroline=True, zerolinecolor="rgba(255,255,255,0.2)"),
        yaxis=dict(tickfont=dict(size=13)),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    st.plotly_chart(fig_sec, use_container_width=True, key="mp_sector_heatmap")

st.divider()

# ── Movers ────────────────────────────────────────────────────────────────────
st.subheader("🔥 Market Movers")

# Use a fixed set of large-cap tickers for movers
MOVER_TICKERS = [
    "AAPL","MSFT","GOOGL","AMZN","NVDA","META","TSLA","AVGO","JPM","V",
    "UNH","LLY","JNJ","XOM","MA","HD","PG","MRK","ABBV","CVX",
    "COST","BAC","CRM","NFLX","AMD","ORCL","TMO","ABT","QCOM","DHR",
    "ADBE","WMT","KO","PEP","MCD","CSCO","INTC","GE","HON","CAT",
    "GS","BLK","SCHW","SPGI","UPS","RTX","DE","LMT","BA","NEE",
]
mover_quotes = get_quotes_bulk(MOVER_TICKERS)

def _pct(q): return q.get("pct_change") or 0
def _vol(q): return q.get("volume") or 0

sorted_pct = sorted(mover_quotes.items(), key=lambda x: _pct(x[1]), reverse=True)
gainers    = [(t, q) for t, q in sorted_pct if _pct(q) > 0][:5]
losers     = [(t, q) for t, q in sorted(mover_quotes.items(), key=lambda x: _pct(x[1]))
              if _pct(x[1]) < 0][:5]
most_active= sorted(mover_quotes.items(), key=lambda x: _vol(x[1]), reverse=True)[:5]

def render_mover_row(tkr, q, color):
    price  = q.get("price")
    pct    = q.get("pct_change")
    name   = q.get("name", tkr)[:20]
    logo   = logo_img_tag(tkr, size=28)
    p_str  = f"${price:,.2f}" if price else "—"
    c_str  = f"{'+' if (pct or 0)>=0 else ''}{pct:.2f}%" if pct is not None else "—"
    return f"""
<div class="mover-row">
  {logo}
  <div style="flex:1">
    <div style="font-weight:700;font-size:14px;">{tkr}</div>
    <div style="font-size:12px;color:#94a3b8;">{name}</div>
  </div>
  <div style="text-align:right">
    <div style="font-size:14px;font-weight:600;">{p_str}</div>
    <div style="color:{color};font-size:13px;font-weight:700;">{c_str}</div>
  </div>
</div>"""

mc1, mc2, mc3 = st.columns(3)
with mc1:
    st.markdown("**🟢 Top Gainers**")
    for tkr, q in gainers:
        st.markdown(render_mover_row(tkr, q, "#26a69a"), unsafe_allow_html=True)
with mc2:
    st.markdown("**🔴 Top Losers**")
    for tkr, q in losers:
        st.markdown(render_mover_row(tkr, q, "#ef5350"), unsafe_allow_html=True)
with mc3:
    st.markdown("**⚡ Most Active**")
    for tkr, q in most_active:
        pct   = q.get("pct_change") or 0
        color = "#26a69a" if pct >= 0 else "#ef5350"
        st.markdown(render_mover_row(tkr, q, color), unsafe_allow_html=True)

st.divider()

# ── Top Headlines ─────────────────────────────────────────────────────────────
st.subheader("📰 Top Market Headlines")
with st.spinner("Loading headlines…"):
    headlines = market_news(max_items=3)

if headlines:
    for art in headlines:
        title = art.get("title", "")
        pub   = art.get("publisher", "")
        ago   = art.get("time_ago", "")
        summ  = art.get("summary", "")[:160]
        link  = art.get("link", "#")
        st.markdown(f"""
<div class="news-card">
  <a href="{link}" target="_blank" style="text-decoration:none;color:#e2e8f0;font-weight:600;font-size:15px;">{title}</a>
  <div style="font-size:12px;color:#64748b;margin-top:4px;">{pub} · {ago}</div>
  {f'<div style="font-size:13px;color:#94a3b8;margin-top:6px;">{summ}</div>' if summ else ''}
</div>
""", unsafe_allow_html=True)
else:
    st.info("No headlines available right now.")

# ── Footer ────────────────────────────────────────────────────────────────────
st.divider()
st.caption(DISCLOSURE)
