from fastapi.testclient import TestClient


def create_test_product(
    client: TestClient,
    *,
    sku: str = "ORDER-001",
    quantity: int = 10,
    price: str = "25.00",
) -> int:
    response = client.post(
        "/products",
        json={
            "sku": sku,
            "name": f"Product {sku}",
            "description": "Product used for order testing",
            "quantity": quantity,
            "price": price,
        },
    )

    assert response.status_code == 201

    return response.json()["id"]


def test_create_order_deducts_inventory(client: TestClient):
    product_id = create_test_product(
        client,
        quantity=10,
        price="25.00",
    )

    response = client.post(
        "/orders",
        json={
            "customer_name": "Jane Smith",
            "items": [
                {
                    "product_id": product_id,
                    "quantity": 2,
                }
            ],
        },
    )

    assert response.status_code == 201

    order = response.json()

    assert order["customer_name"] == "Jane Smith"
    assert order["status"] == "pending"
    assert order["total_amount"] == "50.00"
    assert len(order["items"]) == 1
    assert order["items"][0]["product_id"] == product_id
    assert order["items"][0]["quantity"] == 2
    assert order["items"][0]["unit_price"] == "25.00"
    assert order["items"][0]["line_total"] == "50.00"

    product_response = client.get(f"/products/{product_id}")

    assert product_response.status_code == 200
    assert product_response.json()["quantity"] == 8


def test_order_with_multiple_products_calculates_total(client: TestClient):
    first_product_id = create_test_product(
        client,
        sku="MULTI-001",
        quantity=10,
        price="10.00",
    )

    second_product_id = create_test_product(
        client,
        sku="MULTI-002",
        quantity=10,
        price="15.50",
    )

    response = client.post(
        "/orders",
        json={
            "customer_name": "Multiple Item Customer",
            "items": [
                {
                    "product_id": first_product_id,
                    "quantity": 2,
                },
                {
                    "product_id": second_product_id,
                    "quantity": 3,
                },
            ],
        },
    )

    assert response.status_code == 201

    order = response.json()

    assert order["total_amount"] == "66.50"
    assert len(order["items"]) == 2

    first_product = client.get(f"/products/{first_product_id}").json()
    second_product = client.get(f"/products/{second_product_id}").json()

    assert first_product["quantity"] == 8
    assert second_product["quantity"] == 7


def test_duplicate_product_lines_are_combined(client: TestClient):
    product_id = create_test_product(
        client,
        quantity=10,
        price="5.00",
    )

    response = client.post(
        "/orders",
        json={
            "customer_name": "Duplicate Line Customer",
            "items": [
                {
                    "product_id": product_id,
                    "quantity": 2,
                },
                {
                    "product_id": product_id,
                    "quantity": 3,
                },
            ],
        },
    )

    assert response.status_code == 201

    order = response.json()

    assert order["total_amount"] == "25.00"
    assert len(order["items"]) == 1
    assert order["items"][0]["quantity"] == 5

    product = client.get(f"/products/{product_id}").json()

    assert product["quantity"] == 5


def test_overselling_is_rejected_without_changing_stock(client: TestClient):
    product_id = create_test_product(
        client,
        quantity=3,
        price="20.00",
    )

    response = client.post(
        "/orders",
        json={
            "customer_name": "Oversell Customer",
            "items": [
                {
                    "product_id": product_id,
                    "quantity": 5,
                }
            ],
        },
    )

    assert response.status_code == 400

    detail = response.json()["detail"]

    assert "Insufficient stock" in detail
    assert "Available: 3" in detail
    assert "requested: 5" in detail

    product = client.get(f"/products/{product_id}").json()

    assert product["quantity"] == 3

    orders_response = client.get("/orders")

    assert orders_response.status_code == 200
    assert orders_response.json() == []


def test_canceling_order_restores_inventory(client: TestClient):
    product_id = create_test_product(
        client,
        quantity=10,
        price="12.00",
    )

    create_response = client.post(
        "/orders",
        json={
            "customer_name": "Cancellation Customer",
            "items": [
                {
                    "product_id": product_id,
                    "quantity": 4,
                }
            ],
        },
    )

    assert create_response.status_code == 201

    order_id = create_response.json()["id"]

    product_after_order = client.get(f"/products/{product_id}").json()

    assert product_after_order["quantity"] == 6

    cancel_response = client.patch(
        f"/orders/{order_id}/status",
        json={"status": "canceled"},
    )

    assert cancel_response.status_code == 200
    assert cancel_response.json()["status"] == "canceled"

    product_after_cancel = client.get(f"/products/{product_id}").json()

    assert product_after_cancel["quantity"] == 10


def test_valid_order_status_workflow(client: TestClient):
    product_id = create_test_product(client)

    create_response = client.post(
        "/orders",
        json={
            "customer_name": "Status Customer",
            "items": [
                {
                    "product_id": product_id,
                    "quantity": 1,
                }
            ],
        },
    )

    order_id = create_response.json()["id"]

    paid_response = client.patch(
        f"/orders/{order_id}/status",
        json={"status": "paid"},
    )

    assert paid_response.status_code == 200
    assert paid_response.json()["status"] == "paid"

    shipped_response = client.patch(
        f"/orders/{order_id}/status",
        json={"status": "shipped"},
    )

    assert shipped_response.status_code == 200
    assert shipped_response.json()["status"] == "shipped"


def test_shipped_order_cannot_be_canceled(client: TestClient):
    product_id = create_test_product(client, quantity=10)

    create_response = client.post(
        "/orders",
        json={
            "customer_name": "Shipped Customer",
            "items": [
                {
                    "product_id": product_id,
                    "quantity": 2,
                }
            ],
        },
    )

    order_id = create_response.json()["id"]

    client.patch(
        f"/orders/{order_id}/status",
        json={"status": "paid"},
    )

    client.patch(
        f"/orders/{order_id}/status",
        json={"status": "shipped"},
    )

    cancel_response = client.patch(
        f"/orders/{order_id}/status",
        json={"status": "canceled"},
    )

    assert cancel_response.status_code == 400
    assert cancel_response.json()["detail"] == (
        "Cannot change order status from 'shipped' to 'canceled'."
    )

    product = client.get(f"/products/{product_id}").json()

    assert product["quantity"] == 8
