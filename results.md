## Test 1: Valid BUY Trade

**Objective:** Verify that the application accepts and stores a valid BUY trade.

**Endpoint:** `POST /trades`

**Input:**
```json
{
  "venue": "BINANCE",
  "trade_id": "MANUAL-001",
  "symbol": "EDGE-TEST-01",
  "side": "BUY",
  "quantity": "10",
  "price": "100",
  "timestamp": "2026-10-31T10:00:00Z"
}
```

**Expected Result:**
- HTTP status: `201 Created`
- Trade should be stored successfully.
- Duplicate should be `false`.

**Actual Result:**
- HTTP status: `201 Created`
- Trade was successfully accepted.
- Quantity: `10`
- Price: `100`
- Duplicate: `false`

**Status: PASS**

**Conclusion:** The application successfully accepted a valid BUY trade and returned the correct trade details.

## Test 2: Verify Position After BUY

**Objective:** Verify that a successful BUY trade updates the position correctly.

**Endpoint:** `GET /positions`

**Input:** No input required.

**Expected Result for EDGE-TEST-01:**
- Quantity: 10
- Average cost: 100
- Realized PnL: 0

**Actual Result:**
- Quantity: 10
- Average cost: 100
- Realized PnL: 0

**Status: PASS**

**Conclusion:** The application correctly updated the position after the BUY trade.

## Test 3: Duplicate Trade (Idempotency)

**Objective:** Verify that submitting the same trade twice does not process it again.

**Endpoint:** `POST /trades`

**Input:** Submitted the exact same trade used in Test 1 with:
- Venue: BINANCE
- Trade ID: MANUAL-001
- Symbol: EDGE-TEST-01
- Side: BUY
- Quantity: 10
- Price: 100

**Expected Result:**
- HTTP status: `201`
- Duplicate should be `true`.
- Trade should not be processed again.

**Actual Result:**
- HTTP status: `201`
- Duplicate: `true`
- Application recognised the existing trade.

**Status: PASS**

**Conclusion:** Idempotency worked correctly. The repeated trade was recognised and not processed again.

## Test 4: Position Unchanged After Duplicate Trade

**Objective:** Verify that submitting a duplicate trade does not change the existing position.

**Endpoint:** `GET /positions`

**Expected Result:**
- Quantity should remain 10.
- Average cost should remain 100.

**Actual Result:**
- Quantity: 10
- Average cost: 100
- Realized PnL: 0

**Status: PASS**

**Conclusion:** The duplicate trade was not processed again, and the existing position remained unchanged.

**## Test 5: Second BUY Trade**

**Objective:** Verify that the application accepts a second BUY trade for the same symbol and updates the average cost correctly.

**Endpoint:** `POST /trades`

**Input:** BINANCE, MANUAL-002, EDGE-TEST-01, BUY, quantity 10, price 110.

**Expected Result:**
- HTTP status: `201 Created`
- Duplicate: `false`
- Position quantity: 20
- Average cost: 105

**Actual Result:**
- HTTP status: `201 Created`
- Duplicate: `false`
- Trade accepted successfully.

**Status: PASS**

**Conclusion:** The application successfully accepted the second BUY trade.

## Test 6: SELL Trade

**Objective:** Verify that the application accepts a valid SELL trade.

**Endpoint:** `POST /trades`

**Input:** BINANCE, MANUAL-003, EDGE-TEST-01, SELL, quantity 5, price 120.

**Expected Result:** HTTP `201 Created`, duplicate `false`.

**Actual Result:** HTTP `201 Created`, duplicate `false`. Trade accepted successfully.

**Status: PASS**

**Conclusion:** The application successfully accepted the SELL trade.

## Test 7: FIFO and Weighted Average PnL

**Objective:** Verify that FIFO and Weighted Average calculate realized PnL differently based on their cost-basis methods.

**Endpoint:** `GET /pnl/{symbol}`

**Input:** Symbol: EDGE-TEST-01

