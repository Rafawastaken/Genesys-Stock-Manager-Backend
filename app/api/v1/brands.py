# app/api/v1/brands.py
from __future__ import annotations
from typing import Annotated
import logging

from fastapi import APIRouter, Query, Depends

from app.infra.uow import UoW
from app.core.deps import get_uow, require_access_token
from app.schemas.brands import BrandListOut, BrandOut
from app.domains.catalog.usecases.brands import list_brands as uc_list

router = APIRouter(prefix="/brands", tags=["brands"])
UowDep = Annotated[UoW, Depends(get_uow)]
log = logging.getLogger("gsm.api.brands")


@router.get("", response_model=BrandListOut, dependencies=[Depends(require_access_token)])
def list_brands(
    search: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    uow: UoW = Depends(get_uow),
):
    rows, total = uc_list.execute(uow, search=search, page=page, page_size=page_size)
    items = [BrandOut(id=b.id, name=b.name) for b in rows]
    return BrandListOut(items=items, total=total, page=page, page_size=page_size)
