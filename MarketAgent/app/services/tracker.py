from datetime import datetime
from typing import List

from sqlmodel import Session, select

from app.core.database import TradeLog, get_engine
from app.models.schemas import MarketData, TradeSignal


class PortfolioManager:
    """Handles persistence and retrieval of trade signals."""

    def __init__(self):
        self.engine = get_engine()

    def log_signal(self, signal: TradeSignal, market_data: MarketData) -> TradeLog:
        """Persist a generated trade signal to the database."""

        log_entry = TradeLog(
            timestamp=datetime.utcnow(),
            ticker=market_data.ticker,
            signal=signal.signal,
            confidence=signal.confidence,
            reasoning=signal.reasoning,
            price_at_signal=market_data.current_price,
        )

        with Session(self.engine) as session:
            session.add(log_entry)
            session.commit()
            session.refresh(log_entry)

        return log_entry

    def get_recent_signals(self, limit: int = 5) -> List[TradeLog]:
        """Retrieve the most recent trade signals."""

        with Session(self.engine) as session:
            statement = select(TradeLog).order_by(TradeLog.timestamp.desc()).limit(limit)
            results = session.exec(statement).all()
        return results
