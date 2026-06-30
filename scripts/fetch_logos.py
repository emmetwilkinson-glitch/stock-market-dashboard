"""
Download company/ETF logos into assets/logos/<TICKER>.<ext>.

Source priority:
  1. simple-icons via jsDelivr CDN  (SVG, post-process to fill="#ffffff")
  2. vectorlogo.zone                (SVG)
  3. apple-touch-icon from company domain
  4. Google FaviconV2 at size=256   (PNG)
  5. DuckDuckGo icon fallback       (PNG)

Usage:
  python scripts/fetch_logos.py
  python scripts/fetch_logos.py --tickers AAPL MSFT GOOGL
"""

import os
import re
import sys
import time
import argparse
import requests
from pathlib import Path

ASSETS_DIR = Path(__file__).parent.parent / "assets" / "logos"
ASSETS_DIR.mkdir(parents=True, exist_ok=True)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36"
    )
}
TIMEOUT = 10

# ── Ticker → company slug / domain map ───────────────────────────────────────
TICKER_META = {
    "AAPL":  ("apple",           "apple.com"),
    "MSFT":  ("microsoft",       "microsoft.com"),
    "GOOGL": ("google",          "google.com"),
    "GOOG":  ("google",          "google.com"),
    "META":  ("meta",            "meta.com"),
    "AMZN":  ("amazon",          "amazon.com"),
    "NVDA":  ("nvidia",          "nvidia.com"),
    "TSLA":  ("tesla",           "tesla.com"),
    "AVGO":  ("broadcom",        "broadcom.com"),
    "AMD":   ("amd",             "amd.com"),
    "INTC":  ("intel",           "intel.com"),
    "QCOM":  ("qualcomm",        "qualcomm.com"),
    "TXN":   ("texas-instruments","ti.com"),
    "MU":    ("micron-technology","micron.com"),
    "AMAT":  ("applied-materials","appliedmaterials.com"),
    "LRCX":  ("lam-research",    "lamresearch.com"),
    "CRM":   ("salesforce",      "salesforce.com"),
    "NOW":   ("servicenow",      "servicenow.com"),
    "ORCL":  ("oracle",          "oracle.com"),
    "ADBE":  ("adobe",           "adobe.com"),
    "INTU":  ("intuit",          "intuit.com"),
    "PANW":  ("palo-alto-networks","paloaltonetworks.com"),
    "CRWD":  ("crowdstrike",     "crowdstrike.com"),
    "ZS":    ("zscaler",         "zscaler.com"),
    "SNOW":  ("snowflake",       "snowflake.com"),
    "PLTR":  ("palantir",        "palantir.com"),
    "NET":   ("cloudflare",      "cloudflare.com"),
    "DDOG":  ("datadog",         "datadoghq.com"),
    "MDB":   ("mongodb",         "mongodb.com"),
    "NFLX":  ("netflix",         "netflix.com"),
    "DIS":   ("disney",          "disney.com"),
    "CMCSA": ("comcast",         "comcast.com"),
    "T":     ("att",             "att.com"),
    "VZ":    ("verizon",         "verizon.com"),
    "TMUS":  ("t-mobile",        "t-mobile.com"),
    "SPOT":  ("spotify",         "spotify.com"),
    "ROKU":  ("roku",            "roku.com"),
    "JPM":   ("jpmorgan-chase",  "jpmorganchase.com"),
    "BAC":   ("bank-of-america", "bankofamerica.com"),
    "WFC":   ("wells-fargo",     "wellsfargo.com"),
    "GS":    ("goldman-sachs",   "goldmansachs.com"),
    "MS":    ("morgan-stanley",  "morganstanley.com"),
    "C":     ("citigroup",       "citi.com"),
    "BLK":   ("blackrock",       "blackrock.com"),
    "V":     ("visa",            "visa.com"),
    "MA":    ("mastercard",      "mastercard.com"),
    "PYPL":  ("paypal",          "paypal.com"),
    "AXP":   ("american-express","americanexpress.com"),
    "UNH":   ("unitedhealth-group","unitedhealthgroup.com"),
    "JNJ":   ("johnson-and-johnson","jnj.com"),
    "LLY":   ("eli-lilly",       "lilly.com"),
    "ABT":   ("abbott-laboratories","abbott.com"),
    "MRK":   ("merck",           "merck.com"),
    "TMO":   ("thermo-fisher-scientific","thermofisher.com"),
    "ABBV":  ("abbvie",          "abbvie.com"),
    "PFE":   ("pfizer",          "pfizer.com"),
    "AMGN":  ("amgen",           "amgen.com"),
    "GILD":  ("gilead-sciences", "gilead.com"),
    "WMT":   ("walmart",         "walmart.com"),
    "COST":  ("costco",          "costco.com"),
    "HD":    ("the-home-depot",  "homedepot.com"),
    "MCD":   ("mcdonalds",       "mcdonalds.com"),
    "SBUX":  ("starbucks",       "starbucks.com"),
    "NKE":   ("nike",            "nike.com"),
    "LOW":   ("lowes",           "lowes.com"),
    "TGT":   ("target",          "target.com"),
    "PG":    ("procter-and-gamble","pg.com"),
    "KO":    ("coca-cola",       "coca-cola.com"),
    "PEP":   ("pepsi",           "pepsico.com"),
    "XOM":   ("exxon-mobil",     "exxonmobil.com"),
    "CVX":   ("chevron",         "chevron.com"),
    "GE":    ("general-electric","ge.com"),
    "HON":   ("honeywell",       "honeywell.com"),
    "CAT":   ("caterpillar",     "caterpillar.com"),
    "DE":    ("john-deere",      "deere.com"),
    "UPS":   ("ups",             "ups.com"),
    "FDX":   ("fedex",           "fedex.com"),
    "BA":    ("boeing",          "boeing.com"),
    "NEE":   ("nextera-energy",  "nexteraenergy.com"),
    "SCHW":  ("charles-schwab",  "schwab.com"),
    "SPY":   (None,              "ssga.com"),
    "QQQ":   (None,              "invesco.com"),
    "IWM":   (None,              "ishares.com"),
    "VTI":   (None,              "vanguard.com"),
    "VEA":   (None,              "vanguard.com"),
    "AGG":   (None,              "ishares.com"),
    "GLD":   (None,              "spdrgoldshares.com"),
    "TLT":   (None,              "ishares.com"),
    "XLK":   (None,              "ssga.com"),
    "XLF":   (None,              "ssga.com"),
    "XLV":   (None,              "ssga.com"),
    "XLE":   (None,              "ssga.com"),
    "XLI":   (None,              "ssga.com"),
    "XLY":   (None,              "ssga.com"),
    "XLP":   (None,              "ssga.com"),
    "XLU":   (None,              "ssga.com"),
    "XLRE":  (None,              "ssga.com"),
    "XLB":   (None,              "ssga.com"),
    "XLC":   (None,              "ssga.com"),
}


