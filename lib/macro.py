"""FRED macro indicator helpers."""

import os
import streamlit as st
import pandas as pd

# Lazy import so app doesn't crash if fredapi not installed
def _fred():
    try:
        from fredapi import Fred
        key = os.getenv("FRED_API_KEY")
        if not key:
            return None
        return Fred(api_key=key)
    except ImportError:
        return None


FRED_SERIES = {
    "Real GDP (QoQ %)":             "A191RL1Q225SBEA",
    "Unemployment Rate":            "UNRATE",
    "CPI YoY %":                    "CPIAUCSL",
    "Core CPI YoY %":               "CPILFESL",
    "Fed Funds Rate":               "FEDFUNDS",
    "10Y-2Y Spread (bps)":          "T10Y2Y",
    "Retail Sales MoM %":           "RSAFS",
    "Industrial Production":        "INDPRO",
    "PCE YoY %":                    "PCEPI",
    "Consumer Sentiment":           "UMCSENT",
}

YIELD_CURVE_SERIES = {
    "3M":  "DGS3MO",
    "6M":  "DGS6MO",
    "1Y":  "DGS1",
    "2Y":  "DGS2",
    "5Y":  "DGS5",
    "7Y":  "DGS7",
    "10Y": "DGS10",
    "20Y": "DGS20",
    "30Y": "DGS30",
}


@st.cache_data(ttl=3600, show_spinner=False)
def get_fred_indicator(series_id: str, periods: int = 12) -> pd.Series:
    """Fetch a FRED series, return last N observations."""
    fred = _fred()
    if fred is None:
        return pd.Series(dtype=float)
    try:
        s = fred.get_series(series_id)
        return s.dropna().tail(periods)
    except Exception:
        return pd.Series(dtype=float)


@st.cache_data(ttl=3600, show_spinner=False)
def get_all_indicators() -> dict:
    """Return latest values for all macro indicators."""
    fred = _fred()
    if fred is None:
        return {}
    results = {}
    for name, sid in FRED_SERIES.items():
        try:
            s = fred.get_series(sid).dropna()
            if s.empty:
                continue
            latest = float(s.iloc[-1])
            prev   = float(s.iloc[-2]) if len(s) >= 2 else None
            results[name] = {
                "value":  latest,
                "prev":   prev,
                "delta":  latest - prev if prev is not None else None,
                "series": s.tail(24),
            }
        except Exception:
            continue
    return results


@st.cache_data(ttl=3600, show_spinner=False)
def get_yield_curve() -> dict:
    """Return {maturity_label: yield} for the current yield curve."""
    fred = _fred()
    if fred is None:
        return {}
    out = {}
    for label, sid in YIELD_CURVE_SERIES.items():
        try:
            s = fred.get_series(sid).dropna()
            if not s.empty:
                out[label] = float(s.iloc[-1])
        except Exception:
            continue
    return out
