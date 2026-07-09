from fastapi import Depends, FastAPI
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database import get_db
from app.routers.inventory import router as inventory_router
from app.routers.orders import router as orders_router
from app.routers.products import router as products_router
from app.routers.reports import router as reports_router

app = FastAPI(
    title="Inventory API",
    description="Inventory and order management backend with stock validation, order workflows, and reporting.",
    version="0.1.0",
)

app.include_router(products_router)
app.include_router(inventory_router)
app.include_router(orders_router)
app.include_router(reports_router)


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.get("/health/db")
def database_health_check(db: Session = Depends(get_db)):
    db.execute(text("SELECT 1"))
    return {"database": "ok"}