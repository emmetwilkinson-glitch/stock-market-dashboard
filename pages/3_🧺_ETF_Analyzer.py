"""ETF Analyzer page."""

import os
from dotenv import load_dotenv
load_dotenv()

import streamlit as st
import plotly.graph_objects as go
import pandas as pd

from lib.config      import DISCLOSURE, APP_ICON
from lib.market_data import PERIOD_MAP, get_quote, get_history, get_etf_details, get_quotes_bulk, get_prev_close
from lib.charts      import render_price_chart
from lib.risk        import etf_risk_score
from lib.etf_peers   import find_peers
from lib.logos       import logo_img_tag, get_logo_b64

st.set_page_config(page_title="ETF Analyzer | Stock Market Analyst",
                   page_icon=APP_ICON, layout="wide")

st.markdown("""
<style>
  .main .block-container { font-size:17px; max-width:1400px; }
  .holding-row { display:flex; align-items:center; gap:10px; padding:6px 0;
                  border-bottom:1px solid #1e2d3d; }
  .callout { background:#14532d22; border:1px solid #26a69a44; border-radius:8px;
              padding:12px 16px; margin-top:8px; }
</style>
""", unsafe_allow_html=True)

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

st.title("🧺 ETF Analyzer")

col_in1, col_in2 = st.columns([2, 3])
with col_in1:
    ticker = st.text_input("ETF Ticker", value="SPY", placeholder="e.g. QQQ").strip().upper()
with col_in2:
    periods    = list(PERIOD_MAP.keys())
    sel_period = st.segmented_control("Period", periods, default="1Y", key="etf_period")
    if not sel_period:
        sel_period = "1Y"

if not ticker:
    st.info("Enter an ETF ticker to begin.")
    st.stop()

p_cfg = PERIOD_MAP[sel_period]

with st.spinner(f"Loading {ticker}…"):
    quote   = get_quote(ticker)
    details = get_etf_details(ticker)
    df      = get_history(ticker, period=p_cfg["period"], interval=p_cfg["interval"])
    prev_c  = get_prev_close(ticker) if sel_period == "1D" else None

if quote.get("price") is None and df.empty:
    st.error(f"No data for **{ticker}**. Is this an ETF ticker?")
    st.stop()

# ── Header ────────────────────────────────────────────────────────────────────
price    = quote.get("price") or 0
pct      = quote.get("pct_change") or 0
name     = details.get("name") or quote.get("name") or ticker
category = details.get("category") or "ETF"
expense  = details.get("expense_ratio")
aum      = details.get("aum")

logo_src = get_logo_b64(ticker)
c1, c2, c3 = st.columns([1, 3, 4])
with c1:
    if logo_src:
        st.image(logo_src, width=64)
    else:
        st.markdown(logo_img_tag(ticker, 64), unsafe_allow_html=True)
with c2:
    pct_color = "#26a69a" if pct >= 0 else "#ef5350"
    sign      = "+" if pct >= 0 else ""
    st.markdown(f"### {name}")
    st.markdown(f"`{ticker}` · {category}")
    st.markdown(
        f'<span style="font-size:24px;font-weight:800;">${price:,.2f}</span> '
        f'<span style="color:{pct_color};font-size:16px;">{sign}{pct:.2f}%</span>',
        unsafe_allow_html=True
    )
with c3:
    def _fmt_big(v):
        if v is None: return "—"
        if v >= 1e12: return f"${v/1e12:.1f}T"
        if v >= 1e9:  return f"${v/1e9:.1f}B"
        if v >= 1e6:  return f"${v/1e6:.1f}M"
        return f"${v:,.0f}"
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("AUM",            _fmt_big(aum))
    m2.metric("Expense Ratio",  f"{expense*100:.2f}%" if expense else "—")
    m3.metric("YTD Return",     f"{details.get('ytd_return')*100:.1f}%" if details.get("ytd_return") else "—")
    m4.metric("3Y Avg Return",  f"{details.get('three_yr_return')*100:.1f}%" if details.get("three_yr_return") else "—")

st.divider()

# ── Chart ─────────────────────────────────────────────────────────────────────
view_opts = ["Performance", "Price", "Candlestick", "Area"]
view_sel  = st.segmented_control("Chart view", view_opts, default="Performance", key="etf_chart_view")
if not view_sel:
    view_sel = "Performance"
if not df.empty:
    fig = render_price_chart(df, ticker, view=view_sel, show_volume=True,
                             baseline_price=prev_c, height=460)
    st.plotly_chart(fig, use_container_width=True, key="etf_main_chart")

st.divider()

# ── Returns & Risk ────────────────────────────────────────────────────────────
rc1, rc2 = st.columns(2)

with rc1:
    st.markdown("**📈 Returns**")
    ret_data = {
        "Period":       ["YTD",  "3Y Avg",  "5Y Avg"],
        "Return":       [
            f"{details.get('ytd_return',0)*100:.1f}%"       if details.get("ytd_return") else "—",
            f"{details.get('three_yr_return',0)*100:.1f}%"  if details.get("three_yr_return") else "—",
            f"{details.get('five_yr_return',0)*100:.1f}%"   if details.get("five_yr_return") else "—",
        ],
    }
    st.table(pd.DataFrame(ret_data))

