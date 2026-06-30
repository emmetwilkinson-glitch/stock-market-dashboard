"""Interest rate and treasury yield helpers using FRED."""

import streamlit as st
import pandas as pd
from lib.macro import get_fred_indicator, YIELD_CURVE_SERIES


@st.cache_data(ttl=3600, show_spinner=False)
def get_treasury_history(maturity: str = "10Y", periods: int = 252) -> pd.Series:
    """Return historical daily yield for a given maturity."""
    sid = YIELD_CURVE_SERIES.get(maturity)
    if not sid:
        return pd.Series(dtype=float)
    return get_fred_indicator(sid, periods=periods)


@st.cache_data(ttl=3600, show_spinner=False)
def get_spread_history(periods: int = 252) -> pd.Series:
    """Return 10Y-2Y spread history."""
    return get_fred_indicator("T10Y2Y", periods=periods)
