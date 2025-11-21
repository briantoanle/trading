from datetime import datetime
from pathlib import Path
from typing import Optional

from sqlmodel import Field, SQLModel, create_engine


class TradeLog(SQLModel, table=True):
    """Represents a persisted trading decision."""

    id: Optional[int] = Field(default=None, primary_key=True)
    timestamp: datetime = Field(default_factory=datetime.utcnow, index=True)
    ticker: str
    signal: str
    confidence: float
    reasoning: str
    price_at_signal: float


def get_engine():
    """Return a SQLModel engine backed by a local SQLite database."""

    db_path = Path("market_agent.db")
    engine = create_engine(f"sqlite:///{db_path}")
    SQLModel.metadata.create_all(engine)
    return engine
