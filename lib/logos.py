"""Ticker → domain map and base64 logo loader."""

import base64
import os
from pathlib import Path

ASSETS_DIR = Path(__file__).parent.parent / "assets" / "logos"

# ── Ticker → company domain map (top ~125 US tickers + ETFs) ─────────────────
TICKER_DOMAIN = {
    # Tech
    "AAPL":  "apple.com",        "MSFT":  "microsoft.com",
    "GOOGL": "google.com",       "GOOG":  "google.com",
    "META":  "meta.com",         "AMZN":  "amazon.com",
    "NVDA":  "nvidia.com",       "TSLA":  "tesla.com",
    "AVGO":  "broadcom.com",     "AMD":   "amd.com",
    "INTC":  "intel.com",        "QCOM":  "qualcomm.com",
    "TXN":   "ti.com",           "MU":    "micron.com",
    "AMAT":  "appliedmaterials.com", "LRCX": "lam-research.com",
    "KLAC":  "kla.com",          "ADI":   "analog.com",
    "MRVL":  "marvell.com",      "NXPI":  "nxp.com",
    "CRM":   "salesforce.com",   "NOW":   "servicenow.com",
    "ORCL":  "oracle.com",       "SAP":   "sap.com",
    "ADBE":  "adobe.com",        "INTU":  "intuit.com",
    "PANW":  "paloaltonetworks.com", "CRWD": "crowdstrike.com",
    "ZS":    "zscaler.com",      "SNOW":  "snowflake.com",
    "PLTR":  "palantir.com",     "NET":   "cloudflare.com",
    "DDOG":  "datadoghq.com",    "MDB":   "mongodb.com",
    "HUBS":  "hubspot.com",      "TEAM":  "atlassian.com",
    # Comms / Media
    "NFLX":  "netflix.com",      "DIS":   "disney.com",
    "CMCSA": "comcast.com",      "T":     "att.com",
    "VZ":    "verizon.com",      "TMUS":  "t-mobile.com",
    "SPOT":  "spotify.com",      "ROKU":  "roku.com",
    # Financials
    "JPM":   "jpmorganchase.com","BAC":   "bankofamerica.com",
    "WFC":   "wellsfargo.com",   "GS":    "goldmansachs.com",
    "MS":    "morganstanley.com","C":     "citi.com",
    "BLK":   "blackrock.com",    "SCHW":  "schwab.com",
    "AXP":   "americanexpress.com", "V":  "visa.com",
    "MA":    "mastercard.com",   "PYPL":  "paypal.com",
    "SQ":    "squareup.com",     "COF":   "capitalone.com",
    "USB":   "usbank.com",       "PNC":   "pnc.com",
    "TFC":   "truist.com",       "MCO":   "moodys.com",
    "SPGI":  "spglobal.com",     "ICE":   "theice.com",
    # Health Care
    "UNH":   "unitedhealthgroup.com", "JNJ": "jnj.com",
    "LLY":   "lilly.com",        "ABT":   "abbott.com",
    "MRK":   "merck.com",        "TMO":   "thermofisher.com",
    "ABBV":  "abbvie.com",       "DHR":   "danaher.com",
    "PFE":   "pfizer.com",       "AMGN":  "amgen.com",
    "GILD":  "gilead.com",       "ISRG":  "intuitivesurgical.com",
    "BMY":   "bms.com",          "CVS":   "cvshealth.com",
    "MDT":   "medtronic.com",    "BSX":   "bostonscientific.com",
    # Consumer
    "AMZN":  "amazon.com",       "WMT":   "walmart.com",
    "COST":  "costco.com",       "HD":    "homedepot.com",
    "MCD":   "mcdonalds.com",    "SBUX":  "starbucks.com",
    "NKE":   "nike.com",         "LOW":   "lowes.com",
    "TGT":   "target.com",       "BKNG":  "booking.com",
    "MAR":   "marriott.com",     "CMG":   "chipotle.com",
    "PG":    "pg.com",           "KO":    "coca-cola.com",
    "PEP":   "pepsico.com",      "PM":    "pmi.com",
    "MO":    "altria.com",       "CL":    "colgate.com",
    "GIS":   "generalmills.com", "KHC":   "kraftheinzcompany.com",
    # Energy
    "XOM":   "exxonmobil.com",   "CVX":   "chevron.com",
    "COP":   "conocophillips.com","SLB":  "slb.com",
    "EOG":   "eogresources.com", "PSX":   "phillips66.com",
    "MPC":   "marathonpetroleum.com",
    # Industrials
    "GE":    "ge.com",           "HON":   "honeywell.com",
    "CAT":   "caterpillar.com",  "DE":    "deere.com",
    "RTX":   "rtx.com",          "LMT":   "lockheedmartin.com",
    "BA":    "boeing.com",       "UPS":   "ups.com",
    "FDX":   "fedex.com",        "NSC":   "norfolksouthern.com",
    "UNP":   "up.com",           "MMM":   "3m.com",
    # Utilities / Real Estate
    "NEE":   "nexteraenergy.com","DUK":   "duke-energy.com",
    "SO":    "southerncompany.com","AMT":  "americantower.com",
    "PLD":   "prologis.com",     "EQIX":  "equinix.com",
    # ETFs
    "SPY":   "ssga.com",         "QQQ":   "invesco.com",
    "IWM":   "blackrock.com",    "DIA":   "ssga.com",
    "VTI":   "vanguard.com",     "VEA":   "vanguard.com",
    "VWO":   "vanguard.com",     "AGG":   "blackrock.com",
    "BND":   "vanguard.com",     "GLD":   "ssga.com",
    "SLV":   "blackrock.com",    "TLT":   "blackrock.com",
    "HYG":   "blackrock.com",    "LQD":   "blackrock.com",
    "XLK":   "ssga.com",         "XLF":   "ssga.com",
    "XLV":   "ssga.com",         "XLE":   "ssga.com",
    "XLI":   "ssga.com",         "XLY":   "ssga.com",
    "XLP":   "ssga.com",         "XLU":   "ssga.com",
    "XLRE":  "ssga.com",         "XLB":   "ssga.com",
    "XLC":   "ssga.com",         "VIG":   "vanguard.com",
    "SCHD":  "schwab.com",       "ARKK":  "ark-funds.com",
}


