"""Anthropic Claude API calls for AI-powered financial analysis."""

import os
import streamlit as st

_KEY_VAR = "ANTHROPIC_API_KEY"
_MODEL   = "claude-haiku-4-5-20251001"
_MAX_TOK = 1500


def _client():
    """Return an Anthropic client or None if key is missing."""
    key = os.getenv(_KEY_VAR)
    if not key:
        return None
    try:
        import anthropic
        return anthropic.Anthropic(api_key=key)
    except ImportError:
        return None


def _call(system: str, user: str) -> str:
    """Make a Claude API call. Returns text or an error string."""
    client = _client()
    if client is None:
        return (
            "⚠️ **Anthropic API key not configured.** "
            "Add `ANTHROPIC_API_KEY=your_key` to your `.env` file. "
            "Get a free key at [console.anthropic.com](https://console.anthropic.com)."
        )
    try:
        msg = client.messages.create(
            model=_MODEL,
            max_tokens=_MAX_TOK,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        return msg.content[0].text
    except Exception as e:
        return f"⚠️ Claude API error: {e}"


# ── Shared system prompt ──────────────────────────────────────────────────────
_BASE_SYSTEM = (
    "You are a professional equity analyst assistant. Your role is to provide clear, "
    "factual, well-structured financial analysis for educational and research purposes. "
    "Always include a disclosure that this is not financial advice. "
    "Use markdown formatting. Be concise and data-driven."
)


def bull_bear_case(ticker: str, fundamentals: dict, tech_score: int, fund_score: int) -> str:
    """Generate bull / bear case for a stock."""
    pe    = fundamentals.get("pe_trailing")
    roe   = fundamentals.get("roe")
    beta  = fundamentals.get("beta")
    name  = fundamentals.get("name", ticker)
    rev_g = fundamentals.get("revenue_growth")
    nm    = fundamentals.get("net_margin")
    de    = fundamentals.get("debt_to_equity")
    rec   = fundamentals.get("recommendation", "N/A")

    prompt = f"""
Provide a concise **Bull Case** and **Bear Case** analysis for **{name} ({ticker})**.

Key metrics:
- Technical Score: {tech_score}/100
- Fundamental Score: {fund_score}/100
- Trailing P/E: {pe}
- ROE: {f"{roe*100:.1f}%" if roe else "N/A"}
- Net Margin: {f"{nm*100:.1f}%" if nm else "N/A"}
- Revenue Growth: {f"{rev_g*100:.1f}%" if rev_g else "N/A"}
- D/E Ratio: {de}
- Beta: {beta}
- Analyst Consensus: {rec}

Format:
## 🐂 Bull Case
[3-4 bullet points]

## 🐻 Bear Case
[3-4 bullet points]

## 📊 Overall View
[2-3 sentences]

---
*Disclosure: For educational purposes only. Not financial advice.*
"""
    return _call(_BASE_SYSTEM, prompt)


def deep_analysis(ticker: str, fundamentals: dict, tech_score: int, fund_score: int,
                  macro_context: str = "") -> str:
    """Generate a comprehensive stock analysis report."""
    name = fundamentals.get("name", ticker)
    prompt = f"""
Write a comprehensive equity research note for **{name} ({ticker})**.

Scores:
- Technical Score: {tech_score}/100
- Fundamental Score: {fund_score}/100

Fundamentals snapshot:
{_fmt_dict(fundamentals)}

{f"Macro context: {macro_context}" if macro_context else ""}

Cover: Business model, competitive positioning, financial health, valuation assessment,
technical setup, key risks, and a summary investment perspective.
Use markdown headers. Keep it under 600 words.

---
*Disclosure: For educational and research purposes only. Not financial advice.*
"""
    return _call(_BASE_SYSTEM, prompt)


def macro_pulse(indicators: dict, yield_curve: dict) -> str:
    """Generate a macro environment assessment."""
    ind_str = "\n".join(
        f"- {k}: {v['value']:.2f} (prev {v['prev']:.2f})" if v.get("prev") else f"- {k}: {v['value']:.2f}"
        for k, v in indicators.items()
    )
    yc_str  = ", ".join(f"{m}={y:.2f}%" for m, y in yield_curve.items()) if yield_curve else "Unavailable"

    prompt = f"""
Provide a concise macro environment pulse-check based on the current data.

Key indicators:
{ind_str}

Yield curve: {yc_str}

Cover:
1. Economic growth momentum
2. Inflation and Fed policy outlook
3. Yield curve implications (recession risk)
4. Equity market implications
5. Key risks to watch

Use markdown. ~400 words max.

---
*Disclosure: Educational only. Not financial advice.*
"""
    system = (
        "You are a macroeconomic analyst. Provide objective, data-driven commentary "
        "on the current economic environment for investors. Use markdown."
    )
    return _call(system, prompt)


def portfolio_analysis(holdings: list[dict], quotes: dict, risk_label: str) -> str:
    """Generate portfolio-level analysis."""
    lines = []
    for h in holdings:
        q = quotes.get(h["ticker"], {})
        price = q.get("price") or 0
        value = price * h.get("shares", 0)
        cost  = h.get("cost_basis", 0) * h.get("shares", 0)
        ret   = (value - cost) / cost * 100 if cost else 0
        lines.append(
            f"- {h['ticker']}: {h.get('shares',0):.1f} shares, "
            f"current ${value:,.0f}, return {ret:+.1f}%"
        )

    prompt = f"""
Analyse this personal investment portfolio:

Holdings:
{chr(10).join(lines)}

Portfolio risk profile: {risk_label}

Provide:
1. **Portfolio Assessment** — concentration, sector balance, geographic exposure
2. **Strengths** — what's working
3. **Risks & Weaknesses** — concerns, over-concentration, gaps
4. **Rebalancing Considerations** — areas to consider (not specific buy/sell advice)
5. **Summary** — overall profile

~400 words max. Use markdown.

---
*Disclosure: Educational only. Not financial advice.*
"""
    return _call(_BASE_SYSTEM, prompt)


def _fmt_dict(d: dict) -> str:
    lines = []
    for k, v in d.items():
        if v is None or k in ("description", "website", "name"):
            continue
        if isinstance(v, float):
            lines.append(f"- {k}: {v:.4g}")
        else:
            lines.append(f"- {k}: {v}")
    return "\n".join(lines[:25])
