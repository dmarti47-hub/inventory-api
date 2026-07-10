from fastapi.testclient import TestClient


def create_test_product(client: TestClient, quantity: int = 10) -> int:
    response = client.post(
        "/products",
        json={
            "sku": "INV-001",
            "name": "Inventory Product",
            "description": "Used for inventory tests",
            "quantity": quantity,
            "price": "29.99",
        },
    )

    assert response.status_code == 201

    return response.json()["id"]


def test_add_inventory(client: TestClient):
    product_id = create_test_product(client, quantity=10)

    response = client.post(
        "/inventory/adjust",
        json={
            "product_id": product_id,
            "quantity_change": 5,
            "reason": "supplier restock",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["product_id"] == product_id
    assert data["previous_quantity"] == 10
    assert data["new_quantity"] == 15
    assert data["adjustment"]["quantity_change"] == 5
    assert data["adjustment"]["reason"] == "supplier restock"


def test_remove_inventory(client: TestClient):
    product_id = create_test_product(client, quantity=10)

    response = client.post(
        "/inventory/adjust",
        json={
            "product_id": product_id,
            "quantity_change": -4,
            "reason": "damaged items",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["previous_quantity"] == 10
    assert data["new_quantity"] == 6


def test_inventory_cannot_go_below_zero(client: TestClient):
    product_id = create_test_product(client, quantity=3)

    response = client.post(
        "/inventory/adjust",
        json={
            "product_id": product_id,
            "quantity_change": -10,
            "reason": "bad adjustment",
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Inventory cannot go below zero."


def test_inventory_adjustment_requires_nonzero_change(client: TestClient):
    product_id = create_test_product(client, quantity=3)

    response = client.post(
        "/inventory/adjust",
        json={
            "product_id": product_id,
            "quantity_change": 0,
            "reason": "zero adjustment",
        },
    )

    assert response.status_code == 422