with rc2:
    risk_score, risk_label = etf_risk_score(df, details)
    st.markdown("**⚠️ Risk Profile**")
    bands = [
        (0,  20,  "#1e4d3b"),
        (20, 40,  "#1a4d1a"),
        (40, 60,  "#4d3800"),
        (60, 80,  "#4d2000"),
        (80, 100, "#4d0f0f"),
    ]
    fig_risk = go.Figure(go.Indicator(
        mode="gauge+number",
        value=risk_score,
        title={"text": f"<b>Risk Score</b><br><span style='font-size:12px;color:#94a3b8'>{risk_label}</span>",
               "font": {"size": 14, "color": "#e2e8f0"}},
        gauge={
            "axis": {"range": [0, 100]},
            "bar":  {"color": "#334155", "thickness": 0.2},
            "bgcolor": "rgba(0,0,0,0)",
            "borderwidth": 0,
            "steps": [{"range": [a, b], "color": c} for a, b, c in bands],
            "threshold": {"line": {"color": "#f1f5f9", "width": 3},
                          "thickness": 0.8, "value": risk_score},
        },
        number={"font": {"color": "#f1f5f9", "size": 32}, "suffix": "/100"},
        domain={"x": [0, 1], "y": [0, 1]},
    ))
    fig_risk.update_layout(
        template="plotly_dark", height=200,
        margin=dict(l=10, r=10, t=60, b=10),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    )
    st.plotly_chart(fig_risk, use_container_width=True, key="etf_risk_gauge")

st.divider()

# ── Sector Breakdown ──────────────────────────────────────────────────────────
sec_weights = details.get("sector_weights", {})
if sec_weights:
    st.subheader("🗺️ Sector Allocation")
    df_sec = pd.DataFrame(list(sec_weights.items()), columns=["Sector", "Weight"])
    df_sec = df_sec.sort_values("Weight", ascending=True)
    fig_sec = go.Figure(go.Bar(
        x=df_sec["Weight"] * 100,
        y=df_sec["Sector"],
        orientation="h",
        marker_color="#4a7ab5",
        text=[f"{v*100:.1f}%" for v in df_sec["Weight"]],
        textposition="outside",
    ))
    fig_sec.update_layout(
        template="plotly_dark", height=320,
        margin=dict(l=10, r=60, t=20, b=10),
        xaxis=dict(ticksuffix="%"),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    )
    st.plotly_chart(fig_sec, use_container_width=True, key="etf_sector_chart")
    st.divider()

# ── Top Holdings ──────────────────────────────────────────────────────────────
holdings = details.get("holdings", [])
if holdings:
    st.subheader("🏦 Top Holdings")
    h_c1, h_c2 = st.columns(2)
    for i, h in enumerate(holdings[:10]):
        sym    = h.get("symbol", "")
        hname  = h.get("name", sym)[:25]
        weight = h.get("weight", 0) * 100
        logo   = logo_img_tag(sym, 28)
        row_html = f"""
<div class="holding-row">
  {logo}
  <div style="flex:1;">
    <div style="font-weight:700;font-size:14px;">{sym}</div>
    <div style="font-size:12px;color:#94a3b8;">{hname}</div>
  </div>
  <div style="font-weight:700;font-size:14px;color:#94a3b8;">{weight:.2f}%</div>
</div>"""
        if i < 5:
            h_c1.markdown(row_html, unsafe_allow_html=True)
        else:
            h_c2.markdown(row_html, unsafe_allow_html=True)
    st.divider()

# ── Peer Comparison ───────────────────────────────────────────────────────────
peers = find_peers(ticker)
if peers:
    st.subheader("🔄 Peer Comparison")
    all_tickers   = [ticker] + peers
    peer_quotes   = get_quotes_bulk(all_tickers)
    peer_details  = {t: get_etf_details(t) for t in all_tickers}

    rows = []
    for t in all_tickers:
        d = peer_details[t]
        q = peer_quotes.get(t, {})
        rows.append({
            "Ticker":        t,
            "Name":          (d.get("name") or q.get("name") or t)[:30],
            "Expense Ratio": d.get("expense_ratio"),
            "AUM":           d.get("aum"),
            "YTD Return":    d.get("ytd_return"),
            "3Y Return":     d.get("three_yr_return"),
        })
    df_peers = pd.DataFrame(rows).sort_values("Expense Ratio")

    # Format display
    def _er(v): return f"{v*100:.2f}%" if v else "—"
    def _ret(v): return f"{v*100:.1f}%" if v else "—"
    def _big(v):
        if not v: return "—"
        if v >= 1e12: return f"${v/1e12:.1f}T"
        if v >= 1e9:  return f"${v/1e9:.1f}B"
        return f"${v/1e6:.0f}M"

    df_disp = df_peers.copy()
    df_disp["Expense Ratio"] = df_disp["Expense Ratio"].apply(_er)
    df_disp["AUM"]           = df_disp["AUM"].apply(_big)
    df_disp["YTD Return"]    = df_disp["YTD Return"].apply(_ret)
    df_disp["3Y Return"]     = df_disp["3Y Return"].apply(_ret)
    st.dataframe(df_disp.set_index("Ticker"), use_container_width=True)

    # Cheaper alternatives callout
    my_er = peer_details.get(ticker, {}).get("expense_ratio") or 0
    cheaper = [(t, peer_details[t].get("expense_ratio") or 0)
               for t in peers if (peer_details[t].get("expense_ratio") or 0) < my_er]
    if cheaper:
        best_t, best_er = min(cheaper, key=lambda x: x[1])
        savings_bps = (my_er - best_er) * 10000
        savings_100k = (my_er - best_er) * 100_000
        st.markdown(f"""
<div class="callout">
  💡 <strong>Cheaper alternative found:</strong> <code>{best_t}</code> charges
  <strong>{best_er*100:.2f}%</strong> vs {ticker}'s <strong>{my_er*100:.2f}%</strong> —
  saving <strong>{savings_bps:.0f} bps</strong> or
  <strong>${savings_100k:,.0f}/yr</strong> on a $100K position.
</div>
""", unsafe_allow_html=True)

# ── Footer ────────────────────────────────────────────────────────────────────
st.divider()
st.caption(DISCLOSURE)
