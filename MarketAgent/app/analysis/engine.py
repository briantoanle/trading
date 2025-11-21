import json
from typing import List, Optional, Tuple
import openai
import pandas as pd
from datetime import datetime, timedelta

from app.models.schemas import MarketData, NewsItem, TradeSignal
from app.services.market import MarketFetcher
from app.services.news import NewsFetcher
from app.core.config import settings

class AnalysisEngine:
    """
    The core analysis engine that uses an LLM to generate trade signals.
    """

    def __init__(self):
        """Initializes the AnalysisEngine and its components."""
        self.market_fetcher = MarketFetcher()
        self.news_fetcher = NewsFetcher()
        self.client = openai.OpenAI(
            base_url=settings.nvidia_api_base,
            api_key=settings.nvidia_api_key,
        )

    def _construct_system_prompt(self) -> str:
        """
        Builds the system prompt for the "Cynical Trader" persona.

        Returns:
            str: The system prompt string.
        """
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
        """
        Formats market data and news into a strict text block for the LLM.

        Args:
            market_data (MarketData): The market data for the ticker.
            news (List[NewsItem]): A list of recent news items.

        Returns:
            str: A formatted string containing all the context for the LLM.
        """
        # Format technical indicators
        tech_analysis = (
            f"Ticker: {market_data.ticker}\n"
            f"Current Price: ${market_data.current_price:.2f}\n"
            f"Relative Strength Index (RSI): {market_data.rsi:.2f}\n"
            f"50-Period EMA: {market_data.ema_50:.2f}\n"
        )

        # Format news
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

        Args:
            ticker (str): The stock ticker to analyze.
            mock (bool): If True, bypass the API and return a mock signal.

        Returns:
            Optional[Tuple[TradeSignal, MarketData, List[NewsItem]]]: A tuple containing
            the signal, market data, and news, or None if analysis fails.
        """
        if mock:
            return self._mock_analysis(ticker)

        market_data = self.market_fetcher.fetch_market_data(ticker)
        if not market_data:
            print(f"Could not retrieve market data for {ticker}.")
            return None

        news = self.news_fetcher.fetch_news(ticker)

        user_prompt = self._format_context(market_data, news)
        system_prompt = self._construct_system_prompt()

        try:
            response = self.client.chat.completions.create(
                model="meta/llama3-8b-instruct",  # Example model
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.3,
                max_tokens=256,
                response_format={"type": "json_object"},
            )

            response_content = response.choices[0].message.content
            if not response_content:
                return None

            signal_data = json.loads(response_content)
            signal = TradeSignal(**signal_data)
            return signal, market_data, news

        except openai.APIError as e:
            print(f"NVIDIA API Error: {e}")
            return None
        except json.JSONDecodeError:
            print(f"Failed to decode LLM response into JSON.")
            return None
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            return None

    def _mock_analysis(
        self, ticker: str
    ) -> Tuple[TradeSignal, MarketData, List[NewsItem]]:
        """
        Returns a hardcoded, dummy analysis package for testing.

        Args:
            ticker (str): The ticker being mocked.

        Returns:
            Tuple[TradeSignal, MarketData, List[NewsItem]]: A dummy analysis package.
        """
        mock_signal = TradeSignal(
            signal="Hold",
            confidence=0.65,
            reasoning=f"Mock analysis for {ticker}: Price is consolidating near the 50-day EMA. RSI is neutral. "
            "Waiting for a clearer catalyst before taking a position.",
            stop_loss=None,
        )
        
        # Create a dummy DataFrame for OHLCV
        dummy_df = pd.DataFrame({
            'Open': [150], 'High': [152], 'Low': [149], 'Close': [151], 'Volume': [1000000]
        })

        mock_market_data = MarketData(
            ticker=ticker,
            ohlcv=dummy_df,
            rsi=55.0,
            ema_50=150.5,
            current_price=151.00,
        )

        mock_news = [
            NewsItem(
                headline=f"{ticker} announces new AI chip, investors are cautiously optimistic.",
                url="https://example.com/news1",
                source="Mock News Service",
                date=datetime.now() - timedelta(hours=3),
            ),
            NewsItem(
                headline="Analysts debate future growth prospects for the semiconductor industry.",
                url="https://example.com/news2",
                source="Fauxancial Times",
                date=datetime.now() - timedelta(hours=8),
            ),
        ]

        return mock_signal, mock_market_data, mock_news
