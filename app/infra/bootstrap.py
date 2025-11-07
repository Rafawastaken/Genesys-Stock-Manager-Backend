# app/infra/bootstrap.py
from sqlalchemy.engine import Engine
import logging

log = logging.getLogger("gsm.bootstrap")


def ensure_brand_category_ci(engine: Engine) -> None:
    ddl = [
        "CREATE UNIQUE INDEX IF NOT EXISTS ux_brands_name_ci ON brands (lower(btrim(name)));",
        "CREATE UNIQUE INDEX IF NOT EXISTS ux_categories_name_ci ON categories (lower(btrim(name)));",
    ]
    with engine.begin() as conn:
        for q in ddl:
            try:
                conn.exec_driver_sql(q)
            except Exception as e:
                log.warning("Bootstrap DDL skipped/failed: %s -> %s", q, e)
