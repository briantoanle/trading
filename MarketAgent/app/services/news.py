from datetime import datetime
from typing import List

from duckduckgo_search import DDGS
from loguru import logger

from app.models.schemas import NewsItem
from app.utils.resilience import retry_api_call


class NewsFetcher:
    """Fetches and normalizes recent news articles for a ticker symbol."""

    @retry_api_call
    def fetch_news(self, ticker: str, max_results: int = 3) -> List[NewsItem]:
        """Fetch recent news articles using the latest DuckDuckGo Search client."""
        logger.info(f"Fetching news for {ticker}...")
        results: List[NewsItem] = []

        with DDGS() as ddgs:
            # Modern DDGS client supports limiting results directly
            ddgs_news_gen = ddgs.news(
                keywords=ticker,
                region="us-en",
                safesearch="moderate",
                timelimit="d",  # Last 24 hours
                max_results=max_results,
            )

            for r in ddgs_news_gen:
                # Convert DDG's date string to datetime
                published_raw = r.get("date") or r.get("published")
                try:
                    published_date = datetime.fromisoformat(published_raw)
                except Exception:
                    published_date = datetime.now()  # Fallback

                results.append(
                    NewsItem(
                        headline=r.get("title", ""),
                        url=r.get("url") or r.get("href", ""),
                        source=r.get("source", "Unknown"),
                        date=published_date,
                    )
                )
        return results