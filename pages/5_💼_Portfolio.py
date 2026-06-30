"""Portfolio Tracker page."""

import os
from dotenv import load_dotenv
load_dotenv()

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd

from lib.config      import DISCLOSURE, APP_ICON
from lib.portfolio   import load_portfolio, save_portfolio, add_holding, remove_holding
from lib.market_data import get_quotes_bulk, get_history_bulk
from lib.risk        import portfolio_risk_score
from lib.claude_analyst import portfolio_analysis

st.set_page_config(page_title="Portfolio | Stock Market Analyst",
                   page_icon=APP_ICON, layout="wide")

st.markdown("""
<style>
  .main .block-container { font-size:17px; max-width:1400px; }
  .holding-row { padding:8px 0; border-bottom:1px solid #1e2d3d; }
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

st.title("💼 Portfolio Tracker")

# ── Add / Edit Holding ────────────────────────────────────────────────────────
with st.expander("➕ Add / Update Holding", expanded=False):
    with st.form("add_holding_form"):
        fc1, fc2, fc3, fc4 = st.columns([2, 1.5, 1.5, 2])
        in_ticker = fc1.text_input("Ticker", placeholder="e.g. AAPL").strip().upper()
        in_shares = fc2.number_input("Shares", min_value=0.0, step=0.001, format="%.3f")
        in_cost   = fc3.number_input("Avg Cost / Share ($)", min_value=0.0, step=0.01, format="%.2f")
        in_notes  = fc4.text_input("Notes (optional)", placeholder="e.g. IRA account")
        submitted = st.form_submit_button("Save Holding")
        if submitted:
            if not in_ticker:
                st.error("Ticker is required.")
            elif in_shares <= 0:
                st.error("Shares must be > 0.")
            else:
                add_holding(in_ticker, in_shares, in_cost, in_notes)
                st.success(f"Saved {in_ticker}.")
                st.rerun()

# ── Load Holdings ─────────────────────────────────────────────────────────────
holdings = load_portfolio()

if not holdings:
    st.info("No holdings yet. Use the form above to add your first position.")
    st.divider()
    st.caption(DISCLOSURE)
    st.stop()

tickers      = [h["ticker"] for h in holdings]
quotes       = get_quotes_bulk(tickers)
histories    = get_history_bulk(tickers, period="1y", interval="1wk")

# ── Portfolio Summary ─────────────────────────────────────────────────────────
total_value  = 0.0
total_cost   = 0.0
rows         = []
for h in holdings:
    tkr       = h["ticker"]
    shares    = h.get("shares", 0)
    cost_ps   = h.get("cost_basis", 0)
    q         = quotes.get(tkr, {})
    price     = q.get("price") or 0
    pct_day   = q.get("pct_change") or 0
    value     = price * shares
    cost      = cost_ps * shares
    gain      = value - cost
    gain_pct  = (gain / cost * 100) if cost else 0
    name      = q.get("name", tkr)[:25]
    total_value += value
    total_cost  += cost
    rows.append({
        "ticker":    tkr,
        "name":      name,
        "shares":    shares,
        "price":     price,
        "cost_ps":   cost_ps,
        "value":     value,
        "cost":      cost,
        "gain":      gain,
        "gain_pct":  gain_pct,
        "day_chg":   pct_day,
    })

total_gain  = total_value - total_cost
total_ret   = (total_gain / total_cost * 100) if total_cost else 0
risk_score, risk_label = portfolio_risk_score(holdings, histories)

# ── Summary metrics ───────────────────────────────────────────────────────────
st.subheader("📊 Portfolio Overview")
mc = st.columns(5)
mc[0].metric("Total Value",   f"${total_value:,.2f}")
mc[1].metric("Total Cost",    f"${total_cost:,.2f}")
mc[2].metric("Total Gain",    f"${total_gain:,.2f}", f"{total_ret:+.1f}%",
             delta_color="normal" if total_gain >= 0 else "inverse")
mc[3].metric("Positions",     str(len(holdings)))
mc[4].metric("Risk Profile",  risk_label)

st.divider()

# ── Holdings Table ────────────────────────────────────────────────────────────
st.subheader("📋 Holdings")
col_names = ["Ticker", "Name", "Shares", "Price", "Cost/Share", "Value", "Gain ($)", "Gain (%)", "Day %"]
table_rows = []
for r in rows:
    g_c = "🟢" if r["gain"] >= 0 else "🔴"
    d_c = "🟢" if r["day_chg"] >= 0 else "🔴"
    table_rows.append({
        "Ticker":     r["ticker"],
        "Name":       r["name"],
        "Shares":     f"{r['shares']:.3f}",
        "Price":      f"${r['price']:,.2f}",
        "Cost/Share": f"${r['cost_ps']:,.2f}",
        "Value":      f"${r['value']:,.2f}",
        "Gain ($)":   f"{g_c} ${abs(r['gain']):,.2f}",
        "Gain (%)":   f"{r['gain_pct']:+.2f}%",
        "Day %":      f"{d_c} {r['day_chg']:+.2f}%",
    })
st.dataframe(pd.DataFrame(table_rows).set_index("Ticker"), use_container_width=True)

# Remove holding
rem_tickers = [r["ticker"] for r in rows]
to_remove   = st.selectbox("Remove a holding", ["—"] + rem_tickers)
if to_remove != "—" and st.button(f"Remove {to_remove}", type="secondary"):
    remove_holding(to_remove)
    st.success(f"Removed {to_remove}.")
    st.rerun()

st.divider()

# ── Charts ────────────────────────────────────────────────────────────────────
ch1, ch2 = st.columns(2)

with ch1:
    st.markdown("**Allocation by Value**")
    labels = [r["ticker"] for r in rows]
    values = [r["value"] for r in rows]
    fig_pie = go.Figure(go.Pie(
        labels=labels, values=values,
        hole=0.45, showlegend=True,
        textinfo="label+percent",
        marker=dict(line=dict(color="#0f1117", width=2)),
    ))
    fig_pie.update_layout(
        template="plotly_dark", height=320,
        margin=dict(l=10, r=10, t=20, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
    )
    st.plotly_chart(fig_pie, use_container_width=True, key="port_pie")

with ch2:
    st.markdown("**Return by Position**")
    df_bar = pd.DataFrame({"Ticker": [r["ticker"] for r in rows],
                            "Return (%)": [r["gain_pct"] for r in rows]})
    df_bar = df_bar.sort_values("Return (%)", ascending=True)
    colors = ["#26a69a" if v >= 0 else "#ef5350" for v in df_bar["Return (%)"]]
    fig_bar = go.Figure(go.Bar(
        x=df_bar["Return (%)"], y=df_bar["Ticker"],
        orientation="h", marker_color=colors,
        text=[f"{v:+.1f}%" for v in df_bar["Return (%)"]],
        textposition="outside",
    ))
    fig_bar.update_layout(
        template="plotly_dark", height=320,
        margin=dict(l=10, r=60, t=20, b=10),
        xaxis=dict(ticksuffix="%", zeroline=True, zerolinecolor="rgba(255,255,255,0.2)"),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    )
    st.plotly_chart(fig_bar, use_container_width=True, key="port_ret_bar")

st.divider()

# ── AI Portfolio Analysis ─────────────────────────────────────────────────────
st.subheader("🤖 AI Portfolio Analysis")
if st.button("Analyze Portfolio with Claude", key="port_claude_btn"):
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")
    if not anthropic_key:
        st.warning(
            "**Anthropic API key not configured.**  \n"
            "Add `ANTHROPIC_API_KEY=your_key` to `.env`. "
            "Get a key at [console.anthropic.com](https://console.anthropic.com)."
        )
    else:
        with st.spinner("Analyzing with Claude…"):
            result = portfolio_analysis(holdings, quotes, risk_label)
        st.markdown(result)

# ── Footer ────────────────────────────────────────────────────────────────────
st.divider()
st.caption(DISCLOSURE)
