"""yfinance wrappers for market data."""

import yfinance as yf
import pandas as pd
import streamlit as st
from datetime import datetime, timedelta

# ── Index / asset tickers (real indices, not ETFs) ──────────────────────────
INDEX_TICKERS = {
    "S&P 500":     "^GSPC",
    "Nasdaq 100":  "^NDX",
    "Dow Jones":   "^DJI",
    "Russell 2000":"^RUT",
    "VIX":         "^VIX",
    "10Y Yield":   "^TNX",
    "Gold":        "GC=F",
    "Crude WTI":   "CL=F",
    "Bitcoin":     "BTC-USD",
    "DXY":         "DX-Y.NYB",
}

# ── SPDR Sector ETFs ─────────────────────────────────────────────────────────
SECTOR_ETFS = {
    "Technology":         "XLK",
    "Financials":         "XLF",
    "Health Care":        "XLV",
    "Energy":             "XLE",
    "Industrials":        "XLI",
    "Consumer Discr.":    "XLY",
    "Consumer Staples":   "XLP",
    "Utilities":          "XLU",
    "Real Estate":        "XLRE",
    "Materials":          "XLB",
    "Communication Svcs": "XLC",
}

# ── Period map ───────────────────────────────────────────────────────────────
PERIOD_MAP = {
    "1D":  {"period": "1d",  "interval": "5m"},
    "5D":  {"period": "5d",  "interval": "30m"},
    "1M":  {"period": "1mo", "interval": "1d"},
    "3M":  {"period": "3mo", "interval": "1d"},
    "6M":  {"period": "6mo", "interval": "1d"},
    "YTD": {"period": "ytd", "interval": "1d"},
    "1Y":  {"period": "1y",  "interval": "1wk"},
    "3Y":  {"period": "3y",  "interval": "1wk"},
    "5Y":  {"period": "5y",  "interval": "1wk"},
    "10Y": {"period": "10y", "interval": "1mo"},
    "20Y": {"period": "20y", "interval": "1mo"},
    "30Y": {"period": "30y", "interval": "1mo"},
    "Max": {"period": "max", "interval": "1mo"},
}


@st.cache_data(ttl=60, show_spinner=False)
def get_quote(ticker: str) -> dict:
    """Return a flat dict of key quote fields for one ticker."""
    try:
        t = yf.Ticker(ticker)
        info = t.fast_info
        full = t.info or {}
        prev_close = getattr(info, "previous_close", None) or full.get("previousClose")
        price      = getattr(info, "last_price", None)     or full.get("currentPrice") or full.get("regularMarketPrice")
        if price is None:
            hist = t.history(period="2d", interval="1d")
            if not hist.empty:
                price = float(hist["Close"].iloc[-1])
                if len(hist) >= 2:
                    prev_close = float(hist["Close"].iloc[-2])
        change     = (price - prev_close) if (price and prev_close) else None
        pct_change = (change / prev_close * 100) if (change and prev_close) else None
        return {
            "ticker":      ticker,
            "name":        full.get("shortName") or full.get("longName") or ticker,
            "price":       price,
            "prev_close":  prev_close,
            "change":      change,
            "pct_change":  pct_change,
            "market_cap":  getattr(info, "market_cap", None) or full.get("marketCap"),
            "volume":      getattr(info, "three_month_average_volume", None) or full.get("volume"),
            "pe_trailing": full.get("trailingPE"),
            "beta":        full.get("beta"),
            "sector":      full.get("sector"),
            "industry":    full.get("industry"),
            "currency":    full.get("currency", "USD"),
        }
    except Exception:
        return {"ticker": ticker, "price": None, "pct_change": None}


@st.cache_data(ttl=300, show_spinner=False)
def get_history(ticker: str, period: str = "1y", interval: str = "1d") -> pd.DataFrame:
    """Return OHLCV history as a DataFrame with a DatetimeIndex."""
    try:
        df = yf.download(ticker, period=period, interval=interval,
                         progress=False, auto_adjust=True)
        if df.empty:
            return pd.DataFrame()
        # Flatten multi-level columns from yfinance 0.2+
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        df.index = pd.to_datetime(df.index)
        return df
    except Exception:
        return pd.DataFrame()


@st.cache_data(ttl=60, show_spinner=False)
def get_quotes_bulk(tickers: list) -> dict:
    """Return {ticker: quote_dict} for a list of tickers."""
    results = {}
    for t in tickers:
        results[t] = get_quote(t)
    return results


@st.cache_data(ttl=300, show_spinner=False)
def get_history_bulk(tickers: list, period: str = "1y", interval: str = "1d") -> dict:
    """Return {ticker: DataFrame} for multiple tickers."""
    results = {}
    for t in tickers:
        results[t] = get_history(t, period=period, interval=interval)
    return results


