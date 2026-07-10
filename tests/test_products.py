from fastapi.testclient import TestClient


def test_create_product(client: TestClient):
    response = client.post(
        "/products",
        json={
            "sku": "TEST-001",
            "name": "Test Product",
            "description": "A test product",
            "quantity": 10,
            "price": "19.99",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["id"] == 1
    assert data["sku"] == "TEST-001"
    assert data["name"] == "Test Product"
    assert data["quantity"] == 10
    assert data["price"] == "19.99"
    assert data["is_active"] is True


def test_duplicate_sku_returns_conflict(client: TestClient):
    product_payload = {
        "sku": "DUP-001",
        "name": "Duplicate Product",
        "description": "Testing duplicate SKUs",
        "quantity": 5,
        "price": "9.99",
    }

    first_response = client.post("/products", json=product_payload)
    second_response = client.post("/products", json=product_payload)

    assert first_response.status_code == 201
    assert second_response.status_code == 409
    assert second_response.json()["detail"] == "A product with this SKU already exists."


def test_list_products(client: TestClient):
    client.post(
        "/products",
        json={
            "sku": "LIST-001",
            "name": "Listed Product",
            "description": None,
            "quantity": 3,
            "price": "4.99",
        },
    )

    response = client.get("/products")

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1
    assert data[0]["sku"] == "LIST-001"


def test_soft_delete_product_hides_from_default_list(client: TestClient):
    create_response = client.post(
        "/products",
        json={
            "sku": "DELETE-001",
            "name": "Delete Me",
            "description": None,
            "quantity": 7,
            "price": "14.99",
        },
    )

    product_id = create_response.json()["id"]

    delete_response = client.delete(f"/products/{product_id}")
    list_response = client.get("/products")
    include_inactive_response = client.get("/products?include_inactive=true")

    assert delete_response.status_code == 204
    assert list_response.status_code == 200
    assert list_response.json() == []
    assert include_inactive_response.status_code == 200
    assert include_inactive_response.json()[0]["is_active"] is False
