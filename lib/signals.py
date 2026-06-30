"""Technical and fundamental scoring with buy/sell signals."""

import pandas as pd
import numpy as np
from typing import Optional


# ── Technical helpers ─────────────────────────────────────────────────────────

def _rsi(series: pd.Series, period: int = 14) -> float:
    """Compute RSI for the last value in a price series."""
    delta = series.diff()
    gain  = delta.clip(lower=0).rolling(period).mean()
    loss  = (-delta.clip(upper=0)).rolling(period).mean()
    rs    = gain / loss.replace(0, np.nan)
    rsi   = 100 - 100 / (1 + rs)
    return float(rsi.iloc[-1]) if not rsi.empty else 50.0


def _macd(series: pd.Series):
    """Return (macd_line, signal_line) last values."""
    ema12 = series.ewm(span=12, adjust=False).mean()
    ema26 = series.ewm(span=26, adjust=False).mean()
    macd  = ema12 - ema26
    sig   = macd.ewm(span=9, adjust=False).mean()
    return float(macd.iloc[-1]), float(sig.iloc[-1])


def compute_technical_score(df: pd.DataFrame, fundamentals: dict) -> tuple[int, list[str]]:
    """
    Returns (score 0-100, list of driver bullets).
    Weights:
      - 200DMA position      20
      - 50DMA position       15
      - RSI bucket           20
      - MACD signal          15
      - 52-week range pos.   15
      - Momentum (1M return) 15
    """
    if df.empty or "Close" not in df.columns:
        return 50, ["Insufficient price data"]

    close  = df["Close"].dropna()
    price  = float(close.iloc[-1])
    score  = 0
    bullets = []

    # 200DMA
    ma200 = float(close.rolling(200).mean().iloc[-1]) if len(close) >= 200 else None
    if ma200:
        if price > ma200:
            score += 20
            bullets.append(f"Price above 200-day MA (${ma200:,.2f})")
        else:
            bullets.append(f"Price below 200-day MA (${ma200:,.2f})")
    else:
        score += 10
        bullets.append("200-day MA unavailable (insufficient history)")

    # 50DMA
    ma50 = float(close.rolling(50).mean().iloc[-1]) if len(close) >= 50 else None
    if ma50:
        if price > ma50:
            score += 15
            bullets.append(f"Price above 50-day MA (${ma50:,.2f})")
        else:
            bullets.append(f"Price below 50-day MA (${ma50:,.2f})")
    else:
        score += 7
        bullets.append("50-day MA unavailable (insufficient history)")

    # RSI
    rsi_val = _rsi(close) if len(close) >= 15 else 50.0
    if 40 <= rsi_val <= 65:
        score += 20
        bullets.append(f"RSI {rsi_val:.0f} — healthy momentum zone")
    elif 65 < rsi_val <= 75:
        score += 12
        bullets.append(f"RSI {rsi_val:.0f} — approaching overbought")
    elif rsi_val > 75:
        score += 5
        bullets.append(f"RSI {rsi_val:.0f} — overbought territory")
    elif 30 <= rsi_val < 40:
        score += 12
        bullets.append(f"RSI {rsi_val:.0f} — oversold recovery zone")
    else:
        score += 5
        bullets.append(f"RSI {rsi_val:.0f} — oversold")

    # MACD
    if len(close) >= 27:
        macd_v, sig_v = _macd(close)
        if macd_v > sig_v:
            score += 15
            bullets.append(f"MACD bullish crossover (MACD {macd_v:.2f} > Signal {sig_v:.2f})")
        else:
            bullets.append(f"MACD bearish (MACD {macd_v:.2f} < Signal {sig_v:.2f})")
    else:
        score += 7

    # 52-week range
    high52 = fundamentals.get("52w_high") or float(close.tail(252).max())
    low52  = fundamentals.get("52w_low")  or float(close.tail(252).min())
    rng    = high52 - low52
    pos52  = (price - low52) / rng if rng > 0 else 0.5
    if pos52 >= 0.75:
        score += 15
        bullets.append(f"Near 52-week high — {pos52*100:.0f}% of annual range")
    elif pos52 >= 0.5:
        score += 10
        bullets.append(f"Mid 52-week range — {pos52*100:.0f}% of annual range")
    elif pos52 >= 0.25:
        score += 5
        bullets.append(f"Lower half of 52-week range — {pos52*100:.0f}%")
    else:
        bullets.append(f"Near 52-week low — {pos52*100:.0f}% of annual range")

    # 1-month momentum
    if len(close) >= 22:
        ret1m = (close.iloc[-1] / close.iloc[-22] - 1) * 100
        if ret1m > 5:
            score += 15
            bullets.append(f"Strong 1-month return: +{ret1m:.1f}%")
        elif ret1m > 0:
            score += 10
            bullets.append(f"Positive 1-month return: +{ret1m:.1f}%")
        elif ret1m > -5:
            score += 5
            bullets.append(f"Slight 1-month decline: {ret1m:.1f}%")
        else:
            bullets.append(f"Weak 1-month return: {ret1m:.1f}%")
    else:
        score += 7

    return min(100, max(0, score)), bullets


