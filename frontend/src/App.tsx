import { useQuery } from "@tanstack/react-query";
import { Navigate, NavLink, Route, Routes } from "react-router-dom";
import { getHealth } from "./api/client";
import { DashboardPage } from "./pages/DashboardPage";
import { ProductsPage } from "./pages/ProductsPage";
import { InventoryPage } from "./pages/InventoryPage";
import { OrdersPage } from "./pages/OrdersPage";
import "./App.css";

const navigation = [
  { path: "/dashboard", label: "Dashboard" },
  { path: "/products", label: "Products" },
  { path: "/inventory", label: "Inventory" },
  { path: "/orders", label: "Orders" },
];

function App() {
  const healthQuery = useQuery({
  queryKey: ["health"],
  queryFn: getHealth,
  refetchInterval: 30_000,
});

const apiStatus = healthQuery.isPending
  ? "Checking API..."
  : healthQuery.isSuccess
    ? "API connected"
    : "API unavailable";

const statusClass = healthQuery.isSuccess
  ? "status-dot connected"
  : healthQuery.isError
    ? "status-dot error"
    : "status-dot";
  
  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <span className="brand-mark">IC</span>
          <div>
            <strong>Inventory Control</strong>
            <small>Operations Portal</small>
          </div>
        </div>

        <nav aria-label="Primary navigation">
          {navigation.map((item) => (
            <NavLink
              className={({ isActive }) =>
                isActive ? "nav-link active" : "nav-link"
              }
              key={item.path}
              to={item.path}
            >
              {item.label}
            </NavLink>
          ))}
        </nav>

        <div className="sidebar-footer">
          <span className={statusClass} />
          {apiStatus}
        </div>
      </aside>

      <main className="main-content">
        <Routes>
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
          <Route path="/dashboard" element={<DashboardPage />} />
          <Route path="/products" element={<ProductsPage />} />
          <Route path="/inventory" element={<InventoryPage />} />
          <Route path="/orders" element={<OrdersPage />} />
          <Route path="*" element={<Navigate to="/dashboard" replace />} />
        </Routes>
      </main>
    </div>
  );
}

export default App;