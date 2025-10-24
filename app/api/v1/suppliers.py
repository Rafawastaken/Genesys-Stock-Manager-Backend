# app/api/v1/suppliers.py
from fastapi import APIRouter, Depends, Query, status, HTTPException
from app.core.deps import require_access_token, get_uow
from app.infra.uow import UoW
from app.schemas.suppliers import SupplierCreate, SupplierOut, SupplierList
from app.services.queries.suppliers import list_suppliers as q_list
from app.services.commands.suppliers import create_supplier as c_create
from app.services.commands.suppliers import delete_supplier as c_delete

router = APIRouter(prefix="/suppliers", tags=["suppliers"])

@router.get("", response_model=SupplierList)
def list_suppliers(
    search: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
    uow: UoW = Depends(get_uow),
    _=Depends(require_access_token),
):
    items, total = q_list.handle(uow, search=search, page=page, page_size=page_size)
    return {"items": items, "total": total, "page": page, "page_size": page_size}

@router.post("", response_model=SupplierOut, status_code=status.HTTP_201_CREATED)
def create_supplier(
    payload: SupplierCreate,
    uow: UoW = Depends(get_uow),
    _=Depends(require_access_token),
):
    return c_create.handle(uow, data=payload)

@router.delete("/{supplier_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_supplier_endpoint(
    supplier_id: int,
    uow: UoW = Depends(get_uow),
    _=Depends(require_access_token),
):
    try:
        c_delete.handle(uow, supplier_id=supplier_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Supplier not found")
    return  # 204
