"""Utility helpers for rendering lightweight price visualizations in the CLI."""

from __future__ import annotations

from typing import Iterable

import pandas as pd

from app.models.schemas import MarketData

SPARK_CHARS = "▁▂▃▄▅▆▇█"


def _normalize_value(value: float, minimum: float, maximum: float) -> int:
    if maximum == minimum:
        return len(SPARK_CHARS) // 2

    ratio = (value - minimum) / (maximum - minimum)
    ratio = max(0.0, min(1.0, ratio))
    return int(round(ratio * (len(SPARK_CHARS) - 1)))


def _build_series_line(series: Iterable[float], minimum: float, maximum: float) -> str:
    return "".join(SPARK_CHARS[_normalize_value(val, minimum, maximum)] for val in series)


def render_price_chart(market_data: MarketData, lookback: int = 30) -> str:
    """
    Render a simple ASCII sparkline of the close price (and EMA50 if available).
    """

    closes: pd.Series = market_data.ohlcv["Close"].tail(lookback)
    ema_series = (
        market_data.ohlcv["EMA_50"].tail(lookback)
        if "EMA_50" in market_data.ohlcv.columns
        else None
    )

    series_min = closes.min()
    series_max = closes.max()

    if ema_series is not None:
        series_min = min(series_min, ema_series.min())
        series_max = max(series_max, ema_series.max())

    if series_min == series_max:
        series_max += 1  # avoid divide-by-zero

    price_line = _build_series_line(closes, series_min, series_max)
    price_line = price_line[:-1] + "●" if len(price_line) > 1 else "●"

    lines = ["Price", price_line]

    if ema_series is not None:
        ema_line = _build_series_line(ema_series, series_min, series_max)
        lines.extend(["EMA50", ema_line])

    lines.append(
        f"Last close: ${closes.iloc[-1]:.2f} | EMA50: ${market_data.ema_50:.2f}"
    )

    return "\n".join(lines)
