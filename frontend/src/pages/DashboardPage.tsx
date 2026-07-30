import { useQuery } from "@tanstack/react-query";
import { getDashboardData } from "../api/client";
import "./DashboardPage.css";

const currencyFormatter = new Intl.NumberFormat("en-US", {
  style: "currency",
  currency: "USD",
});

export function DashboardPage() {
  const dashboardQuery = useQuery({
    queryKey: ["dashboard"],
    queryFn: getDashboardData,
  });

  if (dashboardQuery.isPending) {
    return (
      <section className="dashboard-state">
        <p>Loading dashboard data...</p>
      </section>
    );
  }

  if (dashboardQuery.isError) {
    const message =
      dashboardQuery.error instanceof Error
        ? dashboardQuery.error.message
        : "An unexpected error occurred.";

    return (
      <section className="dashboard-state dashboard-error">
        <h1>Dashboard unavailable</h1>
        <p>{message}</p>

        <button
          type="button"
          onClick={() => void dashboardQuery.refetch()}
        >
          Try again
        </button>
      </section>
    );
  }

  const { products, lowStock, revenue } = dashboardQuery.data;

  const totalUnits = products.reduce(
    (total, product) => total + product.quantity,
    0,
  );

  return (
    <section className="dashboard-page">
      <header className="dashboard-header">
        <div>
          <p className="dashboard-kicker">Overview</p>
          <h1>Inventory dashboard</h1>
          <p>
            Live product, stock, and revenue information from the FastAPI
            backend.
          </p>
        </div>

        <button
          className="dashboard-refresh"
          type="button"
          disabled={dashboardQuery.isFetching}
          onClick={() => void dashboardQuery.refetch()}
        >
          {dashboardQuery.isFetching ? "Refreshing..." : "Refresh data"}
        </button>
      </header>

      <div className="dashboard-metrics">
        <article className="dashboard-metric-card">
          <span>Total products</span>
          <strong>{products.length}</strong>
          <small>Active catalog entries</small>
        </article>

        <article className="dashboard-metric-card">
          <span>Units on hand</span>
          <strong>{totalUnits}</strong>
          <small>Across all active products</small>
        </article>

        <article className="dashboard-metric-card">
          <span>Low-stock products</span>
          <strong>{lowStock.length}</strong>
          <small>Five units or fewer</small>
        </article>

        <article className="dashboard-metric-card">
          <span>Total revenue</span>
          <strong>
            {currencyFormatter.format(Number(revenue.total_revenue))}
          </strong>
          <small>
            {revenue.paid_or_shipped_order_count} paid or shipped orders
          </small>
        </article>
      </div>

      <article className="dashboard-panel">
        <div className="dashboard-panel-header">
          <div>
            <h2>Low-stock inventory</h2>
            <p>Products that may require replenishment.</p>
          </div>
        </div>

        {lowStock.length === 0 ? (
          <p className="dashboard-empty">
            No products are currently below the stock threshold.
          </p>
        ) : (
          <div className="dashboard-table-wrapper">
            <table className="dashboard-table">
              <thead>
                <tr>
                  <th>SKU</th>
                  <th>Product</th>
                  <th>Quantity</th>
                  <th>Status</th>
                </tr>
              </thead>

              <tbody>
                {lowStock.map((product) => (
                  <tr key={product.sku}>
                    <td>{product.sku}</td>
                    <td>{product.name}</td>
                    <td>{product.quantity}</td>
                    <td>
                      <span className="dashboard-stock-pill">Low stock</span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </article>
    </section>
  );
}