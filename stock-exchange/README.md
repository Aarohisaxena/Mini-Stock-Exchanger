# Mini Stock Exchange

A mini stock exchange with a price-time priority matching engine, REST APIs, PostgreSQL persistence, and live WebSocket order book updates.

## Architecture

```
Order Matching Engine
├── FastAPI (REST + WebSocket)
├── PostgreSQL (optional persistence)
├── Matching Engine (pure Python)
├── Order Book (heapq price-time priority)
├── Limit & Market Orders
├── Partial Fills
└── Order Cancel / Modify
```

## Project Structure

```
stock-exchange/
├── models/              # Phase 1: core order model
├── engine/              # Phase 1: order book, matching engine, trades
├── app/
│   ├── api/             # FastAPI routes
│   ├── services/        # Business logic
│   ├── database/        # SQLAlchemy models
│   └── main.py          # App entry point
└── tests/
```

## Quick Start

### 1. Install dependencies

```bash
cd stock-exchange
pip install -r requirements.txt
```

### 2. Run Phase 1 tests (matching engine only)

```bash
python tests/test_matching_engine.py
```

### 3. Start the API server

```bash
uvicorn app.main:app --reload --app-dir .
```

Open http://127.0.0.1:8000/docs for interactive API docs.

### 4. PostgreSQL (optional)

Set `DATABASE_URL` before starting the server:

```bash
set DATABASE_URL=postgresql://user:password@localhost:5432/stock_exchange
uvicorn app.main:app --reload --app-dir .
```

Tables are created automatically on startup.

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/orders` | Place limit or market order |
| DELETE | `/orders/{id}` | Cancel an open order |
| PATCH | `/orders/{id}` | Modify price or quantity |
| GET | `/orderbook` | View bids and asks |
| GET | `/trades` | View trade history |
| WS | `/ws/orderbook` | Live order book updates |

### Place Order

```json
POST /orders
{
  "side": "buy",
  "price": 100,
  "quantity": 5,
  "type": "limit"
}
```

### Market Order

```json
POST /orders
{
  "side": "buy",
  "quantity": 10,
  "type": "market"
}
```

### Order Book

```json
GET /orderbook
{
  "bids": [{"price": 105, "qty": 10}],
  "asks": [{"price": 106, "qty": 5}]
}
```

## Matching Rules

1. **Price priority**: highest bid matches lowest ask when `bid >= ask`
2. **Time priority**: earlier orders at the same price execute first (FIFO)
3. **Trade price**: executes at the resting (maker) order's price
4. **Partial fills**: large orders fill incrementally against the book
5. **Market orders**: execute immediately at best available price; unfilled remainder is cancelled

## WebSocket

Connect to `ws://127.0.0.1:8000/ws/orderbook`. You receive the current book on connect, then live updates after each trade.

```javascript
const ws = new WebSocket("ws://127.0.0.1:8000/ws/orderbook");
ws.onmessage = (event) => console.log(JSON.parse(event.data));
```

## Development Phases

- **Phase 1** — Core matching engine (`models/`, `engine/`)
- **Phase 2** — FastAPI REST layer (`app/api/`)
- **Phase 3** — Partial fills, market orders, cancel, modify
- **Phase 4** — PostgreSQL via SQLAlchemy
- **Phase 5** — WebSocket live order book broadcast
