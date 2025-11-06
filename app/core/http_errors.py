# app/core/http_errors.py
from __future__ import annotations
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError

from app.core.errors import NotFound, Conflict, BadRequest

def _payload(status: int, code: str, message: str, details=None):
    body = {"error": code, "message": message}
    if details is not None:
        body["details"] = details
    return JSONResponse(status_code=status, content=body)

def init_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(NotFound)
    async def _not_found(_: Request, exc: NotFound):
        return _payload(404, "not_found", str(exc) or "Resource not found")

    @app.exception_handler(Conflict)
    async def _conflict(_: Request, exc: Conflict):
        return _payload(409, "conflict", str(exc) or "Resource conflict")

    @app.exception_handler(BadRequest)
    async def _bad_request(_: Request, exc: BadRequest):
        return _payload(400, "bad_request", str(exc) or "Bad request")

    # Guard-rail útil: mapear IntegrityError → 409 por omissão
    @app.exception_handler(IntegrityError)
    async def _integrity(_: Request, exc: IntegrityError):
        return _payload(409, "integrity_error", "Unique constraint violated")
