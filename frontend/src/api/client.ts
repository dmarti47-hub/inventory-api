const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8001";

export type ApiDecimal = number | string;

export interface HealthResponse {
  status: string;
}

export interface Product {
  id: number;
  sku: string;
  name: string;
  description: string | null;
  quantity: number;
  price: ApiDecimal;
  is_active: boolean;
}

export interface LowStockProduct {
  id: number;
  sku: string;
  name: string;
  quantity: number;
  price: ApiDecimal;
}

export interface RevenueSummary {
  paid_or_shipped_order_count: number;
  total_revenue: ApiDecimal;
  average_order_value: ApiDecimal;
}

export interface DashboardData {
  products: Product[];
  lowStock: LowStockProduct[];
  revenue: RevenueSummary;
}

export interface InventoryAdjustment {
  id: number;
  product_id: number;
  quantity_change: number;
  reason: string | null;
  created_at: string;
}

export interface InventoryAdjustmentInput {
  product_id: number;
  quantity_change: number;
  reason?: string | null;
}

export interface InventoryAdjustmentResult {
  product_id: number;
  sku: string;
  name: string;
  previous_quantity: number;
  new_quantity: number;
  adjustment: InventoryAdjustment;
}

export type OrderStatus =
  | "pending"
  | "paid"
  | "shipped"
  | "canceled";

export interface OrderItemInput {
  product_id: number;
  quantity: number;
}

export interface OrderInput {
  customer_name: string;
  items: OrderItemInput[];
}

export interface OrderItem {
  id: number;
  product_id: number;
  quantity: number;
  unit_price: ApiDecimal;
  line_total: ApiDecimal;
}

export interface Order {
  id: number;
  customer_name: string;
  status: OrderStatus;
  total_amount: ApiDecimal;
  created_at: string;
  updated_at: string;
  items: OrderItem[];
}

async function apiRequest<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, options);

  if (!response.ok) {
    let message = `API request failed: ${response.status} ${response.statusText}`;

    const errorBody: unknown = await response.json().catch(() => null);

    if (
      errorBody &&
      typeof errorBody === "object" &&
      "detail" in errorBody &&
      typeof errorBody.detail === "string"
    ) {
      message = errorBody.detail;
    }

    throw new Error(message);
  }

  return response.json() as Promise<T>;
}

export function getHealth(): Promise<HealthResponse> {
  return apiRequest<HealthResponse>("/health");
}

export function getProducts(): Promise<Product[]> {
  return apiRequest<Product[]>("/products");
}

export function getLowStockProducts(
  threshold = 5,
): Promise<LowStockProduct[]> {
  return apiRequest<LowStockProduct[]>(
    `/reports/low-stock?threshold=${threshold}`,
  );
}

export function getRevenueSummary(): Promise<RevenueSummary> {
  return apiRequest<RevenueSummary>("/reports/revenue-summary");
}

export async function getDashboardData(): Promise<DashboardData> {
  const [products, lowStock, revenue] = await Promise.all([
    getProducts(),
    getLowStockProducts(),
    getRevenueSummary(),
  ]);

  return {
    products,
    lowStock,
    revenue,
  };
}

export function getInventoryAdjustments(): Promise<InventoryAdjustment[]> {
  return apiRequest<InventoryAdjustment[]>("/inventory/adjustments");
}

export function adjustInventory(
  input: InventoryAdjustmentInput,
): Promise<InventoryAdjustmentResult> {
  return apiRequest<InventoryAdjustmentResult>("/inventory/adjust", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(input),
  });
}

export function getOrders(
  statusFilter?: OrderStatus,
): Promise<Order[]> {
  const query = statusFilter
    ? `?status_filter=${encodeURIComponent(statusFilter)}`
    : "";

  return apiRequest<Order[]>(`/orders${query}`);
}

export function getOrder(orderId: number): Promise<Order> {
  return apiRequest<Order>(`/orders/${orderId}`);
}

export function createOrder(input: OrderInput): Promise<Order> {
  return apiRequest<Order>("/orders", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(input),
  });
}

export function updateOrderStatus(
  orderId: number,
  status: OrderStatus,
): Promise<Order> {
  return apiRequest<Order>(`/orders/${orderId}/status`, {
    method: "PATCH",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ status }),
  });
}