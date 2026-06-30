"""ETF and portfolio risk scoring."""

import pandas as pd
import numpy as np
from typing import Optional


def etf_risk_score(df: pd.DataFrame, etf_details: dict) -> tuple[int, str]:
    """
    Compute ETF risk score 0-100 (0 = conservative, 100 = very aggressive).
    Factors:
      - Annualised volatility      40 pts
      - Max drawdown               35 pts
      - Concentration (top5 wt)   25 pts
    Returns (score, label).
    """
    if df.empty or "Close" not in df.columns or len(df) < 20:
        return 50, "Moderate"

    close = df["Close"].dropna()
    rets  = close.pct_change().dropna()

    # Annualised volatility
    ann_vol = float(rets.std() * np.sqrt(252)) * 100  # in %
    if ann_vol < 8:
        vol_pts = 5
    elif ann_vol < 12:
        vol_pts = 15
    elif ann_vol < 18:
        vol_pts = 25
    elif ann_vol < 25:
        vol_pts = 33
    else:
        vol_pts = 40

    # Max drawdown
    roll_max = close.cummax()
    drawdown = (close - roll_max) / roll_max
    max_dd   = float(drawdown.min()) * 100  # negative
    if max_dd > -5:
        dd_pts = 5
    elif max_dd > -10:
        dd_pts = 12
    elif max_dd > -20:
        dd_pts = 22
    elif max_dd > -35:
        dd_pts = 30
    else:
        dd_pts = 35

    # Concentration
    holdings = etf_details.get("holdings", [])
    if holdings:
        top5_wt = sum(h.get("weight", 0) for h in holdings[:5])
        if top5_wt < 0.20:
            conc_pts = 5
        elif top5_wt < 0.35:
            conc_pts = 12
        elif top5_wt < 0.50:
            conc_pts = 18
        else:
            conc_pts = 25
    else:
        conc_pts = 12  # neutral if unknown

    total = vol_pts + dd_pts + conc_pts

    if total < 20:
        label = "Conservative"
    elif total < 35:
        label = "Moderate-Conservative"
    elif total < 50:
        label = "Moderate"
    elif total < 65:
        label = "Moderate-Aggressive"
    elif total < 80:
        label = "Aggressive"
    else:
        label = "Very Aggressive"

    return min(100, max(0, total)), label


def portfolio_risk_score(holdings: list, histories: dict) -> tuple[int, str]:
    """
    Compute an overall portfolio risk score from constituent volatilities.
    holdings: list of {"ticker": ..., "shares": ..., "cost_basis": ...}
    histories: {ticker: DataFrame}
    """
    vols = []
    weights = []
    for h in holdings:
        t = h["ticker"]
        df = histories.get(t, pd.DataFrame())
        if df.empty or "Close" not in df.columns:
            continue
        close = df["Close"].dropna()
        if len(close) < 20:
            continue
        ann_vol = float(close.pct_change().dropna().std() * np.sqrt(252)) * 100
        shares  = h.get("shares", 0)
        price   = float(close.iloc[-1])
        value   = shares * price
        vols.append(ann_vol)
        weights.append(value)

    if not vols:
        return 50, "Moderate"

    total_val = sum(weights)
    if total_val <= 0:
        return 50, "Moderate"

    weighted_vol = sum(v * w for v, w in zip(vols, weights)) / total_val

    if weighted_vol < 8:
        score, label = 20, "Conservative"
    elif weighted_vol < 12:
        score, label = 35, "Moderate-Conservative"
    elif weighted_vol < 18:
        score, label = 50, "Moderate"
    elif weighted_vol < 25:
        score, label = 65, "Moderate-Aggressive"
    elif weighted_vol < 35:
        score, label = 80, "Aggressive"
    else:
        score, label = 95, "Very Aggressive"

    return score, label
