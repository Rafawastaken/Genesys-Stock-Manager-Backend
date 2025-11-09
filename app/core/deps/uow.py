from typing import Annotated
from fastapi import Depends
from sqlalchemy.orm import Session
from app.infra.session import get_session
from app.infra.uow import UoW


def get_uow(db: Annotated[Session, Depends(get_session)]) -> UoW:
    return UoW(db)