**Expected Result:**
- FIFO: Quantity 15, average cost approximately 106.6667, realized PnL 100.
- Weighted Average: Quantity 15, average cost 105, realized PnL 75.

**Actual Result:**
- FIFO: Quantity 15, average cost 106.66666666666667, realized PnL 100.
- Weighted Average: Quantity 15, average cost 105, realized PnL 75.
- Both requests returned HTTP 200.

**Status: PASS**

**Conclusion:** Both cost-basis methods produced the expected results. FIFO and Weighted Average correctly calculated different realized PnL values.

## Test 8: Submit Latest Market Price

**Objective:** Verify that the application accepts and stores the latest market price for a symbol.

**Endpoint:** `POST /prices`

**Input:** Symbol: EDGE-TEST-01, Price: 125.

**Expected Result:** HTTP `200 OK` and the latest price should be stored.

**Actual Result:**
- HTTP status: `200 OK`
- Symbol: EDGE-TEST-01
- Price: 125
- Updated timestamp returned successfully.

**Status: PASS**

**Conclusion:** The application successfully stored the latest market price.
## Test 9: FIFO PnL Calculation with Latest Price

**Objective:** Verify realized PnL, unrealized PnL, and total PnL using FIFO cost basis and the latest market price.

**Endpoint:** `GET /pnl/EDGE-TEST-01?cost_basis=FIFO`

**Expected Result:**
- Quantity: 15
- Average cost: approximately 106.6667
- Realized PnL: 100
- Latest price: 125
- Unrealized PnL: 275
- Total PnL: 375

**Actual Result:**
- HTTP status: 200
- Quantity: 15
- Average cost: 106.66666666666667
- Realized PnL: 100
- Latest price: 125
- Unrealized PnL: 275
- Total PnL: 375

**Status: PASS**

**Conclusion:** The application correctly calculated FIFO realized PnL, unrealized PnL, and total PnL using the latest market price.

## Test 10: Weighted Average PnL Calculation with Latest Price

**Objective:** Verify realized PnL, unrealized PnL, and total PnL using Weighted Average cost basis.

**Endpoint:** `GET /pnl/EDGE-TEST-01?cost_basis=WEIGHTED_AVERAGE`

**Expected Result:**
- Quantity: 15
- Average cost: 105
- Realized PnL: 75
- Latest price: 125
- Unrealized PnL: 300
- Total PnL: 375

**Actual Result:**
- HTTP status: 200
- Quantity: 15
- Average cost: 105
- Realized PnL: 75
- Latest price: 125
- Unrealized PnL: 300
- Total PnL: 375

**Status: PASS**

**Conclusion:** The application correctly calculated Weighted Average realized PnL, unrealized PnL, and total PnL.

**## Test 11: Oversell Protection**

**Objective:** Verify that the application rejects a SELL trade when the requested quantity exceeds the available position.

**Endpoint:** `POST /trades`

**Input:** BINANCE, SELL, EDGE-TEST-01, quantity 20, price 125.

**Expected Result:**
- HTTP status: `409 Conflict`
- The oversell request should be rejected.
- The existing position should remain unchanged.

**Actual Result:**
- HTTP status: `409 Conflict`
- Error: `cannot sell 20; available quantity is 15.0000000000`.
- Trade was rejected.

**Status: PASS**

**Conclusion:** The application correctly rejected the oversell attempt because the requested quantity exceeded the available position.

## Test 12: Verify Position Unchanged After Oversell

**Objective:** Verify that a rejected oversell attempt does not modify the existing position.

**Endpoint:** `GET /positions`

**Expected Result for EDGE-TEST-01:**
- Quantity: 15
- Average cost: 105
- Realized PnL: 75

**Actual Result:**
- HTTP status: 200
- Quantity: 15
- Average cost: 105
- Realized PnL: 75

**Status: PASS**

**Conclusion:** The position remained unchanged after the application rejected the oversell attempt.

## Test 13: Trade Reconciliation

**Objective:** Verify that the application compares stored trades with venue-provided trades and identifies missing, extra, and mismatched records.

