# Inventory API

A backend inventory and order management API built with **FastAPI**, **PostgreSQL**, **SQLAlchemy**, and **Docker**.

This project simulates a realistic backend system for managing products, inventory adjustments, customer orders, order status workflows, business reports, and CSV exports. It focuses on backend fundamentals that matter in real applications: relational database modeling, validation, transactions, stock control, automated testing, and clean API design.

## Project Highlights

- Built with FastAPI and PostgreSQL
- Product CRUD with SKU uniqueness validation
- Inventory adjustment workflow with audit history
- Transaction-safe order creation
- Overselling prevention through stock validation
- Order status workflow: pending, paid, shipped, canceled
- Canceling an order restores inventory before shipment
- Low-stock and revenue summary reports
- CSV exports for products, low-stock items, and orders
- Dockerized PostgreSQL setup
- Automated pytest suite with 91% test coverage
- Ruff linting and formatting support
- GitHub Actions CI for automated linting and testing

## Demo

This project includes seeded demo data so the API can be reviewed quickly through the Swagger documentation.

### Run the Demo Locally

Start PostgreSQL:

```bash
docker compose up -d db
```

Run migrations:

```bash
uv run alembic upgrade head
```

Load demo data:

```bash
uv run python -m scripts.seed_demo_data
```

Start the API:

```bash
uv run uvicorn app.main:app --reload --port 8001
```

Open the API docs:

```text
http://127.0.0.1:8001/docs
```

Recommended demo endpoints:

```text
GET /products
GET /orders
GET /reports/low-stock?threshold=5
GET /reports/revenue-summary
GET /reports/products.csv
GET /reports/orders.csv
```

The seed script creates:

- Sample products such as laptops, monitors, keyboards, mice, and docking stations
- Inventory adjustment history
- Pending, paid, shipped, and canceled demo orders
- Data for low-stock and revenue reports

### Demo Screenshots

#### Swagger API Documentation

![Swagger API docs](docs/screenshots/swagger-docs.png)

#### Products Endpoint

![Products endpoint](docs/screenshots/products-endpoint.png)

#### Orders Endpoint

![Orders endpoint](docs/screenshots/orders-endpoint.png)

#### Revenue Summary Report

![Revenue summary](docs/screenshots/revenue-summary.png)

#### Test Coverage

![Test coverage](docs/screenshots/test-coverage.png)

## Tech Stack

| Area | Technology |
|---|---|
| API Framework | FastAPI |
| Database | PostgreSQL |
| ORM | SQLAlchemy |
| Migrations | Alembic |
| Validation | Pydantic |
| Testing | Pytest |
| Coverage | Pytest-Cov |
| Linting/Formatting | Ruff |
| Local Services | Docker Compose |
| Package Management | uv |
| CI | GitHub Actions |

## Core Features

### Products

The API supports product creation, listing, updating, lookup by ID, and soft deletion.

Product fields include:

- SKU
- Name
- Description
- Quantity
- Price
- Active status

Example endpoints:

```text
POST   /products
GET    /products
GET    /products/{product_id}
PATCH  /products/{product_id}
DELETE /products/{product_id}
```

### Inventory Adjustments

Inventory can be increased or decreased through a dedicated adjustment endpoint. Each adjustment is recorded for audit/history purposes.

Example endpoints:

```text
POST /inventory/adjust
GET  /inventory/adjustments
```

Business rules:

- Inventory adjustments cannot reduce stock below zero.
- Quantity changes cannot be zero.
- Inactive products cannot have inventory adjusted.

### Orders

Orders can contain one or more products. When an order is placed, the API validates inventory, calculates totals, creates order items, and deducts stock.

Example endpoints:

```text
POST  /orders
GET   /orders
GET   /orders/{order_id}
PATCH /orders/{order_id}/status
```

Business rules:

- Orders require at least one item.
- Item quantities must be positive.
- Products must exist and be active.
- Orders cannot exceed available stock.
- Duplicate product lines are combined into one order item.
- Stock is deducted only after validation succeeds.

### Order Status Workflow

Supported order statuses:

```text
pending
paid
shipped
canceled
```

Allowed transitions:

| Current Status | Allowed Next Status |
|---|---|
| pending | paid, canceled |
| paid | shipped, canceled |
| shipped | final status |
| canceled | final status |

Canceling an order before shipment restores the ordered quantity back to inventory.

### Reports

The API includes business-facing report endpoints.

```text
GET /reports/low-stock
GET /reports/revenue-summary
```

Revenue reports only include orders with a status of:

```text
paid
shipped
```

Pending and canceled orders are excluded from revenue totals.

### CSV Exports

The API supports downloadable CSV exports:

```text
GET /reports/products.csv
GET /reports/low-stock.csv
GET /reports/orders.csv
```

These exports make the project more realistic by showing how backend systems often support reporting and business operations.

## Database Design

Main tables:

```text
products
inventory_adjustments
orders
order_items
```

Relationships:

- A product can appear in many order items.
- An order has many order items.
- A product can have many inventory adjustments.
- Order items store the product price at the time of purchase.

This prevents historical orders from changing if the product price changes later.

## Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/Dmarti47-hub/inventory-api.git
cd inventory-api
```

### 2. Create the environment file

Create a `.env` file:

```bash
cp .env.example .env
```

Example environment values:

```env
DATABASE_URL=postgresql+psycopg://inventory_user:inventory_pass@localhost:5433/inventory_db
TEST_DATABASE_URL=postgresql+psycopg://inventory_user:inventory_pass@localhost:5434/inventory_test_db
```

### 3. Start PostgreSQL

```bash
docker compose up -d db test_db
```

### 4. Install dependencies

```bash
uv sync
```

### 5. Run migrations

```bash
uv run alembic upgrade head
```

### 6. Start the API

```bash
uv run uvicorn app.main:app --reload --port 8001
```

The API docs will be available at:

```text
http://127.0.0.1:8001/docs
```

## Running Tests

Start the test database:

```bash
docker compose up -d test_db
```

Run the test suite:

```bash
uv run pytest -v
```

Run tests with coverage:

```bash
uv run pytest --cov=app --cov-report=term-missing
```

Current test result:

```text
21 passed
91% coverage
```

## Linting and Formatting

Run Ruff linting:

```bash
uv run ruff check .
```

Format code:

```bash
uv run ruff format .
```

## Docker Usage

Build and run the full API stack:

```bash
docker compose up --build
```

Run in the background:

```bash
docker compose up --build -d
```

View API logs:

```bash
docker compose logs -f api
```

Stop containers:

```bash
docker compose down
```

## Makefile Commands

If using the included Makefile:

```bash
make run
make test
make test-cov
make lint
make format
make db-up
make db-down
make docker-up
make docker-down
make docker-logs
make seed
```

## Example Product Request

```json
{
  "sku": "LAPTOP-001",
  "name": "Business Laptop",
  "description": "Standard office laptop",
  "quantity": 20,
  "price": "899.99"
}
```

## Example Order Request

```json
{
  "customer_name": "Jane Smith",
  "items": [
    {
      "product_id": 1,
      "quantity": 2
    }
  ]
}
```

## Portfolio Summary

This project demonstrates backend API development using FastAPI, PostgreSQL, SQLAlchemy, and Docker. It goes beyond basic CRUD by implementing transaction-safe order creation, inventory validation, order status workflows, reporting endpoints, CSV exports, CI checks, and automated tests for business-critical edge cases.