def _fix_svg_for_dark(content: bytes) -> bytes:
    """Replace fill colors with white so SVGs show on dark backgrounds."""
    text = content.decode("utf-8", errors="replace")
    # Set svg fill to white
    text = re.sub(r'<svg([^>]*?)>', r'<svg\1 fill="#ffffff">', text, count=1)
    # Override any fill in path/circle etc
    text = re.sub(r'fill="(?!none)[^"]*"', 'fill="#ffffff"', text)
    return text.encode("utf-8")


def _try_simple_icons(slug: str) -> bytes | None:
    if not slug:
        return None
    url = f"https://cdn.jsdelivr.net/npm/simple-icons@latest/icons/{slug}.svg"
    try:
        r = requests.get(url, timeout=TIMEOUT, headers=HEADERS)
        if r.status_code == 200 and b"<svg" in r.content:
            return _fix_svg_for_dark(r.content)
    except Exception:
        pass
    return None


def _try_vectorlogo(slug: str) -> bytes | None:
    if not slug:
        return None
    url = f"https://www.vectorlogo.zone/logos/{slug}/{slug}-icon.svg"
    try:
        r = requests.get(url, timeout=TIMEOUT, headers=HEADERS)
        if r.status_code == 200 and b"<svg" in r.content:
            return _fix_svg_for_dark(r.content)
    except Exception:
        pass
    return None


def _try_apple_touch(domain: str) -> bytes | None:
    if not domain:
        return None
    for path in ["/apple-touch-icon.png", "/apple-touch-icon-precomposed.png"]:
        url = f"https://{domain}{path}"
        try:
            r = requests.get(url, timeout=TIMEOUT, headers=HEADERS, allow_redirects=True)
            if r.status_code == 200 and r.content[:8].startswith(b"\x89PNG"):
                return r.content
        except Exception:
            pass
    return None


def _try_google_favicon(domain: str) -> bytes | None:
    if not domain:
        return None
    url = f"https://www.google.com/s2/favicons?domain={domain}&sz=256"
    try:
        r = requests.get(url, timeout=TIMEOUT, headers=HEADERS)
        if r.status_code == 200 and len(r.content) > 500:
            return r.content
    except Exception:
        pass
    return None


def _try_duckduckgo(domain: str) -> bytes | None:
    if not domain:
        return None
    url = f"https://icons.duckduckgo.com/ip3/{domain}.ico"
    try:
        r = requests.get(url, timeout=TIMEOUT, headers=HEADERS)
        if r.status_code == 200 and len(r.content) > 200:
            return r.content
    except Exception:
        pass
    return None


def fetch_logo(ticker: str) -> bool:
    """Try all sources for ticker. Return True if saved."""
    slug, domain = TICKER_META.get(ticker.upper(), (None, None))
    if not slug and not domain:
        print(f"  {ticker}: no metadata, skipping")
        return False

    steps = [
        ("simple-icons",   lambda: _try_simple_icons(slug), "svg"),
        ("vectorlogo.zone",lambda: _try_vectorlogo(slug),   "svg"),
        ("apple-touch",    lambda: _try_apple_touch(domain),"png"),
        ("google-favicon", lambda: _try_google_favicon(domain),"png"),
        ("duckduckgo",     lambda: _try_duckduckgo(domain), "ico"),
    ]
    for source, fn, ext in steps:
        data = fn()
        if data:
            out = ASSETS_DIR / f"{ticker.upper()}.{ext}"
            out.write_bytes(data)
            print(f"  {ticker}: ✓ {source} → {out.name}")
            return True
        time.sleep(0.05)

    print(f"  {ticker}: ✗ all sources failed")
    return False


def main():
    parser = argparse.ArgumentParser(description="Fetch logos for stock tickers")
    parser.add_argument("--tickers", nargs="*", help="Specific tickers to fetch")
    args = parser.parse_args()

    tickers = [t.upper() for t in args.tickers] if args.tickers else list(TICKER_META.keys())
    print(f"Fetching logos for {len(tickers)} tickers → {ASSETS_DIR}")
    ok = 0
    for t in tickers:
        if fetch_logo(t):
            ok += 1
        time.sleep(0.1)
    print(f"\nDone: {ok}/{len(tickers)} logos saved to {ASSETS_DIR}")


if __name__ == "__main__":
    main()
