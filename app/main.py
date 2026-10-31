from fastapi import FastAPI, Depends, HTTPException
from typing import Literal
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select
from .database import get_db
from .models import Trade
from .schemas import TradeIn, TradeOut, PriceIn, ReconcileRequest
from .service import (ingest_trade, get_positions, get_pnl, upsert_price,
                      reconcile, OversellError, IdempotencyConflict)

app = FastAPI(title="Trade Recorder & PnL Service", version="1.0.0",
            )

@app.get("/health", tags=["API Endpoints"])
def health():
    return {"status": "ok"}

@app.post("/trades", response_model=TradeOut, status_code=201, tags=["API Endpoints"])
def create_trade(payload: TradeIn, db: Session = Depends(get_db)):
    try:
        trade, duplicate = ingest_trade(db, payload)
        result = TradeOut.model_validate(trade)
        result.duplicate = duplicate
        return result
    except OversellError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail=str(exc))
    except IdempotencyConflict as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail=str(exc))
    except IntegrityError:
        db.rollback()

        existing = db.scalar(
            select(Trade).where(
                Trade.venue == payload.venue,
                Trade.trade_id == payload.trade_id
            )
        )

        if existing:
            try:
                trade, duplicate = ingest_trade(db, payload)
                result = TradeOut.model_validate(trade)
                result.duplicate = duplicate
                return result
            except IdempotencyConflict as exc:
                db.rollback()
                raise HTTPException(status_code=409, detail=str(exc))

        raise HTTPException(
            status_code=409,
            detail="trade conflicts with an existing record"
        )

@app.get("/trades", tags=["API Endpoints"])
def list_trades(venue: str | None = None, symbol: str | None = None,
                db: Session = Depends(get_db)):
    stmt = select(Trade)
    if venue:
        stmt = stmt.where(Trade.venue == venue)
    if symbol:
        stmt = stmt.where(Trade.symbol == symbol)
    return db.scalars(stmt.order_by(Trade.timestamp, Trade.id)).all()

@app.get("/positions", tags=["API Endpoints"])
def positions(db: Session = Depends(get_db)):
    return get_positions(db)

@app.post("/prices", tags=["API Endpoints"])
def update_latest_price(payload: PriceIn, db: Session = Depends(get_db)):
    row = upsert_price(db, payload.symbol, payload.price)
    return {"symbol": row.symbol, "price": row.price, "updated_at": row.updated_at}

@app.get("/pnl/{symbol}", tags=["API Endpoints"])
def pnl(
    symbol: str,
    cost_basis: Literal["WEIGHTED_AVERAGE", "FIFO"] = "WEIGHTED_AVERAGE",
    db: Session = Depends(get_db)
):
    result = get_pnl(db, symbol, cost_basis)
    if result is None:
        raise HTTPException(status_code=404, detail="position not found")
    return result

@app.post("/reconcile", tags=["API Endpoints"])
def run_reconciliation(payload: ReconcileRequest, db: Session = Depends(get_db)):
    wrong_venue = [t.trade_id for t in payload.venue_trades if t.venue != payload.venue]
    if wrong_venue:
        raise HTTPException(status_code=422, detail=f"trades contain a different venue: {wrong_venue}")
    ids = [t.trade_id for t in payload.venue_trades]
    if len(ids) != len(set(ids)):
        raise HTTPException(status_code=422, detail="duplicate trade_id in venue snapshot")
    return reconcile(db, payload.venue, payload.venue_trades)
