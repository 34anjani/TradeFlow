# Design Document – Trade Recorder & PnL Service

## 1. Project Overview

The Trade Recorder & PnL Service is a REST API application designed to ingest and validate financial trades, maintain position information, calculate Profit and Loss (PnL), and reconcile locally stored trades with venue-provided trade records.

The application supports BUY and SELL transactions, duplicate trade prevention, long-only position management, and two cost-basis calculation methods: Weighted Average and FIFO.

The main objective is to maintain accurate trade and position records while ensuring data consistency and providing reliable financial calculations.

## 2. Technology Stack

The project is developed using the following technologies, frameworks, libraries, databases, and tools:
- Python: Core programming language used for application development.
- FastAPI: Framework used to build REST API endpoints.
- Pydantic: Used for request validation and data schema definition.
- SQLAlchemy: Used for database interaction and Object-Relational Mapping (ORM).
- SQLite: Default database for local development.
- PostgreSQL: Supported alternative database.
- Decimal: Used for accurate financial calculations and to avoid floating-point precision issues.
- Pytest: Used for automated testing.
- Uvicorn: ASGI server used to run the FastAPI application.
- Swagger UI: Used to explore, execute, and manually test API endpoints.

## 3. System Architecture

The application follows a layered architecture to separate API handling, validation, database operations, and business logic.

### Main components

- **API Layer (FastAPI):** Exposes HTTP endpoints and handles incoming requests.
- **Validation Layer (Pydantic):** Validates request data and rejects invalid inputs.
- **Service Layer:** Implements business rules for trade processing, position updates, PnL calculations, and reconciliation.
- **Database Layer (SQLAlchemy):** Handles database connections, queries, and persistence.
- **Database:** Stores accepted trades, positions, and latest market prices.

### Request processing flow

1. A client sends a request to an API endpoint.
2. FastAPI receives the request.
3. Pydantic validates the incoming data.
4. The service layer executes the required business logic.
5. SQLAlchemy interacts with the database when necessary.
6. The API returns the appropriate response and HTTP status code.

## 4. Database Design

The application uses three primary database tables.

### 4.1 Trades

Stores accepted trade records.

Important fields include:

- Trade ID
- Venue
- Symbol
- Side (BUY or SELL)
- Quantity
- Execution price
- Timestamp

Design decisions:
- Accepted trade records are treated as immutable.
- A unique database constraint is applied to the combination of `venue` and `trade_id`.
- This prevents the same trade from being inserted more than once for the same venue.

### 4.2 Positions

Stores the current position information for each symbol.

Important fields include:

- Symbol
- Net quantity
- Weighted average cost
- Cumulative realized PnL

The position is maintained using accepted BUY and SELL trades.

### 4.3 Latest Prices

Stores the latest submitted market price for each symbol.

When a new price is submitted for a symbol, it becomes the latest price used for subsequent PnL calculations.

### 4.4 Financial Data Precision

- SQL financial columns use `NUMERIC(24, 10)`.
- Python financial calculations use `Decimal` instead of floating-point arithmetic.
- This helps avoid floating-point precision errors in financial calculations.

## 5. API Design

The application exposes the following REST API endpoints:
- GET /health – Checks the health of the application.
- POST /trades – Accepts and records a new trade.
- GET /trades – Retrieves stored trade records.
- GET /positions – Retrieves current position information.
- POST /prices – Updates the latest market price for a symbol.
- GET /pnl/{symbol} – Calculates Profit and Loss (PnL) for a specified symbol.
- POST /reconcile – Compares locally stored trades with venue-provided records and identifies discrepancies.

FastAPI automatically generates interactive API documentation through Swagger UI, available at `/docs`.

## 6. Trade Processing and Business Rules

### 6.1 Trade Ingestion

The application accepts BUY and SELL trade requests.

Before accepting a trade, the application validates the input and checks the idempotency key.

For a valid new trade:
1. The trade details are validated.
2. Duplicate trade checks are performed.
3. The available position is checked for SELL requests.
4. The trade is recorded.
5. The corresponding position is updated.

### 6.2 Idempotency

Idempotency prevents the same trade from being processed multiple times.

The idempotency key is:

`(venue, trade_id)`

The application handles duplicate requests as follows:

- If the same key is submitted with identical trade details, the existing trade is returned without changing the position.
- If the same key is submitted with different trade details, the application returns HTTP 409.
- A database unique constraint provides an additional safeguard against duplicate records.

### 6.3 Position Management

Positions are maintained at the symbol level.

For BUY trades:
- Net quantity increases.
- Average cost is recalculated.
- Existing realized PnL is retained.

For SELL trades:
- Net quantity decreases.
- Realized PnL is updated.
- Average cost remains unchanged while the long position remains open.

When the position quantity reaches zero, average cost resets to zero.

The application supports long-only positions. Short selling is not supported.

### 6.4 Oversell Protection

The application prevents selling more units than are currently available.

For example, if the available quantity is 15 units, a request to sell 20 units is rejected.

The application returns HTTP 409, does not accept the invalid trade, and leaves the existing position unchanged.

## 7. Cost-Basis Methods

The service supports two cost-basis methods: Weighted Average and FIFO.

The PnL endpoint accepts a `cost_basis` query parameter. Weighted Average is the default method.

