"""Shared chart utilities for the Stock Market Analyst dashboard."""

import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from typing import Optional


# ── Helpers ──────────────────────────────────────────────────────────────────

def _interp_zero_crossings(x: list, y: list):
    """Insert linearly-interpolated zero-crossing points into (x, y) series."""
    xs, ys = list(x), list(y)
    out_x, out_y = [], []
    for i in range(len(xs)):
        out_x.append(xs[i])
        out_y.append(ys[i])
        if i < len(xs) - 1 and ys[i] is not None and ys[i + 1] is not None:
            a, b = ys[i], ys[i + 1]
            if (a < 0 < b) or (a > 0 > b):
                # linear interpolation: t where value = 0
                t = a / (a - b)
                # interpolate x
                xa, xb = xs[i], xs[i + 1]
                if isinstance(xa, pd.Timestamp):
                    diff = (xb - xa).total_seconds()
                    xz = xa + pd.Timedelta(seconds=diff * t)
                else:
                    xz = xa + (xb - xa) * t
                out_x.append(xz)
                out_y.append(0.0)
    return out_x, out_y


def split_traces(
    dates: list,
    values: list,
    name: str = "",
    show_legend: bool = False,
) -> list[go.Scatter]:
    """
    Return [green_trace, red_trace] split at zero for a performance series.
    Values are expected to be pct-change or absolute-change from baseline (0 = flat).
    """
    dates_c, values_c = _interp_zero_crossings(dates, values)

    green_y = [v if v is not None and v >= 0 else None for v in values_c]
    red_y   = [v if v is not None and v <= 0 else None for v in values_c]

    def _scatter(y_series, color, leg_name):
        return go.Scatter(
            x=dates_c,
            y=y_series,
            mode="lines",
            line=dict(color=color, width=2),
            name=leg_name,
            showlegend=show_legend,
            connectgaps=False,
            hovertemplate="%{x|%b %d, %Y}<br>%{y:.2f}%<extra></extra>",
        )

    return [
        _scatter(green_y, "#26a69a", f"{name} ▲"),
        _scatter(red_y,   "#ef5350", f"{name} ▼"),
    ]


def _area_traces(dates: list, values: list, baseline: float) -> list[go.Scatter]:
    """Fill-to-zero area chart traces split green/red at baseline."""
    pct = [(v - baseline) / baseline * 100 if baseline else 0 for v in values]
    dates_c, pct_c = _interp_zero_crossings(dates, pct)

    green_y = [v if v >= 0 else 0 for v in pct_c]
    red_y   = [v if v <= 0 else 0 for v in pct_c]

    base_trace = go.Scatter(
        x=dates_c, y=pct_c, mode="lines",
        line=dict(color="rgba(255,255,255,0.3)", width=1.5),
        showlegend=False, hovertemplate="%{x|%b %d}<br>%{y:.2f}%<extra></extra>",
    )
    fill_green = go.Scatter(
        x=dates_c, y=green_y,
        fill="tozeroy", fillcolor="rgba(38,166,154,0.25)",
        line=dict(width=0), showlegend=False,
        hoverinfo="skip",
    )
    fill_red = go.Scatter(
        x=dates_c, y=red_y,
        fill="tozeroy", fillcolor="rgba(239,83,80,0.25)",
        line=dict(width=0), showlegend=False,
        hoverinfo="skip",
    )
    return [fill_green, fill_red, base_trace]


# ── Main chart function ───────────────────────────────────────────────────────

