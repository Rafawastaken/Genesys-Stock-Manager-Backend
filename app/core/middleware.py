import time, uuid
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.logging import set_request_id
import logging

log = logging.getLogger("gsm.http")


class RequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        rid = request.headers.get("X-Request-ID") or uuid.uuid4().hex[:12]
        set_request_id(rid)
        t0 = time.perf_counter()
        try:
            log.info(">> %s %s", request.method, request.url.path)
            response = await call_next(request)
            dt = (time.perf_counter() - t0) * 1000
            response.headers["X-Request-ID"] = rid
            log.info("<< %s %s -> %s in %.1fms", request.method, request.url.path, response.status_code, dt)
            return response
        finally:
            # limpar contexto por segurança (em servers async reutilizam tasks)
            set_request_id(None)
