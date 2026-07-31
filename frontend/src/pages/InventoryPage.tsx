import { useState, type FormEvent } from "react";
import {
  useMutation,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";
import {
  adjustInventory,
  getInventoryAdjustments,
  getProducts,
  type InventoryAdjustmentResult,
} from "../api/client";
import "./InventoryPage.css";

export function InventoryPage() {
  const queryClient = useQueryClient();

  const [productId, setProductId] = useState("");
  const [quantityChange, setQuantityChange] = useState("");
  const [reason, setReason] = useState("");
  const [formError, setFormError] = useState<string | null>(null);
  const [lastResult, setLastResult] =
    useState<InventoryAdjustmentResult | null>(null);

  const productsQuery = useQuery({
    queryKey: ["products"],
    queryFn: getProducts,
  });

  const adjustmentsQuery = useQuery({
    queryKey: ["inventory-adjustments"],
    queryFn: getInventoryAdjustments,
  });

  const inventoryMutation = useMutation({
    mutationFn: adjustInventory,
    onSuccess: async (result) => {
      setLastResult(result);
      setQuantityChange("");
      setReason("");

      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["products"] }),
        queryClient.invalidateQueries({ queryKey: ["dashboard"] }),
        queryClient.invalidateQueries({
          queryKey: ["inventory-adjustments"],
        }),
      ]);
    },
  });

  const products = productsQuery.data ?? [];
  const adjustments = adjustmentsQuery.data ?? [];

  const productNames = new Map(
    products.map((product) => [product.id, product.name]),
  );  

  const selectedProduct = products.find(
    (product) => product.id === Number(productId),
  );

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setFormError(null);
    setLastResult(null);

    const parsedProductId = Number(productId);
    const parsedQuantityChange = Number(quantityChange);

    if (!Number.isInteger(parsedProductId) || parsedProductId <= 0) {
      setFormError("Select a product.");
      return;
    }

    if (
      !Number.isInteger(parsedQuantityChange) ||
      parsedQuantityChange === 0
    ) {
      setFormError("Quantity change must be a nonzero whole number.");
      return;
    }

    inventoryMutation.mutate({
      product_id: parsedProductId,
      quantity_change: parsedQuantityChange,
      reason: reason.trim() || null,
    });
  }

  if (productsQuery.isPending || adjustmentsQuery.isPending) {
    return <section className="inventory-state">Loading inventory...</section>;
  }

  if (productsQuery.isError || adjustmentsQuery.isError) {
    const queryError = productsQuery.error ?? adjustmentsQuery.error;

    return (
      <section className="inventory-state inventory-error">
        <h1>Inventory unavailable</h1>
        <p>
          {queryError instanceof Error
            ? queryError.message
            : "An unexpected error occurred."}
        </p>
      </section>
    );
  }

  return (
    <section className="inventory-page">
      <header className="inventory-header">
        <p className="inventory-kicker">Stock control</p>
        <h1>Inventory</h1>
        <p>Record stock additions and removals with an audit trail.</p>
      </header>

      <div className="inventory-layout">
        <article className="inventory-card">
          <div className="inventory-card-heading">
            <h2>Adjust inventory</h2>
            <p>Use positive numbers to add stock and negative numbers to remove it.</p>
          </div>

          <form className="inventory-form" onSubmit={handleSubmit}>
            <label htmlFor="inventory-product">
              Product
              <select
                id="inventory-product"
                value={productId}
                onChange={(event) => setProductId(event.target.value)}
                required
              >
                <option value="">Select a product</option>

                {products.map((product) => (
                  <option key={product.id} value={product.id}>
                    {product.sku} — {product.name}
                  </option>
                ))}
              </select>
            </label>

            {selectedProduct && (
              <p className="inventory-current-stock">
                Current stock: <strong>{selectedProduct.quantity}</strong>
              </p>
            )}

            <label htmlFor="quantity-change">
              Quantity change
              <input
                id="quantity-change"
                type="number"
                step="1"
                value={quantityChange}
                placeholder="Example: 10 or -3"
                onChange={(event) => setQuantityChange(event.target.value)}
                required
              />
            </label>

            <label htmlFor="inventory-reason">
              Reason
              <input
                id="inventory-reason"
                type="text"
                maxLength={255}
                value={reason}
                placeholder="Shipment received, damaged item, correction..."
                onChange={(event) => setReason(event.target.value)}
              />
            </label>

            {formError && (
              <p className="inventory-message inventory-message-error">
                {formError}
              </p>
            )}

            {inventoryMutation.isError && (
              <p className="inventory-message inventory-message-error">
                {inventoryMutation.error instanceof Error
                  ? inventoryMutation.error.message
                  : "The adjustment could not be saved."}
              </p>
            )}

            {lastResult && (
              <p className="inventory-message inventory-message-success">
                {lastResult.name} changed from{" "}
                <strong>{lastResult.previous_quantity}</strong> to{" "}
                <strong>{lastResult.new_quantity}</strong>.
              </p>
            )}

            <button
              type="submit"
              disabled={inventoryMutation.isPending}
            >
              {inventoryMutation.isPending
                ? "Saving adjustment..."
                : "Save adjustment"}
            </button>
          </form>
        </article>

        <article className="inventory-card">
          <div className="inventory-card-heading">
            <h2>Current stock</h2>
            <p>Live quantities for active products.</p>
          </div>

          <div className="inventory-stock-list">
            {products.map((product) => (
              <div className="inventory-stock-row" key={product.id}>
                <div>
                  <strong>{product.name}</strong>
                  <span>{product.sku}</span>
                </div>

                <span
                  className={
                    product.quantity <= 5
                      ? "inventory-quantity inventory-quantity-low"
                      : "inventory-quantity"
                  }
                >
                  {product.quantity}
                </span>
              </div>
            ))}
          </div>
        </article>
      </div>

      <article className="inventory-card">
        <div className="inventory-card-heading">
          <h2>Recent adjustments</h2>
          <p>The latest inventory audit entries.</p>
        </div>

        <div className="inventory-table-wrapper">
          <table className="inventory-table">
            <thead>
              <tr>
                <th>Date</th>
                <th>Product</th>
                <th>Change</th>
                <th>Reason</th>
              </tr>
            </thead>

            <tbody>
              {adjustments.map((adjustment) => (
                <tr key={adjustment.id}>
                  <td>
                    {new Date(adjustment.created_at).toLocaleString()}
                  </td>
                  <td>
                    {productNames.get(adjustment.product_id) ??
                      `Product #${adjustment.product_id}`}
                  </td>
                  <td>
                    <strong
                      className={
                        adjustment.quantity_change > 0
                          ? "inventory-change-positive"
                          : "inventory-change-negative"
                      }
                    >
                      {adjustment.quantity_change > 0 ? "+" : ""}
                      {adjustment.quantity_change}
                    </strong>
                  </td>
                  <td>{adjustment.reason || "—"}</td>
                </tr>
              ))}

              {adjustments.length === 0 && (
                <tr>
                  <td className="inventory-empty" colSpan={4}>
                    No inventory adjustments have been recorded.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </article>
    </section>
  );
}