def render_price_chart(
    df: pd.DataFrame,
    ticker: str,
    view: str = "Performance",
    show_volume: bool = True,
    baseline_price: Optional[float] = None,
    height: int = 500,
) -> go.Figure:
    """
    Render a price chart with 4 views:
      - Performance : green/red split pct-change from period start (or baseline_price for 1D)
      - Price       : plain close line
      - Candlestick : OHLC candles
      - Area        : filled area split at baseline
    Volume overlay is drawn on a secondary y-axis when show_volume=True.
    """
    if df.empty:
        fig = go.Figure()
        fig.update_layout(template="plotly_dark", title=f"No data for {ticker}")
        return fig

    dates  = df.index.tolist()
    closes = df["Close"].tolist() if "Close" in df.columns else []
    opens  = df["Open"].tolist()  if "Open"  in df.columns else closes
    highs  = df["High"].tolist()  if "High"  in df.columns else closes
    lows   = df["Low"].tolist()   if "Low"   in df.columns else closes
    vols   = df["Volume"].tolist() if "Volume" in df.columns else []

    has_volume = show_volume and len(vols) > 0 and any(v and v > 0 for v in vols)

    # Baseline: explicit param (for 1D intraday) or first close in period
    base = baseline_price if baseline_price is not None else (closes[0] if closes else 1)

    row_heights = [0.75, 0.25] if has_volume else [1.0]
    rows = 2 if has_volume else 1
    specs = [[{"secondary_y": False}]] * rows

    fig = make_subplots(
        rows=rows, cols=1,
        shared_xaxes=True,
        row_heights=row_heights,
        vertical_spacing=0.03,
        specs=specs,
    )

    # ── Price traces ─────────────────────────────────────────────────────────
    if view == "Performance":
        pct = [(c - base) / base * 100 if base else 0 for c in closes]
        for tr in split_traces(dates, pct, name=ticker):
            fig.add_trace(tr, row=1, col=1)

        # Return badge annotation
        if pct:
            last_pct = pct[-1]
            color = "#26a69a" if last_pct >= 0 else "#ef5350"
            sign  = "+" if last_pct >= 0 else ""
            fig.add_annotation(
                x=dates[-1], y=last_pct,
                text=f"  {sign}{last_pct:.2f}%",
                showarrow=False, font=dict(color=color, size=13, family="monospace"),
                xanchor="left", yanchor="middle",
            )
        fig.update_yaxes(ticksuffix="%", row=1, col=1)

    elif view == "Price":
        last_close = closes[-1] if closes else None
        color = "#26a69a" if (last_close and last_close >= base) else "#ef5350"
        fig.add_trace(go.Scatter(
            x=dates, y=closes, mode="lines",
            line=dict(color=color, width=2),
            name=ticker,
            hovertemplate="%{x|%b %d, %Y}<br>$%{y:,.2f}<extra></extra>",
        ), row=1, col=1)
        if last_close:
            pct = (last_close - base) / base * 100 if base else 0
            sign = "+" if pct >= 0 else ""
            fig.add_annotation(
                x=dates[-1], y=last_close,
                text=f"  {sign}{pct:.2f}%",
                showarrow=False, font=dict(color=color, size=13, family="monospace"),
                xanchor="left", yanchor="middle",
            )

    elif view == "Candlestick":
        fig.add_trace(go.Candlestick(
            x=dates, open=opens, high=highs, low=lows, close=closes,
            name=ticker,
            increasing_line_color="#26a69a", decreasing_line_color="#ef5350",
            increasing_fillcolor="#26a69a", decreasing_fillcolor="#ef5350",
        ), row=1, col=1)
        fig.update_layout(xaxis_rangeslider_visible=False)

    elif view == "Area":
        for tr in _area_traces(dates, closes, base):
            fig.add_trace(tr, row=1, col=1)
        pct_last = (closes[-1] - base) / base * 100 if (closes and base) else 0
        color = "#26a69a" if pct_last >= 0 else "#ef5350"
        sign  = "+" if pct_last >= 0 else ""
        fig.add_annotation(
            x=dates[-1], y=pct_last,
            text=f"  {sign}{pct_last:.2f}%",
            showarrow=False, font=dict(color=color, size=13, family="monospace"),
            xanchor="left", yanchor="middle",
        )
        fig.update_yaxes(ticksuffix="%", row=1, col=1)

    # ── Volume bars ──────────────────────────────────────────────────────────
    if has_volume:
        vol_colors = []
        for i, v in enumerate(vols):
            if i == 0:
                vol_colors.append("#26a69a")
            else:
                vol_colors.append("#26a69a" if closes[i] >= closes[i - 1] else "#ef5350")
        fig.add_trace(go.Bar(
            x=dates, y=vols,
            name="Volume",
            marker_color=vol_colors,
            opacity=0.6,
            showlegend=False,
            hovertemplate="%{x|%b %d}<br>Vol: %{y:,.0f}<extra></extra>",
        ), row=2, col=1)
        fig.update_yaxes(
            title_text="Volume", tickformat=".2s",
            showgrid=False, row=2, col=1,
        )

    # ── Layout ───────────────────────────────────────────────────────────────
    fig.update_layout(
        template="plotly_dark",
        height=height,
        margin=dict(l=10, r=60, t=30, b=10),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
        hovermode="x unified",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    fig.update_xaxes(showgrid=False, zeroline=False)
    fig.update_yaxes(showgrid=True, gridcolor="rgba(255,255,255,0.07)", zeroline=True,
                     zerolinecolor="rgba(255,255,255,0.2)", row=1, col=1)

    return fig


def render_sparkline(dates: list, values: list, baseline: float, height: int = 60, width: int = 120) -> go.Figure:
    """Compact sparkline with green/red split for metric cards."""
    if not values:
        return go.Figure()

    pct = [(v - baseline) / baseline * 100 if baseline else 0 for v in values]
    traces = split_traces(dates, pct)

    fig = go.Figure(data=traces)
    fig.update_layout(
        template="plotly_dark",
        height=height,
        width=width,
        margin=dict(l=0, r=0, t=0, b=0),
        showlegend=False,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
        hovermode=False,
    )
    return fig