def compute_fundamental_score(fundamentals: dict) -> tuple[int, list[str]]:
    """
    Returns (score 0-100, list of driver bullets).
    Weights:
      - Profitability (ROE, net margin)  30
      - Valuation (P/E, P/B)            20
      - Leverage (D/E)                  20
      - Growth (rev / earnings)         15
      - Cash / dividend                 15
    """
    score   = 0
    bullets = []

    # Profitability
    roe = fundamentals.get("roe")
    nm  = fundamentals.get("net_margin")
    prof_pts = 0
    if roe is not None:
        if roe > 0.20:
            prof_pts += 15; bullets.append(f"ROE {roe*100:.1f}% — strong returns on equity")
        elif roe > 0.10:
            prof_pts += 10; bullets.append(f"ROE {roe*100:.1f}% — adequate returns on equity")
        elif roe > 0:
            prof_pts += 5;  bullets.append(f"ROE {roe*100:.1f}% — low returns on equity")
        else:
            bullets.append(f"ROE {roe*100:.1f}% — negative equity returns")
    else:
        prof_pts += 7
    if nm is not None:
        if nm > 0.15:
            prof_pts += 15; bullets.append(f"Net margin {nm*100:.1f}% — high profitability")
        elif nm > 0.05:
            prof_pts += 10; bullets.append(f"Net margin {nm*100:.1f}% — moderate profitability")
        elif nm > 0:
            prof_pts += 5;  bullets.append(f"Net margin {nm*100:.1f}% — thin margins")
        else:
            bullets.append(f"Net margin {nm*100:.1f}% — operating at a loss")
    else:
        prof_pts += 7
    score += min(30, prof_pts)

    # Valuation
    pe  = fundamentals.get("pe_trailing")
    pb  = fundamentals.get("price_to_book")
    val_pts = 0
    if pe is not None and pe > 0:
        if pe < 15:
            val_pts += 10; bullets.append(f"P/E {pe:.1f}× — low multiple")
        elif pe < 25:
            val_pts += 7;  bullets.append(f"P/E {pe:.1f}× — fair multiple")
        elif pe < 40:
            val_pts += 4;  bullets.append(f"P/E {pe:.1f}× — elevated multiple")
        else:
            bullets.append(f"P/E {pe:.1f}× — high multiple")
    else:
        val_pts += 5
    if pb is not None and pb > 0:
        if pb < 2:
            val_pts += 10; bullets.append(f"P/B {pb:.1f}× — below book value")
        elif pb < 5:
            val_pts += 7;  bullets.append(f"P/B {pb:.1f}× — reasonable book value")
        else:
            val_pts += 3;  bullets.append(f"P/B {pb:.1f}× — premium to book")
    else:
        val_pts += 5
    score += min(20, val_pts)

    # Leverage
    de = fundamentals.get("debt_to_equity")
    if de is not None:
        if de < 50:
            score += 20; bullets.append(f"D/E {de:.0f}% — conservative leverage")
        elif de < 150:
            score += 12; bullets.append(f"D/E {de:.0f}% — moderate leverage")
        elif de < 300:
            score += 6;  bullets.append(f"D/E {de:.0f}% — higher-than-market leverage")
        else:
            bullets.append(f"D/E {de:.0f}% — highly leveraged")
    else:
        score += 10

    # Growth
    rg = fundamentals.get("revenue_growth")
    eg = fundamentals.get("earnings_growth")
    grw_pts = 0
    if rg is not None:
        if rg > 0.15:
            grw_pts += 8; bullets.append(f"Revenue growth {rg*100:.1f}% YoY — strong")
        elif rg > 0.05:
            grw_pts += 5; bullets.append(f"Revenue growth {rg*100:.1f}% YoY — steady")
        elif rg >= 0:
            grw_pts += 2; bullets.append(f"Revenue growth {rg*100:.1f}% YoY — flat")
        else:
            bullets.append(f"Revenue declining {rg*100:.1f}% YoY")
    else:
        grw_pts += 4
    if eg is not None and eg > 0:
        grw_pts += 7; bullets.append(f"Earnings growth {eg*100:.1f}% YoY")
    elif eg is not None:
        bullets.append(f"Earnings declining {eg*100:.1f}% YoY")
    else:
        grw_pts += 3
    score += min(15, grw_pts)

    # Cash / dividend
    fcf  = fundamentals.get("free_cashflow")
    dyld = fundamentals.get("dividend_yield")
    cash_pts = 0
    if fcf and fcf > 0:
        cash_pts += 10; bullets.append("Positive free cash flow")
    elif fcf and fcf < 0:
        bullets.append("Negative free cash flow")
    else:
        cash_pts += 5
    if dyld and dyld > 0.01:
        cash_pts += 5; bullets.append(f"Dividend yield {dyld*100:.2f}%")
    score += min(15, cash_pts)

    return min(100, max(0, score)), bullets


