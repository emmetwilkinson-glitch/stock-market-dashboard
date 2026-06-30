"""News fetchers using yfinance and Yahoo RSS fallback."""

import streamlit as st
import yfinance as yf
import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
import time


def _time_ago(dt) -> str:
    """Return human-readable 'X hours ago' string."""
    try:
        if isinstance(dt, (int, float)):
            dt = datetime.fromtimestamp(dt, tz=timezone.utc)
        elif isinstance(dt, str):
            # Try parsing ISO string
            dt = datetime.fromisoformat(dt.replace("Z", "+00:00"))
        now  = datetime.now(tz=timezone.utc)
        diff = now - dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None else now - dt
        secs = int(diff.total_seconds())
        if secs < 60:
            return "just now"
        elif secs < 3600:
            return f"{secs // 60}m ago"
        elif secs < 86400:
            return f"{secs // 3600}h ago"
        else:
            return f"{secs // 86400}d ago"
    except Exception:
        return ""


def _parse_yf_articles(articles: list) -> list[dict]:
    out = []
    for a in articles:
        if not isinstance(a, dict):
            continue
        # yfinance nests inside "content" or is flat
        content = a.get("content") or a
        title     = content.get("title")        or a.get("title")
        publisher = content.get("provider", {}).get("displayName") or \
                    content.get("publisher")    or a.get("publisher") or "Yahoo Finance"
        summary   = content.get("summary")      or a.get("summary") or ""
        link      = content.get("canonicalUrl", {}).get("url") or \
                    content.get("link")         or a.get("link") or "#"
        pub_time  = content.get("pubDate")      or content.get("displayTime") or \
                    a.get("providerPublishTime") or a.get("pubDate")
        if not title:
            continue
        out.append({
            "title":     title,
            "publisher": publisher,
            "summary":   summary,
            "link":      link,
            "time_ago":  _time_ago(pub_time) if pub_time else "",
        })
    return out


@st.cache_data(ttl=300, show_spinner=False)
def ticker_news(ticker: str, max_items: int = 10) -> list[dict]:
    """Return news articles for a specific ticker."""
    try:
        t = yf.Ticker(ticker)
        articles = t.news or []
        parsed   = _parse_yf_articles(articles)
        if parsed:
            return parsed[:max_items]
    except Exception:
        pass

    # Yahoo RSS fallback
    try:
        url  = f"https://feeds.finance.yahoo.com/rss/2.0/headline?s={ticker}&region=US&lang=en-US"
        resp = requests.get(url, timeout=8, headers={"User-Agent": "Mozilla/5.0"})
        root = ET.fromstring(resp.content)
        items = root.findall(".//item")
        out   = []
        for item in items[:max_items]:
            title = item.findtext("title", "")
            link  = item.findtext("link", "#")
            pub   = item.findtext("pubDate", "")
            if title:
                out.append({
                    "title":     title,
                    "publisher": "Yahoo Finance",
                    "summary":   "",
                    "link":      link,
                    "time_ago":  pub[:16] if pub else "",
                })
        return out
    except Exception:
        return []


@st.cache_data(ttl=300, show_spinner=False)
def market_news(max_items: int = 20) -> list[dict]:
    """Return general market news by querying a broad market ticker."""
    articles = []
    for ticker in ["^GSPC", "SPY", "QQQ"]:
        try:
            t     = yf.Ticker(ticker)
            items = t.news or []
            parsed = _parse_yf_articles(items)
            articles.extend(parsed)
            if len(articles) >= max_items * 2:
                break
        except Exception:
            continue

    # De-duplicate by title
    seen  = set()
    dedup = []
    for a in articles:
        key = a["title"][:60]
        if key not in seen:
            seen.add(key)
            dedup.append(a)

    # Yahoo Finance RSS market fallback
    if len(dedup) < 5:
        try:
            url  = "https://feeds.finance.yahoo.com/rss/2.0/headline?s=%5EGSPC&region=US&lang=en-US"
            resp = requests.get(url, timeout=8, headers={"User-Agent": "Mozilla/5.0"})
            root = ET.fromstring(resp.content)
            for item in root.findall(".//item"):
                title = item.findtext("title", "")
                link  = item.findtext("link", "#")
                pub   = item.findtext("pubDate", "")
                if title and title[:60] not in seen:
                    seen.add(title[:60])
                    dedup.append({
                        "title":     title,
                        "publisher": "Yahoo Finance",
                        "summary":   "",
                        "link":      link,
                        "time_ago":  pub[:16] if pub else "",
                    })
        except Exception:
            pass

    return dedup[:max_items]
