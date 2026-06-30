"""Stock Analyzer — deep dive on any stock."""

import os
from dotenv import load_dotenv
load_dotenv()

import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import math

from lib.config      import DISCLOSURE, APP_ICON
from lib.market_data import PERIOD_MAP, get_quote, get_history, get_stock_fundamentals, get_prev_close
from lib.charts      import render_price_chart
from lib.signals     import compute_technical_score, compute_fundamental_score, get_at_a_glance, get_recommendation
from lib.logos       import logo_img_tag, get_logo_b64
from lib.news        import ticker_news
from lib.claude_analyst import bull_bear_case, deep_analysis

st.set_page_config(page_title="Stock Analyzer | Stock Market Analyst",
                   page_icon=APP_ICON, layout="wide")

st.markdown("""
<style>
  .main .block-container { font-size:17px; max-width:1400px; }
  .chip {
    display:inline-block; padding:4px 10px; border-radius:20px;
    background:#1e2d3d; font-size:13px; margin:3px 2px; color:#cbd5e1;
    border:1px solid #2a3f55;
  }
  .stat-label { font-size:12px; color:#64748b; }
  .stat-value { font-size:16px; font-weight:600; }
  .gauge-title { font-size:15px; font-weight:700; text-align:center; margin-bottom:4px; }
  .rec-badge {
    display:inline-block; padding:6px 20px; border-radius:6px;
    font-weight:800; font-size:18px; letter-spacing:1px;
  }
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

st.title("🔍 Stock Analyzer")

# ── Ticker input ──────────────────────────────────────────────────────────────
col_in1, col_in2 = st.columns([2, 3])
with col_in1:
    ticker = st.text_input("Ticker symbol", value="AAPL", placeholder="e.g. MSFT").strip().upper()
with col_in2:
    periods   = list(PERIOD_MAP.keys())
    sel_period = st.segmented_control("Period", periods, default="1Y", key="sa_period")
    if not sel_period:
        sel_period = "1Y"

if not ticker:
    st.info("Enter a ticker symbol to begin.")
    st.stop()

p_cfg = PERIOD_MAP[sel_period]

# ── Load data ─────────────────────────────────────────────────────────────────
with st.spinner(f"Loading {ticker}…"):
    quote  = get_quote(ticker)
    fund   = get_stock_fundamentals(ticker)
    df     = get_history(ticker, period=p_cfg["period"], interval=p_cfg["interval"])
    prev_c = get_prev_close(ticker) if sel_period == "1D" else None

if quote.get("price") is None and df.empty:
    st.error(f"No data found for **{ticker}**. Check the ticker and try again.")
    st.stop()

# ── Header row ────────────────────────────────────────────────────────────────
price    = quote.get("price") or 0
pct      = quote.get("pct_change") or 0
mkt_cap  = fund.get("market_cap")
pe       = fund.get("pe_trailing")
beta     = fund.get("beta")
name     = fund.get("name") or quote.get("name") or ticker
sector   = fund.get("sector") or "—"
industry = fund.get("industry") or "—"

logo_src = get_logo_b64(ticker)
col_logo, col_info, col_metrics = st.columns([1, 3, 4])

with col_logo:
    if logo_src:
        st.image(logo_src, width=64)
    else:
        st.markdown(logo_img_tag(ticker, 64), unsafe_allow_html=True)

with col_info:
    pct_color = "#26a69a" if pct >= 0 else "#ef5350"
    sign      = "+" if pct >= 0 else ""
    st.markdown(f"### {name}")
    st.markdown(f"`{ticker}` · {sector} · {industry}")
    st.markdown(
        f'<span style="font-size:24px;font-weight:800;">${price:,.2f}</span> '
        f'<span style="color:{pct_color};font-size:16px;">{sign}{pct:.2f}%</span>',
        unsafe_allow_html=True
    )

with col_metrics:
    m1, m2, m3, m4 = st.columns(4)
    def _fmt_cap(v):
        if v is None: return "—"
        if v >= 1e12: return f"${v/1e12:.1f}T"
        if v >= 1e9:  return f"${v/1e9:.1f}B"
        if v >= 1e6:  return f"${v/1e6:.1f}M"
        return f"${v:,.0f}"
    m1.metric("Market Cap",  _fmt_cap(mkt_cap))
    m2.metric("Trailing P/E", f"{pe:.1f}×" if pe else "—")
    m3.metric("Beta",         f"{beta:.2f}" if beta else "—")
    m4.metric("52W High",     f"${fund.get('52w_high'):,.2f}" if fund.get("52w_high") else "—")

st.divider()

# ── Main Chart ────────────────────────────────────────────────────────────────
view_opts = ["Performance", "Price", "Candlestick", "Area"]
view_sel  = st.segmented_control("Chart view", view_opts, default="Performance", key="sa_chart_view")
if not view_sel:
    view_sel = "Performance"

if not df.empty:
    fig = render_price_chart(df, ticker, view=view_sel, show_volume=True,
                             baseline_price=prev_c, height=500)
    st.plotly_chart(fig, use_container_width=True, key="sa_main_chart")
else:
    st.info("Price history unavailable for this period.")

st.divider()

# ── Snapshot panel ────────────────────────────────────────────────────────────
st.subheader("📊 Snapshot")

tech_score, tech_bullets = compute_technical_score(df, fund)
fund_score, fund_bullets = compute_fundamental_score(fund)
rec_label, rec_color     = get_recommendation(tech_score, fund_score)
glance                   = get_at_a_glance(df, fund)

# Caption
combined = tech_score * 0.5 + fund_score * 0.5
st.markdown(
    f"**{name}** scores **{tech_score}/100** on technical strength and "
    f"**{fund_score}/100** on fundamental quality, for a combined score of "
    f"**{combined:.0f}/100**. "
    f"AI recommendation: "
    f'<span class="rec-badge" style="background:{rec_color}22;color:{rec_color};'
    f'border:1px solid {rec_color};">{rec_label}</span>',
    unsafe_allow_html=True
)

snap_left, snap_mid, snap_right = st.columns([1.2, 1, 1])

with snap_left:
    st.markdown("**At a Glance**")
    for label, value in glance.items():
        st.markdown(f'<span class="chip">**{label}:** {value}</span>', unsafe_allow_html=True)

def _gauge_fig(score: int, title: str, subtitle: str) -> go.Figure:
    """Render a gauge (0-100, red → green)."""
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=score,
        domain={"x": [0, 1], "y": [0, 1]},
        title={"text": f"<b>{title}</b><br><span style='font-size:11px;color:#94a3b8'>{subtitle}</span>",
               "font": {"size": 14, "color": "#e2e8f0"}},
        gauge={
            "axis": {"range": [0, 100], "tickwidth": 1, "tickcolor": "#4a4a6a"},
            "bar":  {"color": "#334155", "thickness": 0.2},
            "bgcolor": "rgba(0,0,0,0)",
            "borderwidth": 0,
            "steps": [
                {"range": [0,  20],  "color": "#7f1d1d"},
                {"range": [20, 40],  "color": "#991b1b"},
                {"range": [40, 60],  "color": "#78350f"},
                {"range": [60, 80],  "color": "#14532d"},
                {"range": [80, 100], "color": "#065f46"},
            ],
            "threshold": {
                "line":  {"color": "#f1f5f9", "width": 3},
                "thickness": 0.8,
                "value": score,
            },
        },
        number={"font": {"color": "#f1f5f9", "size": 36}, "suffix": "/100"},
    ))
    fig.update_layout(
        template="plotly_dark",
        height=240,
        margin=dict(l=10, r=10, t=60, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    return fig

with snap_mid:
    fig_t = _gauge_fig(tech_score, "Technical Strength",
                       "Trend, momentum, position vs averages")
    st.plotly_chart(fig_t, use_container_width=True, key="sa_tech_gauge")
    for b in tech_bullets[:4]:
        st.markdown(f"• {b}")

with snap_right:
    fig_f = _gauge_fig(fund_score, "Fundamental Quality",
                       "Margins, returns, leverage, growth")
    st.plotly_chart(fig_f, use_container_width=True, key="sa_fund_gauge")
    for b in fund_bullets[:4]:
        st.markdown(f"• {b}")

st.divider()

# ── Key Statistics ────────────────────────────────────────────────────────────
st.subheader("📋 Key Statistics")

def _fmt(v, fmt=".2f", suffix="", pct=False, mul=1):
    if v is None: return "—"
    v *= mul
    if pct: v *= 100
    return f"{v:{fmt}}{suffix}"

def _fmt_big(v):
    if v is None: return "—"
    if abs(v) >= 1e12: return f"${v/1e12:.2f}T"
    if abs(v) >= 1e9:  return f"${v/1e9:.2f}B"
    if abs(v) >= 1e6:  return f"${v/1e6:.2f}M"
    return f"${v:,.0f}"

stat_cols = st.columns(3)
sections = [
    ("Valuation", [
        ("Trailing P/E",     _fmt(fund.get("pe_trailing"), ".1f", "×")),
        ("Forward P/E",      _fmt(fund.get("pe_forward"),  ".1f", "×")),
        ("Price/Book",       _fmt(fund.get("price_to_book"),".1f","×")),
        ("EV/EBITDA",        _fmt(fund.get("ev_to_ebitda"),".1f","×")),
        ("Price/Sales",      _fmt(fund.get("price_to_sales"),".2f","×")),
        ("PEG Ratio",        _fmt(fund.get("peg_ratio"),   ".2f")),
    ]),
    ("Profitability", [
        ("Gross Margin",     _fmt(fund.get("gross_margin"),   ".1f", "%", pct=True)),
        ("Operating Margin", _fmt(fund.get("operating_margin"),".1f","%", pct=True)),
        ("Net Margin",       _fmt(fund.get("net_margin"),     ".1f", "%", pct=True)),
        ("ROE",              _fmt(fund.get("roe"),            ".1f", "%", pct=True)),
        ("ROA",              _fmt(fund.get("roa"),            ".1f", "%", pct=True)),
        ("Free Cash Flow",   _fmt_big(fund.get("free_cashflow"))),
    ]),
    ("Balance Sheet", [
        ("Total Cash",       _fmt_big(fund.get("total_cash"))),
        ("Total Debt",       _fmt_big(fund.get("total_debt"))),
        ("D/E Ratio",        _fmt(fund.get("debt_to_equity"), ".0f", "%")),
        ("Current Ratio",    _fmt(fund.get("current_ratio"),  ".2f")),
        ("Quick Ratio",      _fmt(fund.get("quick_ratio"),    ".2f")),
        ("Enterprise Value", _fmt_big(fund.get("enterprise_value"))),
    ]),
    ("Trading", [
        ("52W High",         f"${fund.get('52w_high'):,.2f}" if fund.get("52w_high") else "—"),
        ("52W Low",          f"${fund.get('52w_low'):,.2f}"  if fund.get("52w_low")  else "—"),
        ("50-Day MA",        f"${fund.get('50d_avg'):,.2f}"  if fund.get("50d_avg")  else "—"),
        ("200-Day MA",       f"${fund.get('200d_avg'):,.2f}" if fund.get("200d_avg") else "—"),
        ("Avg Volume",       _fmt_big(fund.get("avg_volume")).replace("$","") if fund.get("avg_volume") else "—"),
        ("Short Ratio",      _fmt(fund.get("short_ratio"), ".1f", "d")),
    ]),
    ("Income", [
        ("Revenue (TTM)",    _fmt_big(fund.get("revenue"))),
        ("EBITDA",           _fmt_big(fund.get("ebitda"))),
        ("EPS (Trailing)",   f"${fund.get('eps_trailing'):.2f}" if fund.get("eps_trailing") else "—"),
        ("EPS (Forward)",    f"${fund.get('eps_forward'):.2f}"  if fund.get("eps_forward")  else "—"),
        ("Revenue Growth",   _fmt(fund.get("revenue_growth"),  ".1f", "%", pct=True)),
        ("Earnings Growth",  _fmt(fund.get("earnings_growth"), ".1f", "%", pct=True)),
    ]),
    ("Analyst", [
        ("Consensus",        (fund.get("recommendation") or "—").replace("_"," ").title()),
        ("# Analysts",       str(fund.get("num_analysts") or "—")),
        ("Price Target",     f"${fund.get('target_mean'):,.2f}" if fund.get("target_mean") else "—"),
        ("Target High",      f"${fund.get('target_high'):,.2f}" if fund.get("target_high") else "—"),
        ("Target Low",       f"${fund.get('target_low'):,.2f}"  if fund.get("target_low")  else "—"),
        ("Dividend Yield",   _fmt(fund.get("dividend_yield"), ".2f", "%", pct=True)),
    ]),
]

for i, (sec_name, rows) in enumerate(sections):
    with stat_cols[i % 3]:
        st.markdown(f"**{sec_name}**")
        for label, val in rows:
            c1, c2 = st.columns([3, 2])
            c1.markdown(f'<span class="stat-label">{label}</span>', unsafe_allow_html=True)
            c2.markdown(f'<span class="stat-value">{val}</span>', unsafe_allow_html=True)
        st.markdown("---")

# ── Business Summary ──────────────────────────────────────────────────────────
desc = fund.get("description")
if desc:
    with st.expander("📄 Business Summary"):
        st.write(desc)

st.divider()

# ── AI Analysis ──────────────────────────────────────────────────────────────
st.subheader("🤖 AI Analysis")
ai_tab1, ai_tab2, ai_tab3 = st.tabs(["🐂🐻 Bull / Bear Case", "📝 Deep Analysis", "📰 Headlines"])

with ai_tab1:
    if st.button("Generate Bull / Bear Case", key="sa_bb_btn"):
        with st.spinner("Analyzing with Claude…"):
            result = bull_bear_case(ticker, fund, tech_score, fund_score)
        st.markdown(result)

with ai_tab2:
    if st.button("Generate Deep Analysis", key="sa_deep_btn"):
        with st.spinner("Running deep analysis with Claude…"):
            result = deep_analysis(ticker, fund, tech_score, fund_score)
        st.markdown(result)

with ai_tab3:
    with st.spinner("Fetching headlines…"):
        articles = ticker_news(ticker, max_items=8)
    if articles:
        for art in articles:
            title = art.get("title", "")
            pub   = art.get("publisher", "")
            ago   = art.get("time_ago", "")
            summ  = art.get("summary", "")[:200]
            link  = art.get("link", "#")
            st.markdown(f"""
**[{title}]({link})**
<div style="font-size:12px;color:#64748b;">{pub} · {ago}</div>
{f'<div style="font-size:13px;color:#94a3b8;">{summ}</div>' if summ else ''}

""", unsafe_allow_html=True)
    else:
        st.info("No headlines found for this ticker.")

# ── Footer ────────────────────────────────────────────────────────────────────
st.divider()
st.caption(DISCLOSURE)