def get_logo_b64(ticker: str) -> str | None:
    """
    Return a base64 data-URL for the ticker's logo, or None if not found.
    Searches assets/logos/<TICKER>.<ext> for png, svg, jpg, ico.
    """
    if not ASSETS_DIR.exists():
        return None
    for ext in ("png", "svg", "jpg", "jpeg", "ico"):
        path = ASSETS_DIR / f"{ticker.upper()}.{ext}"
        if path.exists():
            try:
                data   = path.read_bytes()
                b64    = base64.b64encode(data).decode()
                mime   = "image/svg+xml" if ext == "svg" else f"image/{ext}"
                return f"data:{mime};base64,{b64}"
            except Exception:
                pass
    return None


def logo_img_tag(ticker: str, size: int = 32) -> str:
    """Return an <img> HTML tag for the logo or a plain text fallback."""
    src = get_logo_b64(ticker)
    if src:
        return (
            f'<img src="{src}" width="{size}" height="{size}" '
            f'style="border-radius:4px;object-fit:contain;background:#1e1e2e;" '
            f'alt="{ticker}" />'
        )
    # Fallback: colored initial badge
    initials = ticker[:2].upper()
    return (
        f'<div style="width:{size}px;height:{size}px;border-radius:4px;'
        f'background:#334155;display:flex;align-items:center;justify-content:center;'
        f'font-size:{max(8, size//3)}px;font-weight:700;color:#94a3b8;">{initials}</div>'
    )
