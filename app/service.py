
from decimal import Decimal
from datetime import timezone
from sqlalchemy import select
from sqlalchemy.orm import Session
from .models import Trade, Position, LatestPrice

ZERO = Decimal("0")


class OversellError(Exception):
    pass


class IdempotencyConflict(Exception):
    pass


def ingest_trade(db: Session, data):
    existing = db.scalar(select(Trade).where(
        Trade.venue == data.venue, Trade.trade_id == data.trade_id
    ))

    if existing:
        stored_time = existing.timestamp
        incoming_time = data.timestamp

        if stored_time.tzinfo is None:
            stored_time = stored_time.replace(tzinfo=timezone.utc)
        if incoming_time.tzinfo is None:
            incoming_time = incoming_time.replace(tzinfo=timezone.utc)

        same = (
            existing.symbol == data.symbol
            and existing.side == data.side
            and existing.quantity == data.quantity
            and existing.price == data.price
            and stored_time.astimezone(timezone.utc)
            == incoming_time.astimezone(timezone.utc)
        )

        if not same:
            raise IdempotencyConflict(
                "venue/trade_id already exists with different data"
            )
        return existing, True

    position = db.get(Position, data.symbol)

    if position is None:
        position = Position(
            symbol=data.symbol,
            quantity=ZERO,
            average_cost=ZERO,
            realized_pnl=ZERO
        )
        db.add(position)
        db.flush()

    qty, avg, realized = (
        position.quantity,
        position.average_cost,
        position.realized_pnl
    )

    if data.side == "BUY":
        new_qty = qty + data.quantity
        position.average_cost = (
            (qty * avg) + (data.quantity * data.price)
        ) / new_qty
        position.quantity = new_qty

    else:
        if data.quantity > qty:
            raise OversellError(
                f"cannot sell {data.quantity}; available quantity is {qty}"
            )

        position.realized_pnl = (
            realized + data.quantity * (data.price - avg)
        )
        position.quantity = qty - data.quantity

        if position.quantity == ZERO:
            position.average_cost = ZERO

    trade_data = data.model_dump()
    trade_data["timestamp"] = (
        data.timestamp.astimezone(timezone.utc).replace(tzinfo=None)
    )

    trade = Trade(**trade_data)
    db.add(trade)
    db.commit()
    db.refresh(trade)

    return trade, False


def get_positions(db: Session):
    return db.scalars(
        select(Position).order_by(Position.symbol)
    ).all()


def get_fifo_values(db: Session, symbol: str):
    trades = db.scalars(
        select(Trade)
        .where(Trade.symbol == symbol)
        .order_by(Trade.timestamp, Trade.id)
    ).all()

    # Each lot contains [remaining quantity, purchase price].
    lots = []
    realized_pnl = ZERO

    for trade in trades:
        if trade.side == "BUY":
            lots.append([trade.quantity, trade.price])

        else:
            remaining = trade.quantity

            while remaining > ZERO and lots:
                lot_quantity, lot_price = lots[0]
                consumed = min(remaining, lot_quantity)

                realized_pnl += consumed * (trade.price - lot_price)

                remaining -= consumed
                lot_quantity -= consumed

                if lot_quantity == ZERO:
                    lots.pop(0)
                else:
                    lots[0][0] = lot_quantity

            if remaining > ZERO:
                raise ValueError(
                    "Trade history cannot support FIFO calculation"
                )

    quantity = sum((lot[0] for lot in lots), ZERO)

    remaining_cost = sum(
        (lot[0] * lot[1] for lot in lots), ZERO
    )

    average_cost = (
        remaining_cost / quantity if quantity > ZERO else ZERO
    )

    return quantity, average_cost, realized_pnl


def get_pnl(
    db: Session,
    symbol: str,
    cost_basis: str = "WEIGHTED_AVERAGE"
):
    position = db.get(Position, symbol)

    if position is None:
        return None

    if cost_basis == "FIFO":
        quantity, average_cost, realized_pnl = get_fifo_values(
            db, symbol
        )
    else:
        quantity = position.quantity
        average_cost = position.average_cost
        realized_pnl = position.realized_pnl

    latest = db.get(LatestPrice, symbol)
    market_price = latest.price if latest else None

    unrealized = (
        (market_price - average_cost) * quantity
        if market_price is not None else None
    )

    return {
        "symbol": symbol,
        "cost_basis": cost_basis,
        "quantity": quantity,
        "average_cost": average_cost,
        "realized_pnl": realized_pnl,
        "latest_price": market_price,
        "unrealized_pnl": unrealized,
        "total_pnl": (
            realized_pnl + unrealized
            if unrealized is not None else None
        ),
    }


def upsert_price(db: Session, symbol: str, price: Decimal):
    row = db.get(LatestPrice, symbol)

    if row is None:
        row = LatestPrice(symbol=symbol, price=price)
        db.add(row)
    else:
        row.price = price

    db.commit()
    db.refresh(row)

    return row


def reconcile(db: Session, venue: str, venue_trades):
    stored = {
        t.trade_id: t
        for t in db.scalars(
            select(Trade).where(Trade.venue == venue)
        ).all()
    }

    external = {t.trade_id: t for t in venue_trades}

    missing, extra, mismatched = [], [], []

    for trade_id, ext in external.items():
        local = stored.get(trade_id)

        if local is None:
            missing.append({
                "trade_id": trade_id,
                "venue_trade": ext.model_dump(mode="json")
            })
            continue

        fields = ("symbol", "side", "quantity", "price", "timestamp")
        differences = {}

        for field in fields:
            stored_value = getattr(local, field)
            venue_value = getattr(ext, field)

            if field == "timestamp":
                if stored_value.tzinfo is None:
                    stored_value = stored_value.replace(
                        tzinfo=timezone.utc
                    )
                stored_value = stored_value.astimezone(timezone.utc)
                venue_value = venue_value.astimezone(timezone.utc)

            if stored_value != venue_value:
                differences[field] = {
                    "stored": str(getattr(local, field)),
                    "venue": str(getattr(ext, field))
                }

        if differences:
            mismatched.append({
                "trade_id": trade_id,
                "differences": differences
            })

    for trade_id in stored:
        if trade_id not in external:
            extra.append({"trade_id": trade_id})

    return {
        "venue": venue,
        "missing": missing,
        "extra": extra,
        "mismatched": mismatched
    }
