"""Load and save portfolio holdings to data/portfolio.json."""

import json
import os
from pathlib import Path

DATA_DIR  = Path(__file__).parent.parent / "data"
PORT_FILE = DATA_DIR / "portfolio.json"

DEFAULT_PORTFOLIO: list[dict] = []


def load_portfolio() -> list[dict]:
    """Return list of holdings: [{ticker, shares, cost_basis, notes}]."""
    try:
        if PORT_FILE.exists():
            with open(PORT_FILE, "r") as f:
                data = json.load(f)
            if isinstance(data, list):
                return data
    except Exception:
        pass
    return list(DEFAULT_PORTFOLIO)


def save_portfolio(holdings: list[dict]) -> None:
    """Persist holdings to disk."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(PORT_FILE, "w") as f:
        json.dump(holdings, f, indent=2)


def add_holding(ticker: str, shares: float, cost_basis: float, notes: str = "") -> list[dict]:
    holdings = load_portfolio()
    # Update if ticker already exists
    for h in holdings:
        if h["ticker"].upper() == ticker.upper():
            h["shares"]     = shares
            h["cost_basis"] = cost_basis
            h["notes"]      = notes
            save_portfolio(holdings)
            return holdings
    holdings.append({
        "ticker":     ticker.upper(),
        "shares":     shares,
        "cost_basis": cost_basis,
        "notes":      notes,
    })
    save_portfolio(holdings)
    return holdings


def remove_holding(ticker: str) -> list[dict]:
    holdings = load_portfolio()
    holdings = [h for h in holdings if h["ticker"].upper() != ticker.upper()]
    save_portfolio(holdings)
    return holdings