**Endpoint:** `POST /reconcile`

**Input:** Three BINANCE trades: MANUAL-001, MANUAL-002, and MANUAL-003.

**Expected Result:** The three supplied trades should match the stored records.

**Actual Result:**
- HTTP status: 200
- Missing: 0
- Extra: 6 (other existing BINANCE trades not included in the input)
- Mismatched: 0

**Status: PASS — matching records identified correctly; existing extra records detected.**

**Conclusion:** The reconciliation endpoint correctly identified the three matching trades and reported six additional stored trades.

## Test 14: Missing Trade Detection

**Objective:** Verify that reconciliation identifies a venue trade that does not exist in the application database.

**Endpoint:** `POST /reconcile`

**Input:** Venue trade ID: MANUAL-MISSING-001.

**Expected Result:** MANUAL-MISSING-001 should appear in the missing list.

**Actual Result:**
- HTTP status: 200
- Missing: MANUAL-MISSING-001
- Extra: 9 existing trades
- Mismatched: 0

**Status: PASS**

**Conclusion:** The application correctly identified the venue trade that was missing from its database.

## Test 15: Mismatched Trade Detection

**Objective:** Verify that reconciliation identifies differences between stored trades and venue-provided trades.

**Endpoint:** `POST /reconcile`

**Input:** Existing trade MANUAL-001 with venue price changed from 100 to 105.

**Expected Result:** MANUAL-001 should appear in the mismatched list with the price difference.

**Actual Result:**
- Missing: 0
- Extra: 8
- Mismatched: MANUAL-001
- Stored price: 100
- Venue price: 105

**Status: PASS**

**Conclusion:** The application correctly detected the price mismatch between the stored trade and the venue-provided trade.


## Test 16: Invalid Trade Input

**Objective:** Verify that the application rejects a trade with an invalid negative quantity.

**Endpoint:** `POST /trades`

**Input:** BUY trade with quantity -5.

**Expected Result:** HTTP `422 Unprocessable Entity` with a validation error.

**Actual Result:**
- HTTP status: 422
- Error: Input should be greater than 0.
- Trade was rejected.

**Status: PASS**

**Conclusion:** The application correctly validated the trade quantity and rejected invalid input.

## Additional Manual Tests

### Test 17: Concurrent Duplicate Trade Requests — PASS
- Submitted five identical BUY requests simultaneously using five workers.
- One request inserted the trade successfully (`duplicate: false`).
- Four requests were identified as duplicates (`duplicate: true`).
- All five returned HTTP 201.
- Confirmed that only one trade was stored.

### Test 18: Position Verification After Concurrent Requests — PASS
- Retrieved positions using `GET /positions`.
- Verified `EDGE-TEST-02`.
- Quantity: 1
- Average Cost: 50
- Realized PnL: 0
- Confirmed that concurrent duplicate requests updated the position only once.

### Test 19: Trade History Verification — PASS
- Retrieved all trades using `GET /trades`.
- Verified that `CONCURRENCY-MANUAL-002` appeared exactly once.
- Confirmed that only one record was stored for the five simultaneous requests.

### Test 20: Same Trade ID Across Different Venues — PASS
- Submitted `VENUE-CHECK-001` for COINBASE.
- Submitted the same trade ID for BINANCE.
- Both requests returned HTTP 201 with `duplicate: false`.
- Confirmed that the same trade ID is allowed across different venues.

### Test 21: Conflicting Duplicate Trade — PASS
- Submitted an existing BINANCE trade ID with different quantity and price.
- The API returned HTTP 409 Conflict.
- Response: `venue/trade_id already exists with different data`.
- Confirmed that conflicting duplicate trades are rejected.

### Test 22: Position Verification After Conflicting Duplicate — PASS
- Retrieved positions using `GET /positions`.
- Verified that `TESTUSDT` had quantity `4`, average cost `100`, and realized PnL `0`.
- Confirmed that the two valid trades from COINBASE and BINANCE remained recorded.
- Confirmed that the rejected conflicting duplicate request did not modify the position.
