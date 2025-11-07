from pydantic import BaseModel


class BrandIn(BaseModel):
    name: str


class BrandOut(BaseModel):
    id: int
    name: str


class BrandListOut(BaseModel):
    items: list[BrandOut]
    total: int
    page: int
    page_size: int