### 7.1 Weighted Average

Weighted Average calculates the average purchase price of all currently held units.

For a BUY with current quantity `Q`, current average cost `A`, incoming quantity `q`, and execution price `p`:

`new_average = ((Q * A) + (q * p)) / (Q + q)`

`new_quantity = Q + q`

For a SELL of quantity `q` at price `p`:

`realized_pnl += q * (p - A)`

`new_quantity = Q - q`

The weighted-average values are maintained in the `positions` table during trade ingestion.

### 7.2 FIFO (First In, First Out)

FIFO assumes that the oldest purchased units are sold first.

The service calculates FIFO values by replaying the stored trades for the requested symbol in chronological order, using trade ID as a secondary ordering key.

- Each BUY creates a purchase lot containing its remaining quantity and purchase price.
- Each SELL consumes quantity from the oldest available purchase lot first.
- Realized PnL is calculated using the purchase price of each consumed lot.
- Remaining lots determine the open quantity and average cost.

Trade ID is used as a secondary ordering key when multiple trades have the same timestamp.
FIFO calculations use the stored trade history and do not require a separate purchase-lot table.

## 8. Profit and Loss Calculation

The application calculates three PnL values:

### 8.1 Realized PnL

Realized PnL represents the profit or loss from units that have already been sold.

It is calculated using the difference between the selling price and the applicable cost basis.

### 8.2 Unrealized PnL

Unrealized PnL represents the profit or loss on units that are still held.

`unrealized_pnl = (latest_price - average_cost) * open_quantity`

### 8.3 Total PnL

`total_pnl = realized_pnl + unrealized_pnl`

The selected cost-basis method determines the average cost and realized PnL used in the calculation.

If no latest market price exists, unrealized and total PnL are returned as null.

### Example

Consider the following trades:
- BUY 10 @ 100
- BUY 10 @ 110
- SELL 5 @ 120
- Latest market price: 125

Weighted Average:
- Remaining quantity: 15
- Average cost: 105
- Realized PnL: 75
- Unrealized PnL: 300
- Total PnL: 375

FIFO (First In, First Out):
- Remaining quantity: 15
- Average cost: 106.6667
- Realized PnL: 100
- Unrealized PnL: 275
- Total PnL: 375

### Example API requests

`/pnl/BTC-USD?cost_basis=WEIGHTED_AVERAGE`

`/pnl/BTC-USD?cost_basis=FIFO`

If `cost_basis` is omitted, Weighted Average is used.

## 9. Trade Reconciliation

Reconciliation compares venue-provided trade records with locally stored trade records.

The comparison is performed for the specified venue using `trade_id` as the matching key.

The application identifies three types of discrepancies:

- **Missing:** The venue has the trade, but local storage does not.
- **Extra:** Local storage has the trade, but the venue snapshot does not.
- **Mismatched:** Both records exist, but one or more fields differ.

The fields compared include symbol, side, quantity, price, and timestamp.

Reconciliation is read-only. It reports discrepancies without automatically modifying existing financial records.

## 10. API Error Handling

The application uses standard HTTP status codes to communicate request outcomes:
- 201 – Created: Indicates that a new trade has been successfully accepted.
- 409 – Conflict: Returned when an oversell is attempted or an existing idempotency key is reused with different trade details.
- 422 – Validation Error: Returned when the request contains invalid data or fails schema validation.
- 404 – Not Found: Returned when the requested PnL position does not exist.

FastAPI and Pydantic handle request validation and generate appropriate error responses for invalid inputs.

## 11. Testing Strategy

The application was tested using automated tests with Pytest and manual API testing through FastAPI Swagger UI.

### 11.1 Automated Testing

The automated test suite covers the following scenarios:

- Valid trade ingestion and position updates.
- Invalid trade input validation.
- Duplicate trade handling.
- Conflicting idempotency key handling.
- Weighted Average PnL calculations.
- FIFO PnL calculations.
- Oversell rejection and position consistency.
- Reconciliation of missing, extra, and mismatched trades.

Automated test result: 7 passed.

### 11.2 Manual API Testing

Manual testing was performed through Swagger UI to verify:

- Trade ingestion and retrieval.
- Position updates after BUY and SELL operations.
- Latest market price updates.
- FIFO and Weighted Average PnL calculations.
- Oversell rejection and position consistency.
- Missing and mismatched trade detection.
- Concurrent duplicate trade requests.
- Same trade ID across different venues.

## 12. Design Decisions and Trade-offs

The following design decisions were made to keep the implementation simple and maintainable:

- **SQLite as the default database:** Simplifies local setup and development, while PostgreSQL is supported as an alternative.
- **SQLAlchemy ORM:** Provides structured database interaction and reduces the need for database-specific query code.
- **Decimal for financial calculations:** Helps maintain accuracy when working with monetary values.
- **Weighted Average stored in positions:** Allows position information to be updated during trade ingestion.
- **FIFO calculated from trade history:** Avoids maintaining a separate purchase-lot table, at the cost of replaying trade history when FIFO PnL is requested.
- **Long-only position management:** Keeps position calculations straightforward and avoids the additional complexity of short positions.

## 13. Future Improvements
- Add authentication for secure API access.