@st.cache_data(ttl=300, show_spinner=False)
def get_stock_fundamentals(ticker: str) -> dict:
    """Return rich fundamentals dict for a stock."""
    try:
        t = yf.Ticker(ticker)
        info = t.info or {}
        return {
            # Valuation
            "pe_trailing":       info.get("trailingPE"),
            "pe_forward":        info.get("forwardPE"),
            "price_to_book":     info.get("priceToBook"),
            "ev_to_ebitda":      info.get("enterpriseToEbitda"),
            "price_to_sales":    info.get("priceToSalesTrailing12Months"),
            "peg_ratio":         info.get("pegRatio"),
            # Profitability
            "gross_margin":      info.get("grossMargins"),
            "operating_margin":  info.get("operatingMargins"),
            "net_margin":        info.get("profitMargins"),
            "roe":               info.get("returnOnEquity"),
            "roa":               info.get("returnOnAssets"),
            "roic":              info.get("returnOnCapital"),
            # Balance sheet
            "debt_to_equity":    info.get("debtToEquity"),
            "current_ratio":     info.get("currentRatio"),
            "quick_ratio":       info.get("quickRatio"),
            "total_cash":        info.get("totalCash"),
            "total_debt":        info.get("totalDebt"),
            # Growth
            "revenue_growth":    info.get("revenueGrowth"),
            "earnings_growth":   info.get("earningsGrowth"),
            "revenue_qoq":       info.get("revenueQuarterlyGrowth"),
            # Dividend
            "dividend_yield":    info.get("dividendYield"),
            "payout_ratio":      info.get("payoutRatio"),
            # Trading
            "market_cap":        info.get("marketCap"),
            "enterprise_value":  info.get("enterpriseValue"),
            "beta":              info.get("beta"),
            "52w_high":          info.get("fiftyTwoWeekHigh"),
            "52w_low":           info.get("fiftyTwoWeekLow"),
            "50d_avg":           info.get("fiftyDayAverage"),
            "200d_avg":          info.get("twoHundredDayAverage"),
            "avg_volume":        info.get("averageVolume"),
            "shares_out":        info.get("sharesOutstanding"),
            "float_shares":      info.get("floatShares"),
            "short_ratio":       info.get("shortRatio"),
            # Income
            "revenue":           info.get("totalRevenue"),
            "ebitda":            info.get("ebitda"),
            "free_cashflow":     info.get("freeCashflow"),
            "eps_trailing":      info.get("trailingEps"),
            "eps_forward":       info.get("forwardEps"),
            # Analyst
            "target_mean":       info.get("targetMeanPrice"),
            "target_high":       info.get("targetHighPrice"),
            "target_low":        info.get("targetLowPrice"),
            "recommendation":    info.get("recommendationKey"),
            "num_analysts":      info.get("numberOfAnalystOpinions"),
            # Meta
            "name":              info.get("shortName") or info.get("longName"),
            "sector":            info.get("sector"),
            "industry":          info.get("industry"),
            "description":       info.get("longBusinessSummary"),
            "website":           info.get("website"),
            "employees":         info.get("fullTimeEmployees"),
            "country":           info.get("country"),
            "currency":          info.get("currency", "USD"),
        }
    except Exception:
        return {}


@st.cache_data(ttl=300, show_spinner=False)
def get_etf_details(ticker: str) -> dict:
    """Return ETF-specific details."""
    try:
        t = yf.Ticker(ticker)
        info = t.info or {}
        holdings = []
        try:
            h = t.funds_data
            if h and hasattr(h, 'top_holdings'):
                th = h.top_holdings
                if th is not None and not th.empty:
                    for sym, row in th.iterrows():
                        holdings.append({
                            "symbol": sym,
                            "name":   row.get("Name", sym),
                            "weight": row.get("Hold Percent", 0),
                        })
        except Exception:
            pass
        sector_weights = {}
        try:
            h = t.funds_data
            if h and hasattr(h, 'sector_weightings'):
                sw = h.sector_weightings
                if sw is not None and not sw.empty:
                    for _, row in sw.iterrows():
                        sector_weights[row.get("Sector", "Other")] = row.get("Percentage", 0)
        except Exception:
            pass
        return {
            "name":           info.get("shortName") or info.get("longName") or ticker,
            "category":       info.get("category"),
            "expense_ratio":  info.get("annualReportExpenseRatio") or info.get("totalExpenseRatio"),
            "aum":            info.get("totalAssets"),
            "nav":            info.get("navPrice") or info.get("previousClose"),
            "ytd_return":     info.get("ytdReturn"),
            "three_yr_return":info.get("threeYearAverageReturn"),
            "five_yr_return": info.get("fiveYearAverageReturn"),
            "beta":           info.get("beta3Year"),
            "holdings":       holdings,
            "sector_weights": sector_weights,
            "description":    info.get("longBusinessSummary"),
        }
    except Exception:
        return {}


@st.cache_data(ttl=300, show_spinner=False)
def is_etf(ticker: str) -> bool:
    """Return True if ticker appears to be an ETF."""
    try:
        info = yf.Ticker(ticker).info or {}
        qt = info.get("quoteType", "")
        return qt.upper() in ("ETF", "MUTUALFUND")
    except Exception:
        return False


def get_prev_close(ticker: str) -> float | None:
    """Fetch yesterday's close for intraday baseline."""
    try:
        hist = yf.Ticker(ticker).history(period="5d", interval="1d")
        if len(hist) >= 2:
            return float(hist["Close"].iloc[-2])
        elif len(hist) == 1:
            return float(hist["Close"].iloc[-1])
    except Exception:
        pass
    return None
