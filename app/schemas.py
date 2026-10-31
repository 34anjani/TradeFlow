from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, ConfigDict, Field, field_validator
from typing import Literal

class TradeIn(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    venue: str = Field(min_length=1, max_length=80)
    trade_id: str = Field(min_length=1, max_length=120)
    symbol: str = Field(min_length=1, max_length=40)
    side: Literal["BUY", "SELL"]
    quantity: Decimal = Field(gt=0, max_digits=24, decimal_places=10)
    price: Decimal = Field(gt=0, max_digits=24, decimal_places=10)
    timestamp: datetime

    @field_validator("timestamp")
    @classmethod
    def timestamp_must_be_aware(cls, value):
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("timestamp must include a timezone, e.g. Z")
        return value

class TradeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    venue: str
    trade_id: str
    symbol: str
    side: str
    quantity: Decimal
    price: Decimal
    timestamp: datetime
    duplicate: bool = False

class PriceIn(BaseModel):
    symbol: str = Field(min_length=1, max_length=40)
    price: Decimal = Field(gt=0, max_digits=24, decimal_places=10)

class ReconcileRequest(BaseModel):
    venue: str
    venue_trades: list[TradeIn]