def get_at_a_glance(df: pd.DataFrame, fundamentals: dict) -> dict:
    """
    Return descriptive neutral-language chips for the At-a-Glance panel.
    Keys: trend, momentum, range_pos, profitability, leverage, volatility, valuation
    """
    close = df["Close"].dropna() if not df.empty and "Close" in df.columns else pd.Series(dtype=float)
    price = float(close.iloc[-1]) if not close.empty else None

    # Trend
    ma200 = float(close.rolling(200).mean().iloc[-1]) if len(close) >= 200 else None
    if ma200 and price:
        trend = "Above 200-day MA" if price > ma200 else "Below 200-day MA"
    else:
        trend = "Trend unavailable"

    # Momentum (RSI)
    rsi_val = _rsi(close) if len(close) >= 15 else 50
    if rsi_val > 70:
        momentum = "Overbought (RSI {:.0f})".format(rsi_val)
    elif rsi_val > 55:
        momentum = "Firm momentum (RSI {:.0f})".format(rsi_val)
    elif rsi_val > 45:
        momentum = "Neutral (RSI {:.0f})".format(rsi_val)
    elif rsi_val > 30:
        momentum = "Weakening (RSI {:.0f})".format(rsi_val)
    else:
        momentum = "Oversold (RSI {:.0f})".format(rsi_val)

    # 52-week range position
    high52 = fundamentals.get("52w_high") or (float(close.tail(252).max()) if not close.empty else None)
    low52  = fundamentals.get("52w_low")  or (float(close.tail(252).min()) if not close.empty else None)
    if high52 and low52 and price and (high52 - low52) > 0:
        pos = (price - low52) / (high52 - low52) * 100
        range_pos = f"{pos:.0f}% of 52-week range"
    else:
        range_pos = "Range unavailable"

    # Profitability
    roe = fundamentals.get("roe")
    if roe is None:
        profitability = "Data unavailable"
    elif roe > 0.20:
        profitability = f"High ROE ({roe*100:.0f}%)"
    elif roe > 0.10:
        profitability = f"Moderate ROE ({roe*100:.0f}%)"
    elif roe > 0:
        profitability = f"Low ROE ({roe*100:.0f}%)"
    else:
        profitability = f"Negative ROE ({roe*100:.0f}%)"

    # Leverage
    de = fundamentals.get("debt_to_equity")
    if de is None:
        leverage = "Data unavailable"
    elif de < 50:
        leverage = f"Low D/E ({de:.0f}%)"
    elif de < 150:
        leverage = f"Moderate D/E ({de:.0f}%)"
    else:
        leverage = f"High D/E ({de:.0f}%)"

    # Volatility (beta)
    beta = fundamentals.get("beta")
    if beta is None:
        volatility = "Beta unavailable"
    elif beta < 0.8:
        volatility = f"Low volatility (β {beta:.2f})"
    elif beta < 1.2:
        volatility = f"Market-like volatility (β {beta:.2f})"
    elif beta < 1.8:
        volatility = f"Higher than market (β {beta:.2f})"
    else:
        volatility = f"High volatility (β {beta:.2f})"

    # Valuation
    pe = fundamentals.get("pe_trailing")
    if pe is None or pe <= 0:
        valuation = "P/E unavailable"
    elif pe < 15:
        valuation = f"Low multiple (P/E {pe:.1f}×)"
    elif pe < 25:
        valuation = f"Fair multiple (P/E {pe:.1f}×)"
    elif pe < 40:
        valuation = f"Elevated multiple (P/E {pe:.1f}×)"
    else:
        valuation = f"High multiple (P/E {pe:.1f}×)"

    return {
        "Trend":         trend,
        "Momentum":      momentum,
        "52-week range": range_pos,
        "Profitability": profitability,
        "Leverage":      leverage,
        "Volatility":    volatility,
        "Valuation":     valuation,
    }


def get_recommendation(tech_score: int, fund_score: int) -> tuple[str, str]:
    """
    Return (label, color) buy/sell/hold recommendation based on combined score.
    """
    combined = tech_score * 0.5 + fund_score * 0.5
    if combined >= 72:
        return "Buy", "#26a69a"
    elif combined >= 55:
        return "Accumulate", "#66bb6a"
    elif combined >= 42:
        return "Hold", "#ffa726"
    elif combined >= 28:
        return "Reduce", "#ef7b50"
    else:
        return "Sell", "#ef5350"
