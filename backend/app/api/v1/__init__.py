from fastapi import APIRouter

from app.api.v1.imports import router as imports_router
from app.api.v1.expenses import router as expenses_router
from app.api.v1.anomalies import router as anomalies_router
from app.api.v1.reports import router as reports_router

router = APIRouter()

router.include_router(imports_router, prefix="/imports", tags=["imports"])
router.include_router(expenses_router, prefix="/expenses", tags=["expenses"])
router.include_router(anomalies_router, prefix="/anomalies", tags=["anomalies"])
router.include_router(reports_router, prefix="/reports", tags=["reports"])
