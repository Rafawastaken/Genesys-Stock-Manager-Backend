# app/infra/bootstrap.py
import logging
from sqlalchemy import text

log = logging.getLogger("gsm.bootstrap")


def ensure_brand_category_ci(engine):
    """
    Garante índices case-insensitive.
    - Cria SEMPRE índices normais (não-unique) para performance.
    - Só cria UNIQUE se não houver duplicados; caso haja, loga e segue.
    - Usa AUTOCOMMIT para não deixar a transaction abortada.
    """
    with engine.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
        # índices normais (seguros)
        conn.exec_driver_sql(
            "CREATE INDEX IF NOT EXISTS ix_brands_name_ci ON brands (lower(btrim(name)));"
        )
        conn.exec_driver_sql(
            "CREATE INDEX IF NOT EXISTS ix_categories_name_ci ON categories (lower(btrim(name)));"
        )

        # helper para verificar duplicados
        def has_dupes(table: str) -> bool:
            sql = f"""
                SELECT 1
                FROM {table}
                GROUP BY lower(btrim(name))
                HAVING COUNT(*) > 1
                LIMIT 1
            """
            return conn.execute(text(sql)).first() is not None

        # tentar UNIQUE só se não houver duplicados
        if not has_dupes("brands"):
            conn.exec_driver_sql(
                "CREATE UNIQUE INDEX IF NOT EXISTS ux_brands_name_ci ON brands (lower(btrim(name)));"
            )
        else:
            log.warning("UNIQUE brands SKIPPED: duplicates exist (clean first).")

        if not has_dupes("categories"):
            conn.exec_driver_sql(
                "CREATE UNIQUE INDEX IF NOT EXISTS ux_categories_name_ci ON categories (lower(btrim(name)));"
            )
        else:
            log.warning("UNIQUE categories SKIPPED: duplicates exist (clean first).")
