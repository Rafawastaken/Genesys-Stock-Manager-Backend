# app/core/middleware.py
import time, uuid
import logging
from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.logging import set_request_id
from app.core.errors import AppError  # << novo

log = logging.getLogger("gsm.http")


class RequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        rid = request.headers.get("X-Request-ID") or uuid.uuid4().hex[:12]
        set_request_id(rid)
        t0 = time.perf_counter()

        try:
            log.info(">> %s %s", request.method, request.url.path)
            try:
                # fluxo normal
                response = await call_next(request)
            except AppError as e:
                # erros de domínio → resposta JSON padronizada
                dt = (time.perf_counter() - t0) * 1000
                payload = {"code": e.code, "detail": e.detail}
                response = JSONResponse(status_code=e.http_status, content=payload)
                response.headers["X-Request-ID"] = rid
                log.warning("<< %s %s -> %s (%s) in %.1fms",
                            request.method, request.url.path, e.http_status, e.code, dt)
                return response

            # sucesso → log e header
            dt = (time.perf_counter() - t0) * 1000
            response.headers["X-Request-ID"] = rid
            log.info("<< %s %s -> %s in %.1fms",
                     request.method, request.url.path, response.status_code, dt)
            return response

        finally:
            # limpar contexto (evita bleed entre requests)
            set_request_id(None)
