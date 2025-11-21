import yfinance as yf
import pandas_ta as ta
import pandas as pd
from typing import Optional

from app.models.schemas import MarketData

class MarketFetcher:
    """A class to fetch and process market data for a given stock ticker."""

    def fetch_market_data(self, ticker: str) -> Optional[MarketData]:
        """
        Fetches the last 5 days of hourly data and calculates technical indicators.

        Args:
            ticker (str): The stock ticker symbol to fetch data for.

        Returns:
            Optional[MarketData]: A MarketData object containing the fetched and
            processed data, or None if data could not be fetched.
        """
        stock = yf.Ticker(ticker)
        # Fetch last 5 days of hourly data
        hist: pd.DataFrame = stock.history(period="5d", interval="1h")

        if hist.empty:
            return None

        # Calculate RSI and EMA50
        hist.ta.rsi(length=14, append=True)
        hist.ta.ema(length=50, append=True)
        
        # Ensure columns were added
        rsi_col_name = "RSI_14"
        ema_col_name = "EMA_50"

        if rsi_col_name not in hist.columns or ema_col_name not in hist.columns:
             # Handle cases where indicators might not be calculated (e.g. not enough data)
            return None

        # Get the latest values
        latest_rsi = hist[rsi_col_name].iloc[-1]
        latest_ema = hist[ema_col_name].iloc[-1]
        latest_price = hist["Close"].iloc[-1]

        return MarketData(
            ticker=ticker,
            ohlcv=hist,
            rsi=latest_rsi,
            ema_50=latest_ema,
            current_price=latest_price,
        )
