"""Curated ETF peer groups for cost comparison."""

# Each group: list of tickers tracking similar exposures
ETF_PEER_GROUPS = [
    # US Large Cap
    ["SPY", "IVV", "VOO", "SPLG"],
    # US Total Market
    ["VTI", "ITOT", "SCHB", "SPTM"],
    # Nasdaq 100
    ["QQQ", "QQQM", "ONEQ"],
    # US Small Cap
    ["IWM", "IJR", "VTWO", "SCHA"],
    # International Developed
    ["VEA", "IEFA", "EFA", "SCHF"],
    # Emerging Markets
    ["VWO", "EEM", "IEMG", "SCHE"],
    # US Aggregate Bond
    ["AGG", "BND", "IUSB", "SCHZ"],
    # Short-term Treasury
    ["SHY", "SCHO", "VGSH"],
    # Long-term Treasury
    ["TLT", "VGLT", "SPTL"],
    # TIPS
    ["TIP", "VTIP", "SCHP"],
    # High Yield
    ["HYG", "JNK", "USHY"],
    # Gold
    ["GLD", "IAU", "SGOL"],
    # Technology sector
    ["XLK", "VGT", "IYW", "FTEC"],
    # Financials sector
    ["XLF", "VFH", "IYF", "FNCL"],
    # Healthcare sector
    ["XLV", "VHT", "IYH", "FHLC"],
    # Energy sector
    ["XLE", "VDE", "IYE", "FENY"],
    # Dividend
    ["VIG", "SCHD", "DVY", "NOBL"],
    # Growth
    ["VUG", "IWF", "SCHG", "SPYG"],
    # Value
    ["VTV", "IWD", "SCHV", "SPYV"],
    # Real Estate
    ["VNQ", "XLRE", "IYR", "SCHH"],
]


def find_peers(ticker: str) -> list[str]:
    """Return peer tickers for a given ETF, excluding the ticker itself."""
    t = ticker.upper()
    for group in ETF_PEER_GROUPS:
        if t in group:
            return [x for x in group if x != t]
    return []
