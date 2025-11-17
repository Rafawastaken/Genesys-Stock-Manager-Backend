from __future__ import annotations
from typing import Annotated

from fastapi import APIRouter, Query, Depends

from app.infra.uow import UoW
from app.core.deps import get_uow, require_access_token
from app.schemas.categories import CategoryListOut
from app.domains.catalog.usecases.categories import list_categories as uc_list

router = APIRouter(prefix="/categories", tags=["categories"])
UowDep = Annotated[UoW, Depends(get_uow)]


@router.get("", response_model=CategoryListOut, dependencies=[Depends(require_access_token)])
def list_categories(
    uow: UowDep,
    search: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    items, total = uc_list.execute(uow, search=search, page=page, page_size=page_size)
    return {"items": items, "total": total, "page": page, "page_size": page_size}
