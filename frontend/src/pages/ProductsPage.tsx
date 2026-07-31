import { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { getProducts } from "../api/client";
import "./ProductsPage.css";

const currencyFormatter = new Intl.NumberFormat("en-US", {
  style: "currency",
  currency: "USD",
});

export function ProductsPage() {
  const [searchTerm, setSearchTerm] = useState("");

  const productsQuery = useQuery({
    queryKey: ["products"],
    queryFn: getProducts,
  });

  const filteredProducts = useMemo(() => {
    const products = productsQuery.data ?? [];
    const search = searchTerm.trim().toLowerCase();

    if (!search) {
      return products;
    }

    return products.filter(
      (product) =>
        product.name.toLowerCase().includes(search) ||
        product.sku.toLowerCase().includes(search),
    );
  }, [productsQuery.data, searchTerm]);

  if (productsQuery.isPending) {
    return <section className="products-state">Loading products...</section>;
  }

  if (productsQuery.isError) {
    return (
      <section className="products-state products-error">
        <h1>Products unavailable</h1>
        <p>
          {productsQuery.error instanceof Error
            ? productsQuery.error.message
            : "An unexpected error occurred."}
        </p>

        <button
          type="button"
          onClick={() => void productsQuery.refetch()}
        >
          Try again
        </button>
      </section>
    );
  }

  return (
    <section className="products-page">
      <header className="products-header">
        <div>
          <p className="products-kicker">Catalog</p>
          <h1>Products</h1>
          <p>Search the active product catalog and review stock levels.</p>
        </div>
      </header>

      <article className="products-panel">
        <div className="products-toolbar">
          <div className="products-search">
            <label htmlFor="product-search">Search products</label>
            <input
              id="product-search"
              type="search"
              value={searchTerm}
              placeholder="Search by product name or SKU"
              onChange={(event) => setSearchTerm(event.target.value)}
            />
          </div>

          <span className="products-count">
            {filteredProducts.length} of {productsQuery.data.length} products
          </span>
        </div>

        <div className="products-table-wrapper">
          <table className="products-table">
            <thead>
              <tr>
                <th>SKU</th>
                <th>Product</th>
                <th>Price</th>
                <th>Quantity</th>
                <th>Stock status</th>
              </tr>
            </thead>

            <tbody>
              {filteredProducts.map((product) => {
                const isLowStock = product.quantity <= 5;

                return (
                  <tr key={product.id}>
                    <td className="products-sku">{product.sku}</td>

                    <td>
                      <strong className="products-name">{product.name}</strong>
                      <span className="products-description">
                        {product.description || "No description provided"}
                      </span>
                    </td>

                    <td>
                      {currencyFormatter.format(Number(product.price))}
                    </td>

                    <td>{product.quantity}</td>

                    <td>
                      <span
                        className={
                          isLowStock
                            ? "products-stock products-stock-low"
                            : "products-stock products-stock-ok"
                        }
                      >
                        {isLowStock ? "Low stock" : "In stock"}
                      </span>
                    </td>
                  </tr>
                );
              })}

              {filteredProducts.length === 0 && (
                <tr>
                  <td className="products-empty" colSpan={5}>
                    No products match your search.
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