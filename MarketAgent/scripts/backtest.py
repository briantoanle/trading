"""Simple backtesting script for the AnalysisEngine."""
from __future__ import annotations

from typing import Optional

import pandas as pd
import pandas_ta as ta
import yfinance as yf

from app.analysis.engine import AnalysisEngine
from app.models.schemas import MarketData


def _prepare_market_data(df: pd.DataFrame, index: int, ticker: str) -> Optional[MarketData]:
    """Build a MarketData snapshot from the DataFrame up to a given index."""
    row = df.iloc[index]

    if pd.isna(row["RSI_14"]) or pd.isna(row["EMA_50"]):
        return None

    return MarketData(
        ticker=ticker,
        ohlcv=df.iloc[: index + 1],
        rsi=row["RSI_14"],
        ema_50=row["EMA_50"],
        current_price=row["Close"],
    )


def run_backtest(ticker: str = "NVDA") -> None:
    """Download historical data, simulate AnalysisEngine decisions, and report outcomes."""
    data = yf.download(ticker, period="60d", interval="1h")
    if data.empty:
        print("No data downloaded. Exiting.")
        return

    data.ta.rsi(length=14, append=True)
    data.ta.ema(length=50, append=True)

    engine = AnalysisEngine()

    buy_signals = 0
    successful_buys = 0

    for i in range(0, len(data)):
        if i % 4 != 0:
            continue

        market_data = _prepare_market_data(data, i, ticker)
        if not market_data:
            continue

        future_index = i + 24
        future_price = data.iloc[future_index]["Close"] if future_index < len(data) else None

        analysis = engine.analyze_ticker(
            ticker,
            market_data=market_data,
            news=[],
            use_provided_data=True,
        )

        if not analysis:
            continue

        signal, _, _ = analysis
        price_now = market_data.current_price

        profit_loss = None
        if future_price is not None:
            profit_loss = future_price - price_now

        result_text = f"{profit_loss:+.2f}" if profit_loss is not None else "N/A"
        print(f"{data.index[i]} | {price_now:.2f} | {signal.signal} | {result_text}")

        if signal.signal == "Buy" and profit_loss is not None:
            buy_signals += 1
            if profit_loss > 0:
                successful_buys += 1

    if buy_signals:
        win_rate = (successful_buys / buy_signals) * 100
    else:
        win_rate = 0.0

    print(
        f"Win Rate: {win_rate:.2f}% (Successful Buy signals: {successful_buys}/{buy_signals})"
    )


if __name__ == "__main__":
    run_backtest()
