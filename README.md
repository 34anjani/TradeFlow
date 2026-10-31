# Trade Recorder & PnL Service

## 1. Project Overview

The Trade Recorder & PnL Service is a REST API application developed using Python and FastAPI. It allows users to record financial trades, maintain positions, calculate Profit and Loss (PnL), and reconcile locally stored trades with venue-provided records.

The application supports BUY and SELL trades, duplicate trade prevention, oversell protection, and two cost-basis methods: Weighted Average and FIFO.

## 2. Key Features

- Trade ingestion with input validation.
- Idempotency using `(venue, trade_id)`.
- Position tracking with net quantity and average cost.
- Realized and unrealized PnL calculations.
- Support for Weighted Average and FIFO cost-basis methods.
- Latest market price updates.
- Oversell protection to prevent selling more than the available quantity.
- Trade reconciliation to identify missing, extra, and mismatched trades.
- Financial calculations using Python Decimal.

## 3. Technology Stack

- Python 3.12
- FastAPI
- Pydantic
- SQLAlchemy
- SQLite (default local database)
- PostgreSQL (supported alternative)
- Pytest
- Uvicorn
- HTTPX

## 4. Application Components

The application is organized into separate modules to handle API requests, data validation, database operations, and business logic.

The main components are:

- API endpoints for trade ingestion, position retrieval, PnL calculation, and reconciliation.
- Database models for storing trades, positions, and latest prices.
- Pydantic schemas for request validation and response formatting.
- Service logic for trade processing, position management, and PnL calculations.
- Automated tests to verify application functionality.

## 5. Prerequisites

Before running the application, make sure you have:

- Python 3.12 or later.
- pip (Python package installer).
- Git (to clone the repository).

SQLite is used by default, so a separate database installation is not required for local development.

## 6. Installation and Setup

### Step 1: Clone the repository

```bash
git clone <repository-url>
cd trade-recorder-pnl-service
```

### Step 2: Create a virtual environment

```bash
python -m venv venv
```

### Step 3: Activate the virtual environment

Windows PowerShell:

```powershell
.\venv\Scripts\Activate.ps1
```

Linux/macOS:

```bash
source venv/bin/activate
```

### Step 4: Install dependencies

```bash
pip install -r requirements.txt
```

### Step 5: Initialize the database

```bash
python -m app.init_db
```

## 7. How to Run the Application

Start the FastAPI application using:

```bash
python -m uvicorn app.main:app --reload
```

The application will be available at:

http://127.0.0.1:8000

## 8. API Endpoints and Swagger Documentation

The application provides the following API endpoints:

- **GET `/health`** – Checks the health of the application.
- **POST `/trades`** – Accepts and records a new trade.
- **GET `/trades`** – Retrieves stored trade records.
- **GET `/positions`** – Retrieves current position information.
- **POST `/prices`** – Updates the latest market price for a symbol.
- **GET `/pnl/{symbol}`** – Calculates Profit and Loss (PnL) for a specified symbol.
- **POST `/reconcile`** – Compares locally stored trades with venue-provided records and identifies discrepancies.

### Interactive API Documentation

Once the application is running, open:

http://127.0.0.1:8000/docs

Swagger UI allows you to explore the endpoints, provide input, execute API requests, and view responses.

## 9. Additional Documentation

- [Design Document](DESIGN.md) – Explains the system architecture, database design, business logic, cost-basis methods, and design decisions.
- [Testing Results](results.md) – Contains automated and manual testing details.
- [AI Usage](AI_USAGE.md) – Describes how AI tools were used during development.