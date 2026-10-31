from sqlalchemy import String, DateTime, Numeric, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime, timezone
from decimal import Decimal
from .database import Base

class Trade(Base):
    __tablename__ = "trades"
    __table_args__ = (UniqueConstraint("venue", "trade_id", name="uq_trade_venue_id"),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    venue: Mapped[str] = mapped_column(String(80), index=True)
    trade_id: Mapped[str] = mapped_column(String(120))
    symbol: Mapped[str] = mapped_column(String(40), index=True)
    side: Mapped[str] = mapped_column(String(4))
    quantity: Mapped[Decimal] = mapped_column(Numeric(24, 10))
    price: Mapped[Decimal] = mapped_column(Numeric(24, 10))
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True))

class Position(Base):
    __tablename__ = "positions"
    symbol: Mapped[str] = mapped_column(String(40), primary_key=True)
    quantity: Mapped[Decimal] = mapped_column(Numeric(24, 10), default=Decimal("0"))
    average_cost: Mapped[Decimal] = mapped_column(Numeric(24, 10), default=Decimal("0"))
    realized_pnl: Mapped[Decimal] = mapped_column(Numeric(24, 10), default=Decimal("0"))

class LatestPrice(Base):
    __tablename__ = "latest_prices"
    symbol: Mapped[str] = mapped_column(String(40), primary_key=True)
    price: Mapped[Decimal] = mapped_column(Numeric(24, 10))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
