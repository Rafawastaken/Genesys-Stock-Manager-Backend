# app/api/v1/brands.py
from __future__ import annotations
from typing import Annotated

from fastapi import APIRouter, Query, Depends

from app.infra.uow import UoW
from app.core.deps import get_uow, require_access_token
from app.schemas.brands import BrandListOut
from app.domains.catalog.usecases.brands import list_brands as uc_list

# eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpYXQiOjE3NjM0NjkyNDcsImV4cCI6MTc2MzQ3NjQ0Nywic3ViIjoiNDgiLCJyb2xlIjoiYWRtaW4iLCJ0eXAiOiJhY2Nlc3MiLCJuYW1lIjoiUmFmYWVsIFBpbWVudGEifQ.C7jGaZT7U_XgvU-egfRV6DnZNUEXBDlnUyGho8osCsg

router = APIRouter(prefix="/brands", tags=["brands"], dependencies=[Depends(require_access_token)])
UowDep = Annotated[UoW, Depends(get_uow)]


@router.get("", response_model=BrandListOut)
def list_brands(
    uow: UowDep,  # <— primeiro
    search: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    items, total = uc_list.execute(uow, search=search, page=page, page_size=page_size)
    return {"items": items, "total": total, "page": page, "page_size": page_size}
