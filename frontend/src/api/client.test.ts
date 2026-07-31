import {
  afterEach,
  beforeEach,
  describe,
  expect,
  it,
  vi,
} from "vitest";
import {
  adjustInventory,
  getProducts,
} from "./client";

const fetchMock = vi.fn();

beforeEach(() => {
  fetchMock.mockReset();
  vi.stubGlobal("fetch", fetchMock);
});

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("API client", () => {
  it("retrieves products from the backend", async () => {
    const responseBody = [
      {
        id: 1,
        sku: "MOUSE-001",
        name: "Wireless Mouse",
        description: "Ergonomic wireless mouse",
        quantity: 5,
        price: "29.99",
        is_active: true,
      },
    ];

    fetchMock.mockResolvedValue(
      new Response(JSON.stringify(responseBody), {
        status: 200,
        headers: {
          "Content-Type": "application/json",
        },
      }),
    );

    await expect(getProducts()).resolves.toEqual(responseBody);

    expect(fetchMock).toHaveBeenCalledWith(
      "http://127.0.0.1:8001/products",
      {},
    );
  });

  it("sends an inventory adjustment as JSON", async () => {
    const responseBody = {
      product_id: 1,
      sku: "MOUSE-001",
      name: "Wireless Mouse",
      previous_quantity: 5,
      new_quantity: 7,
      adjustment: {
        id: 10,
        product_id: 1,
        quantity_change: 2,
        reason: "Test restock",
        created_at: "2026-07-30T12:00:00Z",
      },
    };

    fetchMock.mockResolvedValue(
      new Response(JSON.stringify(responseBody), {
        status: 201,
        headers: {
          "Content-Type": "application/json",
        },
      }),
    );

    await expect(
      adjustInventory({
        product_id: 1,
        quantity_change: 2,
        reason: "Test restock",
      }),
    ).resolves.toEqual(responseBody);

    expect(fetchMock).toHaveBeenCalledWith(
      "http://127.0.0.1:8001/inventory/adjust",
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          product_id: 1,
          quantity_change: 2,
          reason: "Test restock",
        }),
      },
    );
  });

  it("surfaces backend error details", async () => {
    fetchMock.mockResolvedValue(
      new Response(
        JSON.stringify({
          detail: "Inventory cannot go below zero.",
        }),
        {
          status: 400,
          statusText: "Bad Request",
          headers: {
            "Content-Type": "application/json",
          },
        },
      ),
    );

    await expect(
      adjustInventory({
        product_id: 1,
        quantity_change: -100,
        reason: "Invalid adjustment",
      }),
    ).rejects.toThrow("Inventory cannot go below zero.");
  });
});