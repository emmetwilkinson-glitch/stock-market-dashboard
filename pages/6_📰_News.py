"""News Page — market headlines and ticker-specific news."""

import os
from dotenv import load_dotenv
load_dotenv()

import streamlit as st
from lib.config  import DISCLOSURE, APP_ICON
from lib.news    import market_news, ticker_news

st.set_page_config(page_title="News | Stock Market Analyst",
                   page_icon=APP_ICON, layout="wide")

st.markdown("""
<style>
  .main .block-container { font-size:17px; max-width:1200px; }
  .news-card {
    background:#1e1e2e; border:1px solid #2a2a3e; border-radius:8px;
    padding:14px 16px; margin-bottom:10px;
  }
  .news-card a { text-decoration:none; color:#e2e8f0; }
  .news-card a:hover { color:#7dd3fc; }
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

st.title("📰 News")

tab_market, tab_ticker = st.tabs(["🌐 Market Headlines", "🔎 By Ticker"])

def render_articles(articles: list):
    if not articles:
        st.info("No news found.")
        return
    for art in articles:
        title = art.get("title", "Untitled")
        pub   = art.get("publisher", "")
        ago   = art.get("time_ago", "")
        summ  = art.get("summary", "")[:250]
        link  = art.get("link", "#")
        st.markdown(f"""
<div class="news-card">
  <a href="{link}" target="_blank"><strong>{title}</strong></a>
  <div style="font-size:12px;color:#64748b;margin-top:4px;">{pub}{' · ' + ago if ago else ''}</div>
  {f'<div style="font-size:13px;color:#94a3b8;margin-top:6px;">{summ}</div>' if summ else ''}
</div>
""", unsafe_allow_html=True)

with tab_market:
    with st.spinner("Fetching market headlines…"):
        articles = market_news(max_items=20)
    render_articles(articles)

with tab_ticker:
    col_t, _ = st.columns([2, 3])
    with col_t:
        tkr_input = st.text_input("Ticker symbol", placeholder="e.g. TSLA", key="news_ticker_input").strip().upper()
    if tkr_input:
        with st.spinner(f"Fetching news for {tkr_input}…"):
            articles = ticker_news(tkr_input, max_items=15)
        render_articles(articles)
    else:
        st.info("Enter a ticker above to search news.")

# ── Footer ────────────────────────────────────────────────────────────────────
st.divider()
st.caption(DISCLOSURE)
