from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.report import LowStockProduct, RevenueSummary
from app.services.report_service import get_low_stock_products, get_revenue_summary

router = APIRouter(prefix="/reports", tags=["Reports"])


@router.get("/low-stock", response_model=list[LowStockProduct])
def low_stock_report(
    threshold: int = Query(default=5, ge=0),
    db: Session = Depends(get_db),
):
    return get_low_stock_products(db=db, threshold=threshold)


@router.get("/revenue-summary", response_model=RevenueSummary)
def revenue_summary(db: Session = Depends(get_db)):
    return get_revenue_summary(db=db)
