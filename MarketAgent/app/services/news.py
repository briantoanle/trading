from duckduckgo_search import DDGS
from typing import List
from datetime import datetime
from loguru import logger

from app.models.schemas import NewsItem
from app.utils.resilience import retry_api_call


class NewsFetcher:
    """A class to fetch recent news for a given stock ticker."""

    @retry_api_call
    def fetch_news(self, ticker: str, max_results: int = 3) -> List[NewsItem]:
        """
        Fetches recent news articles for a given ticker symbol.
        """
        logger.info(f"Fetching news for {ticker}...")
        results = []
        with DDGS() as ddgs:
            # Search for news related to the ticker
            ddgs_news_gen = ddgs.news(
                keywords=ticker,
                region="us-en",
                safesearch="off",
                timelimit="d",  # Last 24 hours
            )

            for r in ddgs_news_gen:
                if len(results) >= max_results:
                    break

                # Convert DDG's date string to datetime
                try:
                    published_date = datetime.strptime(r["date"], "%Y-%m-%dT%H:%M:%S%z")
                except (ValueError, KeyError):
                    published_date = datetime.now()  # Fallback

                results.append(
                    NewsItem(
                        headline=r["title"],
                        url=r["url"],
                        source=r["source"],
                        date=published_date,
                    )
                )
        return results