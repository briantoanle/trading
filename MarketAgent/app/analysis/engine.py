import json
from typing import List, Optional, Tuple
import openai
import pandas as pd
from datetime import datetime, timedelta
from loguru import logger

from app.models.schemas import MarketData, NewsItem, TradeSignal
from app.core.config import settings
from app.services.market import MarketFetcher
from app.services.news import NewsFetcher
from app.services.tracker import PortfolioManager
from app.utils.resilience import clean_json_response, retry_api_call


class AnalysisEngine:
    """
    The core analysis engine that uses an LLM to generate trade signals.
    """

    def __init__(self):
        """Initializes the AnalysisEngine and its components."""
        self.market_fetcher = MarketFetcher()
        self.news_fetcher = NewsFetcher()
        self.portfolio_manager = PortfolioManager()
        self.client = openai.OpenAI(
            base_url=settings.nvidia_api_base,
            api_key=settings.nvidia_api_key,
        )

    def _construct_system_prompt(self) -> str:
        # ... (Keep existing implementation) ...
        return (
            "You are a cynical, quantitative hedge fund trader. Your focus is on risk aversion. "
            "You are analytical, data-driven, and deeply skeptical of market hype. "
            "Identify key trends, support/resistance levels, and any divergences between price action and indicators. "
            "Your analysis must be concise and based *only* on the data provided. "
            "Your final output *must* be a JSON object matching the requested schema with the fields: "
            "'signal' (Buy, Sell, Hold), 'confidence' (0.0-1.0), 'reasoning' (a brief, cynical analysis), "
            "and 'stop_loss' (a price or null)."
        )

    def _format_context(self, market_data: MarketData, news: List[NewsItem]) -> str:
        # ... (Keep existing implementation) ...
        tech_analysis = (
            f"Ticker: {market_data.ticker}\n"
            f"Current Price: ${market_data.current_price:.2f}\n"
            f"Relative Strength Index (RSI): {market_data.rsi:.2f}\n"
            f"50-Period EMA: {market_data.ema_50:.2f}\n"
        )

        news_headlines = "Recent Headlines:\n"
        if news:
            for item in news:
                news_headlines += f"- {item.headline} ({item.source})\n"
        else:
            news_headlines += "- No significant news in the last 24 hours.\n"

        return f"## Market Analysis Request\n\n### Technicals\n{tech_analysis}\n### Sentiment\n{news_headlines}"

    def analyze_ticker(
            self, ticker: str, mock: bool = False
    ) -> Optional[Tuple[TradeSignal, MarketData, List[NewsItem]]]:
        """
        Performs a full analysis of a given ticker and returns a trade signal.
        """
        if mock:
            logger.info(f"Running MOCK analysis for {ticker}")
            mock_result = self._mock_analysis(ticker)
            if mock_result:
                signal, market_data, _ = mock_result
                self.portfolio_manager.log_signal(signal, market_data)
            return mock_result

        # These calls now have automatic retries via the decorators in the classes
        market_data = self.market_fetcher.fetch_market_data(ticker)
        if not market_data:
            logger.error(f"Analysis aborted: Market data unavailable for {ticker}")
            return None

        news = self.news_fetcher.fetch_news(ticker)

        user_prompt = self._format_context(market_data, news)
        system_prompt = self._construct_system_prompt()

        try:
            logger.debug(f"Sending request to LLM for {ticker}...")
            response = self.client.chat.completions.create(
                model="meta/llama3-70b-instruct",  # Updated to 70B for better reasoning
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.3,
                max_tokens=512,
                # response_format={"type": "json_object"}, # Uncomment if model supports it strict
            )

            response_content = response.choices[0].message.content
            if not response_content:
                logger.error("LLM returned empty content.")
                return None

            # Use the robust cleaner instead of raw json.loads
            signal_data = clean_json_response(response_content)

            signal = TradeSignal(**signal_data)
            logger.success(f"Generated signal for {ticker}: {signal.signal}")
            self.portfolio_manager.log_signal(signal, market_data)
            return signal, market_data, news

        except openai.APIError as e:
            logger.error(f"NVIDIA API Error: {e}")
            return None
        except Exception as e:
            logger.exception(f"An unexpected error occurred during analysis: {e}")
            return None

    def _mock_analysis(self, ticker: str) -> Tuple[TradeSignal, MarketData, List[NewsItem]]:
        # ... (Keep existing implementation) ...
        # Just verify indentation is correct when pasting back
        # You can leave the rest of this function exactly as it was
        mock_signal = TradeSignal(
            signal="Hold",
            confidence=0.65,
            reasoning=f"Mock analysis for {ticker}: Price is consolidating near the 50-day EMA. RSI is neutral. Waiting for a clearer catalyst.",
            stop_loss=None,
        )

        dummy_df = pd.DataFrame({
            'Open': [150], 'High': [152], 'Low': [149], 'Close': [151], 'Volume': [1000000]
        })

        # Fix: Ensure column names match what schema expects or what market.py produces if mocked
        dummy_df['RSI_14'] = 55.0
        dummy_df['EMA_50'] = 150.5

        mock_market_data = MarketData(
            ticker=ticker,
            ohlcv=dummy_df,
            rsi=55.0,
            ema_50=150.5,
            current_price=151.00,
        )

        mock_news = [
            NewsItem(
                headline=f"{ticker} announces new AI chip.",
                url="https://example.com",
                source="Mock News",
                date=datetime.now(),
            )
        ]

        return mock_signal, mock_market_data, mock_news
