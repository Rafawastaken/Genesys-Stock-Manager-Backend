from __future__ import annotations
from fastapi import status

class AppError(Exception):
    code: str = "APP_ERROR"
    http_status: int = status.HTTP_400_BAD_REQUEST

    def __init__(self, detail: str | None = None, *, code: str | None = None, http_status: int | None = None):
        super().__init__(detail or self.code)
        if code is not None:
            self.code = code
        if http_status is not None:
            self.http_status = http_status

    @property
    def detail(self) -> str:
        # str(self) contém o detalhe passado ao __init__
        return str(self)

class NotFound(AppError):
    code = "NOT_FOUND"
    http_status = status.HTTP_404_NOT_FOUND

class Conflict(AppError):
    code = "CONFLICT"
    http_status = status.HTTP_409_CONFLICT

class Unauthorized(AppError):
    code = "UNAUTHORIZED"
    http_status = status.HTTP_401_UNAUTHORIZED

class Forbidden(AppError):
    code = "FORBIDDEN"
    http_status = status.HTTP_403_FORBIDDEN

class BadRequest(AppError):
    code = "BAD_REQUEST"
    http_status = status.HTTP_400_BAD_REQUEST

class InvalidArgument(BadRequest):
    code = "INVALID_ARGUMENT"
