import csv
from io import StringIO

from fastapi.testclient import TestClient


def create_test_product(
    client: TestClient,
    *,
    sku: str,
    name: str,
    quantity: int,
    price: str,
) -> int:
    response = client.post(
        "/products",
        json={
            "sku": sku,
            "name": name,
            "description": "Report test product",
            "quantity": quantity,
            "price": price,
        },
    )

    assert response.status_code == 201

    return response.json()["id"]


def create_order(
    client: TestClient,
    *,
    customer_name: str,
    product_id: int,
    quantity: int,
) -> int:
    response = client.post(
        "/orders",
        json={
            "customer_name": customer_name,
            "items": [
                {
                    "product_id": product_id,
                    "quantity": quantity,
                }
            ],
        },
    )

    assert response.status_code == 201

    return response.json()["id"]


def parse_csv_response(response):
    content = response.text
    reader = csv.DictReader(StringIO(content))
    return list(reader)


def test_low_stock_report_returns_products_below_threshold(client: TestClient):
    low_stock_product_id = create_test_product(
        client,
        sku="LOW-001",
        name="Low Stock Product",
        quantity=3,
        price="9.99",
    )

    create_test_product(
        client,
        sku="HIGH-001",
        name="High Stock Product",
        quantity=25,
        price="19.99",
    )

    response = client.get("/reports/low-stock?threshold=5")

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1
    assert data[0]["id"] == low_stock_product_id
    assert data[0]["sku"] == "LOW-001"
    assert data[0]["quantity"] == 3


def test_revenue_summary_counts_only_paid_and_shipped_orders(client: TestClient):
    product_id = create_test_product(
        client,
        sku="REV-001",
        name="Revenue Product",
        quantity=100,
        price="10.00",
    )

    pending_order_id = create_order(
        client,
        customer_name="Pending Customer",
        product_id=product_id,
        quantity=1,
    )

    paid_order_id = create_order(
        client,
        customer_name="Paid Customer",
        product_id=product_id,
        quantity=3,
    )

    shipped_order_id = create_order(
        client,
        customer_name="Shipped Customer",
        product_id=product_id,
        quantity=4,
    )

    canceled_order_id = create_order(
        client,
        customer_name="Canceled Customer",
        product_id=product_id,
        quantity=2,
    )

    paid_response = client.patch(
        f"/orders/{paid_order_id}/status",
        json={"status": "paid"},
    )

    shipped_paid_response = client.patch(
        f"/orders/{shipped_order_id}/status",
        json={"status": "paid"},
    )

    shipped_response = client.patch(
        f"/orders/{shipped_order_id}/status",
        json={"status": "shipped"},
    )

    canceled_response = client.patch(
        f"/orders/{canceled_order_id}/status",
        json={"status": "canceled"},
    )

    assert paid_response.status_code == 200
    assert shipped_paid_response.status_code == 200
    assert shipped_response.status_code == 200
    assert canceled_response.status_code == 200

    response = client.get("/reports/revenue-summary")

    assert response.status_code == 200

    data = response.json()

    assert data["paid_or_shipped_order_count"] == 2
    assert data["total_revenue"] == "70.00"
    assert data["average_order_value"] == "35.00"

    pending_order = client.get(f"/orders/{pending_order_id}").json()

    assert pending_order["status"] == "pending"


def test_products_csv_export(client: TestClient):
    create_test_product(
        client,
        sku="CSV-001",
        name="CSV Product",
        quantity=12,
        price="15.99",
    )

    response = client.get("/reports/products.csv")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")
    assert "products.csv" in response.headers["content-disposition"]

    rows = parse_csv_response(response)

    assert len(rows) == 1
    assert rows[0]["sku"] == "CSV-001"
    assert rows[0]["name"] == "CSV Product"
    assert rows[0]["quantity"] == "12"
    assert rows[0]["price"] == "15.99"
    assert rows[0]["is_active"] == "True"


def test_low_stock_csv_export(client: TestClient):
    create_test_product(
        client,
        sku="LOWCSV-001",
        name="Low CSV Product",
        quantity=2,
        price="5.50",
    )

    create_test_product(
        client,
        sku="HIGHCSV-001",
        name="High CSV Product",
        quantity=20,
        price="8.50",
    )

    response = client.get("/reports/low-stock.csv?threshold=5")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")
    assert "low_stock_products.csv" in response.headers["content-disposition"]

    rows = parse_csv_response(response)

    assert len(rows) == 1
    assert rows[0]["sku"] == "LOWCSV-001"
    assert rows[0]["name"] == "Low CSV Product"
    assert rows[0]["quantity"] == "2"


def test_orders_csv_export(client: TestClient):
    product_id = create_test_product(
        client,
        sku="ORDERCSV-001",
        name="Order CSV Product",
        quantity=20,
        price="11.00",
    )

    order_id = create_order(
        client,
        customer_name="CSV Order Customer",
        product_id=product_id,
        quantity=3,
    )

    client.patch(
        f"/orders/{order_id}/status",
        json={"status": "paid"},
    )

    response = client.get("/reports/orders.csv")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")
    assert "orders.csv" in response.headers["content-disposition"]

    rows = parse_csv_response(response)

    assert len(rows) == 1
    assert rows[0]["customer_name"] == "CSV Order Customer"
    assert rows[0]["status"] == "paid"
    assert rows[0]["total_amount"] == "33.00"
    assert rows[0]["item_count"] == "3"


def test_orders_csv_export_can_filter_by_status(client: TestClient):
    product_id = create_test_product(
        client,
        sku="FILTERCSV-001",
        name="Filter CSV Product",
        quantity=50,
        price="7.00",
    )

    paid_order_id = create_order(
        client,
        customer_name="Paid CSV Customer",
        product_id=product_id,
        quantity=2,
    )

    create_order(
        client,
        customer_name="Pending CSV Customer",
        product_id=product_id,
        quantity=2,
    )

    client.patch(
        f"/orders/{paid_order_id}/status",
        json={"status": "paid"},
    )

    response = client.get("/reports/orders.csv?status_filter=paid")

    assert response.status_code == 200

    rows = parse_csv_response(response)

    assert len(rows) == 1
    assert rows[0]["customer_name"] == "Paid CSV Customer"
    assert rows[0]["status"] == "paid"