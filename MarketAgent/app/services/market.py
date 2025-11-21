import yfinance as yf
import pandas_ta as ta
import pandas as pd
from typing import Optional
from loguru import logger  # Import logger

from app.models.schemas import MarketData
from app.utils.resilience import retry_api_call  # Import the decorator


class MarketFetcher:
    """A class to fetch and process market data for a given stock ticker."""

    @retry_api_call  # Add the decorator here
    def fetch_market_data(self, ticker: str) -> Optional[MarketData]:
        """
        Fetches the last 5 days of hourly data and calculates technical indicators.
        """
        logger.info(f"Fetching market data for {ticker}...")  # Add logging
        stock = yf.Ticker(ticker)
        # Fetch last 5 days of hourly data
        hist: pd.DataFrame = stock.history(period="5d", interval="1h")

        if hist.empty:
            logger.warning(f"No data found for {ticker}")  # Add logging
            return None

        # Calculate RSI and EMA50
        hist.ta.rsi(length=14, append=True)
        hist.ta.ema(length=50, append=True)

        # Ensure columns were added
        rsi_col_name = "RSI_14"
        ema_col_name = "EMA_50"

        if rsi_col_name not in hist.columns or ema_col_name not in hist.columns:
            logger.warning(f"Indicators could not be calculated for {ticker}")
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