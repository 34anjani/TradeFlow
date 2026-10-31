from datetime import datetime, timezone

def trade(trade_id, side, quantity, price, timestamp="2026-10-30T10:00:00Z", venue="binance"):
    return {"venue": venue, "trade_id": trade_id, "symbol": "BTC-USD",
            "side": side, "quantity": str(quantity), "price": str(price),
            "timestamp": timestamp}

def test_average_cost_and_pnl(client):
    assert client.post("/trades", json=trade("T1", "BUY", 10, 100)).status_code == 201
    assert client.post("/trades", json=trade("T2", "BUY", 10, 110,
        "2026-10-30T10:01:00Z")).status_code == 201
    assert client.post("/trades", json=trade("T3", "SELL", 5, 120,
        "2026-10-30T10:02:00Z")).status_code == 201
    client.post("/prices", json={"symbol": "BTC-USD", "price": "125"})
    result = client.get("/pnl/BTC-USD").json()
    assert float(result["quantity"]) == 15
    assert float(result["average_cost"]) == 105
    assert float(result["realized_pnl"]) == 75
    assert float(result["unrealized_pnl"]) == 300

def test_idempotency(client):
    payload = trade("T-1001", "BUY", 10, 100)
    assert client.post("/trades", json=payload).status_code == 201
    response = client.post("/trades", json=payload)
    assert response.status_code == 201
    assert response.json()["duplicate"] is True
    assert len(client.get("/trades").json()) == 1
    assert float(client.get("/positions").json()[0]["quantity"]) == 10

def test_idempotency_conflict(client):
    client.post("/trades", json=trade("T1", "BUY", 10, 100))
    response = client.post("/trades", json=trade("T1", "BUY", 11, 100))
    assert response.status_code == 409
    assert float(client.get("/positions").json()[0]["quantity"]) == 10

def test_oversell_does_not_change_position(client):
    client.post("/trades", json=trade("T1", "BUY", 10, 100))
    response = client.post("/trades", json=trade("T2", "SELL", 15, 120,
        "2026-10-30T10:01:00Z"))
    assert response.status_code == 409
    assert float(client.get("/positions").json()[0]["quantity"]) == 10
    assert len(client.get("/trades").json()) == 1

def test_reconciliation_missing_extra_and_mismatch(client):
    client.post("/trades", json=trade("T1", "BUY", 10, 100))
    client.post("/trades", json=trade("T2", "BUY", 5, 101,
        "2026-10-30T10:01:00Z"))
    venue_snapshot = [
        trade("T1", "BUY", 10, 100),
        trade("T2", "BUY", 6, 101, "2026-10-30T10:01:00Z"),
        trade("T3", "BUY", 1, 99, "2026-10-30T10:02:00Z"),
    ]
    result = client.post("/reconcile", json={
        "venue": "binance", "venue_trades": venue_snapshot
    }).json()
    assert [x["trade_id"] for x in result["missing"]] == ["T3"]
    assert result["extra"] == []
    assert [x["trade_id"] for x in result["mismatched"]] == ["T2"]

def test_invalid_trade_rejected(client):
    payload = trade("T1", "BUY", -1, 100)
    assert client.post("/trades", json=payload).status_code == 422

def test_fifo_cost_and_pnl(client):
    assert client.post(
        "/trades", json=trade("T1", "BUY", 10, 100)
    ).status_code == 201

    assert client.post(
        "/trades", json=trade(
            "T2", "BUY", 10, 110, "2026-10-30T10:01:00Z"
        )
    ).status_code == 201

    assert client.post(
        "/trades", json=trade(
            "T3", "SELL", 5, 120, "2026-10-30T10:02:00Z"
        )
    ).status_code == 201

    client.post("/prices", json={"symbol": "BTC-USD", "price": "125"})

    result = client.get(
        "/pnl/BTC-USD?cost_basis=FIFO"
    ).json()

    assert result["cost_basis"] == "FIFO"
    assert float(result["quantity"]) == 15
    assert abs(float(result["average_cost"]) - 106.6666666667) < 0.000001
    assert float(result["realized_pnl"]) == 100
    assert float(result["unrealized_pnl"]) == 275
