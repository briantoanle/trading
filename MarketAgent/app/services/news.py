from duckduckgo_search import DDGS
from typing import List
from datetime import datetime

from app.models.schemas import NewsItem

class NewsFetcher:
    """A class to fetch recent news for a given stock ticker."""

    def fetch_news(self, ticker: str, max_results: int = 3) -> List[NewsItem]:
        """
        Fetches recent news articles for a given ticker symbol.

        Args:
            ticker (str): The stock ticker symbol (e.g., 'AAPL').
            max_results (int): The maximum number of news items to return.

        Returns:
            List[NewsItem]: A list of NewsItem objects.
        """
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
                    published_date = datetime.now() # Fallback

                results.append(
                    NewsItem(
                        headline=r["title"],
                        url=r["url"],
                        source=r["source"],
                        date=published_date,
                    )
                )
        return results
