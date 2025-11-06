# app/api/v1/suppliers.py
from fastapi import APIRouter, Depends, Query, status, HTTPException, Path
from app.core.deps import require_access_token, get_uow
from app.infra.uow import UoW

from app.schemas.suppliers import SupplierCreate, SupplierOut, SupplierList, SupplierDetailOut, SupplierBundleUpdate
from app.domains.procurement.usecases.suppliers.create_supplier import execute as uc_create
from app.domains.procurement.usecases.suppliers.delete_supplier import execute as uc_delete
from app.domains.procurement.usecases.suppliers.update_bundle import execute as uc_update
from app.domains.procurement.usecases.suppliers.get_supplier_detail import execute as uc_q_detail
from app.domains.procurement.usecases.suppliers.list_suppliers import execute as uc_q_list


router = APIRouter(prefix="/suppliers", tags=["suppliers"])

@router.get("", response_model=SupplierList)
def list_suppliers(
    search: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
    uow: UoW = Depends(get_uow),
    _=Depends(require_access_token),
):
    items, total = uc_q_list(uow, search=search, page=page, page_size=page_size)
    return {"items": items, "total": total, "page": page, "page_size": page_size}

@router.get("/{id_supplier}", response_model=SupplierDetailOut)
def get_supplier_detail(
    id_supplier: int,
    uow: UoW = Depends(get_uow),
    _=Depends(require_access_token),
):
    return uc_q_detail(uow, id_supplier=id_supplier)

@router.post("", response_model=SupplierOut, status_code=status.HTTP_201_CREATED)
def create_supplier(
    payload: SupplierCreate,
    uow: UoW = Depends(get_uow),
    _=Depends(require_access_token),
):
    return uc_create(uow, data=payload)

@router.put("/{id_supplier}", response_model=SupplierDetailOut)
def update_supplier_bundle(
    id_supplier: int = Path(..., ge=1),
    payload: SupplierBundleUpdate = ...,
    uow: UoW = Depends(get_uow),
    _=Depends(require_access_token),
):
    return uc_update(uow, id_supplier=id_supplier, payload=payload)

@router.delete("/{id_supplier}", status_code=status.HTTP_204_NO_CONTENT)
def delete_supplier_endpoint(
    id_supplier: int,
    uow: UoW = Depends(get_uow),
    _=Depends(require_access_token),
):
    uc_delete(uow, id_supplier=id_supplier)
