"""Macro Page — FRED indicators, yield curve, Claude macro pulse."""

import os
from dotenv import load_dotenv
load_dotenv()

import streamlit as st
import plotly.graph_objects as go
import pandas as pd

from lib.config  import DISCLOSURE, APP_ICON
from lib.macro   import get_all_indicators, get_yield_curve, FRED_SERIES
from lib.claude_analyst import macro_pulse

st.set_page_config(page_title="Macro | Stock Market Analyst",
                   page_icon=APP_ICON, layout="wide")

st.markdown("""
<style>
  .main .block-container { font-size:17px; max-width:1400px; }
  .macro-card {
    background:#1e1e2e; border:1px solid #2a2a3e; border-radius:10px;
    padding:14px; margin-bottom:10px;
  }
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

st.title("🌍 Macro Dashboard")

# ── FRED Key Check ────────────────────────────────────────────────────────────
fred_key = os.getenv("FRED_API_KEY")
if not fred_key:
    st.warning(
        "**FRED API key not configured.**  \n"
        "Add `FRED_API_KEY=your_key` to your `.env` file.  \n"
        "Get a free key at [fred.stlouisfed.org/docs/api/api_key.html]"
        "(https://fred.stlouisfed.org/docs/api/api_key.html) — "
        "it takes about 30 seconds."
    )
    st.stop()

# ── Load Indicators ───────────────────────────────────────────────────────────
with st.spinner("Loading FRED data…"):
    indicators  = get_all_indicators()
    yield_curve = get_yield_curve()

if not indicators:
    st.error("Could not load FRED data. Check your API key.")
    st.stop()

# ── Indicator Grid ────────────────────────────────────────────────────────────
st.subheader("📊 Key Economic Indicators")
ind_cols = st.columns(4)
for i, (name, data) in enumerate(indicators.items()):
    val   = data["value"]
    delta = data.get("delta")
    with ind_cols[i % 4]:
        # Format nicely
        if "%" in name or "Rate" in name or "Spread" in name or "CPI" in name or "PCE" in name:
            val_str   = f"{val:.2f}%"
            delta_str = f"{delta:+.2f}%" if delta is not None else None
        else:
            val_str   = f"{val:,.1f}"
            delta_str = f"{delta:+.2f}" if delta is not None else None
        st.metric(name.split("(")[0].strip(), val_str, delta_str)

st.divider()

# ── Indicator Charts ──────────────────────────────────────────────────────────
st.subheader("📈 Historical Trends")
chart_names = list(indicators.keys())
sel_ind = st.multiselect(
    "Select indicators to chart",
    chart_names,
    default=chart_names[:3],
    max_selections=4,
)

if sel_ind:
    ch_cols = st.columns(min(2, len(sel_ind)))
    for i, name in enumerate(sel_ind):
        data   = indicators[name]
        series = data.get("series", pd.Series(dtype=float))
        if series.empty:
            continue
        color = "#4a7ab5"
        fig = go.Figure(go.Scatter(
            x=series.index.tolist(),
            y=series.values.tolist(),
            mode="lines",
            line=dict(color=color, width=2),
            fill="tozeroy",
            fillcolor="rgba(74,122,181,0.15)",
            hovertemplate="%{x|%Y-%m}<br>%{y:.2f}<extra></extra>",
        ))
        fig.update_layout(
            template="plotly_dark", height=220, title=name,
            margin=dict(l=10, r=10, t=40, b=10),
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            xaxis=dict(showgrid=False), yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.07)"),
        )
        with ch_cols[i % 2]:
            st.plotly_chart(fig, use_container_width=True, key=f"macro_chart_{i}")

st.divider()

# ── Yield Curve ───────────────────────────────────────────────────────────────
st.subheader("📐 US Treasury Yield Curve")
if yield_curve:
    maturities = list(yield_curve.keys())
    yields     = list(yield_curve.values())
    fig_yc = go.Figure(go.Scatter(
        x=maturities, y=yields,
        mode="lines+markers",
        line=dict(color="#fbbf24", width=2.5),
        marker=dict(size=8, color="#fbbf24"),
        hovertemplate="%{x}<br>Yield: %{y:.2f}%<extra></extra>",
    ))
    # Shade inversion zones
    fig_yc.add_hline(y=0, line_dash="dot", line_color="rgba(255,255,255,0.2)")
    fig_yc.update_layout(
        template="plotly_dark", height=320,
        margin=dict(l=10, r=10, t=20, b=10),
        xaxis_title="Maturity", yaxis_title="Yield (%)",
        yaxis=dict(ticksuffix="%"),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    )
    st.plotly_chart(fig_yc, use_container_width=True, key="macro_yield_curve")

    # 10Y-2Y spread callout
    y2 = yield_curve.get("2Y")
    y10 = yield_curve.get("10Y")
    if y2 and y10:
        spread = y10 - y2
        color  = "#26a69a" if spread >= 0 else "#ef5350"
        label  = "normal" if spread >= 0 else "inverted (recession watch)"
        st.markdown(
            f'**10Y-2Y Spread: <span style="color:{color}">{spread:+.2f}%</span>** '
            f'— curve is currently **{label}**.',
            unsafe_allow_html=True
        )
else:
    st.info("Yield curve data unavailable. Check your FRED API key.")

st.divider()

# ── Claude Macro Pulse ────────────────────────────────────────────────────────
st.subheader("🤖 AI Macro Pulse-Check")
if st.button("Generate Macro Pulse with Claude", key="macro_claude_btn"):
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")
    if not anthropic_key:
        st.warning(
            "**Anthropic API key not configured.**  \n"
            "Add `ANTHROPIC_API_KEY=your_key` to `.env`. "
            "Get a key at [console.anthropic.com](https://console.anthropic.com)."
        )
    else:
        with st.spinner("Generating macro analysis with Claude…"):
            result = macro_pulse(indicators, yield_curve)
        st.markdown(result)

# ── Footer ────────────────────────────────────────────────────────────────────
st.divider()
st.caption(DISCLOSURE)
