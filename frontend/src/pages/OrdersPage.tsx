import { useState, type FormEvent } from "react";
import {
  useMutation,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";
import {
  createOrder,
  getOrders,
  getProducts,
  updateOrderStatus,
  type Order,
  type OrderStatus,
} from "../api/client";
import "./OrdersPage.css";

interface DraftOrderItem {
  productId: string;
  quantity: string;
}

const statusTransitions: Record<OrderStatus, OrderStatus[]> = {
  pending: ["paid", "canceled"],
  paid: ["shipped", "canceled"],
  shipped: [],
  canceled: [],
};

const actionLabels: Record<OrderStatus, string> = {
  pending: "Mark pending",
  paid: "Mark paid",
  shipped: "Mark shipped",
  canceled: "Cancel order",
};

const currencyFormatter = new Intl.NumberFormat("en-US", {
  style: "currency",
  currency: "USD",
});

function createDraftItem(): DraftOrderItem {
  return {
    productId: "",
    quantity: "1",
  };
}

export function OrdersPage() {
  const queryClient = useQueryClient();

  const [customerName, setCustomerName] = useState("");
  const [draftItems, setDraftItems] = useState<DraftOrderItem[]>([
    createDraftItem(),
  ]);
  const [statusFilter, setStatusFilter] = useState<OrderStatus | "">("");
  const [formError, setFormError] = useState<string | null>(null);
  const [createdOrder, setCreatedOrder] = useState<Order | null>(null);

  const productsQuery = useQuery({
    queryKey: ["products"],
    queryFn: getProducts,
  });

  const ordersQuery = useQuery({
    queryKey: ["orders", statusFilter],
    queryFn: () => getOrders(statusFilter || undefined),
  });

  const createOrderMutation = useMutation({
    mutationFn: createOrder,
    onSuccess: async (order) => {
      setCreatedOrder(order);
      setCustomerName("");
      setDraftItems([createDraftItem()]);

      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["orders"] }),
        queryClient.invalidateQueries({ queryKey: ["products"] }),
        queryClient.invalidateQueries({ queryKey: ["dashboard"] }),
      ]);
    },
  });

  const statusMutation = useMutation({
    mutationFn: ({
      orderId,
      status,
    }: {
      orderId: number;
      status: OrderStatus;
    }) => updateOrderStatus(orderId, status),
    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["orders"] }),
        queryClient.invalidateQueries({ queryKey: ["products"] }),
        queryClient.invalidateQueries({ queryKey: ["dashboard"] }),
      ]);
    },
  });

  const products = productsQuery.data ?? [];
  const orders = ordersQuery.data ?? [];

  const productNames = new Map(
    products.map((product) => [product.id, product.name] as const),
  );

  function updateDraftItem(
    index: number,
    field: keyof DraftOrderItem,
    value: string,
  ) {
    setDraftItems((currentItems) =>
      currentItems.map((item, itemIndex) =>
        itemIndex === index ? { ...item, [field]: value } : item,
      ),
    );
  }

  function addDraftItem() {
    setDraftItems((currentItems) => [
      ...currentItems,
      createDraftItem(),
    ]);
  }

  function removeDraftItem(index: number) {
    setDraftItems((currentItems) =>
      currentItems.filter((_, itemIndex) => itemIndex !== index),
    );
  }

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setFormError(null);
    setCreatedOrder(null);

    const trimmedCustomerName = customerName.trim();

    if (!trimmedCustomerName) {
      setFormError("Enter a customer name.");
      return;
    }

    const parsedItems = draftItems.map((item) => ({
      product_id: Number(item.productId),
      quantity: Number(item.quantity),
    }));

    const hasInvalidItem = parsedItems.some(
      (item) =>
        !Number.isInteger(item.product_id) ||
        item.product_id <= 0 ||
        !Number.isInteger(item.quantity) ||
        item.quantity <= 0,
    );

    if (hasInvalidItem) {
      setFormError(
        "Every order line needs a product and a positive whole-number quantity.",
      );
      return;
    }

    const productIds = parsedItems.map((item) => item.product_id);

    if (new Set(productIds).size !== productIds.length) {
      setFormError("Each product may appear only once per order.");
      return;
    }

    const insufficientStockItem = parsedItems.find((item) => {
      const product = products.find(
        (candidate) => candidate.id === item.product_id,
      );

      return !product || item.quantity > product.quantity;
    });

    if (insufficientStockItem) {
      const product = products.find(
        (candidate) =>
          candidate.id === insufficientStockItem.product_id,
      );

      setFormError(
        product
          ? `${product.name} only has ${product.quantity} units available.`
          : "One of the selected products is unavailable.",
      );
      return;
    }

    createOrderMutation.mutate({
      customer_name: trimmedCustomerName,
      items: parsedItems,
    });
  }

  if (productsQuery.isPending || ordersQuery.isPending) {
    return <section className="orders-state">Loading orders...</section>;
  }

  if (productsQuery.isError || ordersQuery.isError) {
    const queryError = productsQuery.error ?? ordersQuery.error;

    return (
      <section className="orders-state orders-error">
        <h1>Orders unavailable</h1>
        <p>
          {queryError instanceof Error
            ? queryError.message
            : "An unexpected error occurred."}
        </p>
      </section>
    );
  }

  return (
    <section className="orders-page">
      <header className="orders-header">
        <p className="orders-kicker">Order management</p>
        <h1>Orders</h1>
        <p>Create customer orders and manage their fulfillment status.</p>
      </header>

      <div className="orders-layout">
        <article className="orders-card">
          <div className="orders-card-heading">
            <h2>Create order</h2>
            <p>Stock is deducted when the order is created.</p>
          </div>

          <form className="orders-form" onSubmit={handleSubmit}>
            <label htmlFor="customer-name">
              Customer name
              <input
                id="customer-name"
                type="text"
                maxLength={150}
                value={customerName}
                placeholder="Enter customer name"
                onChange={(event) => setCustomerName(event.target.value)}
                required
              />
            </label>

            <fieldset>
              <legend>Order items</legend>

              <div className="orders-draft-items">
                {draftItems.map((item, index) => (
                  <div className="orders-draft-row" key={index}>
                    <label>
                      Product
                      <select
                        value={item.productId}
                        onChange={(event) =>
                          updateDraftItem(
                            index,
                            "productId",
                            event.target.value,
                          )
                        }
                        required
                      >
                        <option value="">Select product</option>

                        {products.map((product) => (
                          <option key={product.id} value={product.id}>
                            {product.name} ({product.quantity} available)
                          </option>
                        ))}
                      </select>
                    </label>

                    <label>
                      Quantity
                      <input
                        type="number"
                        min="1"
                        step="1"
                        value={item.quantity}
                        onChange={(event) =>
                          updateDraftItem(
                            index,
                            "quantity",
                            event.target.value,
                          )
                        }
                        required
                      />
                    </label>

                    <button
                      className="orders-remove-item"
                      type="button"
                      disabled={draftItems.length === 1}
                      onClick={() => removeDraftItem(index)}
                    >
                      Remove
                    </button>
                  </div>
                ))}
              </div>

              <button
                className="orders-add-item"
                type="button"
                onClick={addDraftItem}
              >
                Add another product
              </button>
            </fieldset>

            {formError && (
              <p className="orders-message orders-message-error">
                {formError}
              </p>
            )}

            {createOrderMutation.isError && (
              <p className="orders-message orders-message-error">
                {createOrderMutation.error instanceof Error
                  ? createOrderMutation.error.message
                  : "The order could not be created."}
              </p>
            )}

            {createdOrder && (
              <p className="orders-message orders-message-success">
                Order #{createdOrder.id} created for{" "}
                <strong>{createdOrder.customer_name}</strong> —{" "}
                {currencyFormatter.format(
                  Number(createdOrder.total_amount),
                )}
              </p>
            )}

            <button
              className="orders-submit"
              type="submit"
              disabled={createOrderMutation.isPending}
            >
              {createOrderMutation.isPending
                ? "Creating order..."
                : "Create order"}
            </button>
          </form>
        </article>

        <article className="orders-card">
          <div className="orders-list-heading">
            <div>
              <h2>Order history</h2>
              <p>{orders.length} orders shown</p>
            </div>

            <label htmlFor="status-filter">
              Status
              <select
                id="status-filter"
                value={statusFilter}
                onChange={(event) =>
                  setStatusFilter(
                    event.target.value as OrderStatus | "",
                  )
                }
              >
                <option value="">All statuses</option>
                <option value="pending">Pending</option>
                <option value="paid">Paid</option>
                <option value="shipped">Shipped</option>
                <option value="canceled">Canceled</option>
              </select>
            </label>
          </div>

          {statusMutation.isError && (
            <p className="orders-message orders-message-error orders-status-error">
              {statusMutation.error instanceof Error
                ? statusMutation.error.message
                : "The order status could not be updated."}
            </p>
          )}

          <div className="orders-list">
            {orders.map((order) => (
              <section className="orders-order" key={order.id}>
                <div className="orders-order-heading">
                  <div>
                    <strong>Order #{order.id}</strong>
                    <span>{order.customer_name}</span>
                  </div>

                  <span
                    className={`orders-status orders-status-${order.status}`}
                  >
                    {order.status}
                  </span>
                </div>

                <div className="orders-order-meta">
                  <span>
                    {new Date(order.created_at).toLocaleString()}
                  </span>
                  <strong>
                    {currencyFormatter.format(
                      Number(order.total_amount),
                    )}
                  </strong>
                </div>

                <div className="orders-order-items">
                  {order.items.map((item) => (
                    <div key={item.id}>
                      <span>
                        {productNames.get(item.product_id) ??
                          `Product #${item.product_id}`}
                      </span>

                      <span>
                        {item.quantity} ×{" "}
                        {currencyFormatter.format(
                          Number(item.unit_price),
                        )}
                      </span>

                      <strong>
                        {currencyFormatter.format(
                          Number(item.line_total),
                        )}
                      </strong>
                    </div>
                  ))}
                </div>

                {statusTransitions[order.status].length > 0 && (
                  <div className="orders-actions">
                    {statusTransitions[order.status].map((nextStatus) => (
                      <button
                        className={
                          nextStatus === "canceled"
                            ? "orders-action orders-action-danger"
                            : "orders-action"
                        }
                        type="button"
                        key={nextStatus}
                        disabled={
                          statusMutation.isPending &&
                          statusMutation.variables?.orderId === order.id
                        }
                        onClick={() =>
                          statusMutation.mutate({
                            orderId: order.id,
                            status: nextStatus,
                          })
                        }
                      >
                        {actionLabels[nextStatus]}
                      </button>
                    ))}
                  </div>
                )}
              </section>
            ))}

            {orders.length === 0 && (
              <p className="orders-empty">
                No orders match the selected status.
              </p>
            )}
          </div>
        </article>
      </div>
    </section>
  );
}