```
Backend
├─ app
│  ├─ api
│  │  ├─ v1
│  │  │  ├─ auth.py
│  │  │  ├─ feeds.py
│  │  │  ├─ mappers.py
│  │  │  ├─ products.py
│  │  │  ├─ runs.py
│  │  │  ├─ suppliers.py
│  │  │  ├─ system.py
│  │  │  └─ __init__.py
│  │  └─ __init__.py
│  ├─ core
│  │  ├─ config.py
│  │  ├─ deps.py
│  │  ├─ logging.py
│  │  ├─ middleware.py
│  │  ├─ normalize.py
│  │  └─ __init__.py
│  ├─ domain
│  │  ├─ ingest_engine.py
│  │  └─ __init__.py
│  ├─ external
│  │  ├─ feed_downloader.py
│  │  ├─ prestashop_client.py
│  │  └─ __init__.py
│  ├─ infra
│  │  ├─ base.py
│  │  ├─ session.py
│  │  ├─ uow.py
│  │  └─ __init__.py
│  ├─ models
│  │  ├─ brand.py
│  │  ├─ category.py
│  │  ├─ enums.py
│  │  ├─ feed_mapper.py
│  │  ├─ feed_run.py
│  │  ├─ product.py
│  │  ├─ product_meta.py
│  │  ├─ product_supplier_event.py
│  │  ├─ supplier.py
│  │  ├─ supplier_feed.py
│  │  ├─ supplier_item.py
│  │  └─ __init__.py
│  ├─ repositories
│  │  ├─ base.py
│  │  ├─ brand_repo.py
│  │  ├─ category_repo.py
│  │  ├─ feed_run_repo.py
│  │  ├─ mapper_repo.py
│  │  ├─ product_event_repo.py
│  │  ├─ product_repo.py
│  │  ├─ supplier_feed_repo.py
│  │  ├─ supplier_item_repo.py
│  │  ├─ supplier_repo.py
│  │  └─ __init__.py
│  ├─ schemas
│  │  ├─ auth.py
│  │  ├─ feeds.py
│  │  ├─ mappers.py
│  │  ├─ products.py
│  │  ├─ suppliers.py
│  │  ├─ system.py
│  │  └─ __init__.py
│  ├─ services
│  │  ├─ commands
│  │  │  ├─ auth
│  │  │  │  └─ login.py
│  │  │  ├─ feeds
│  │  │  │  ├─ delete_supplier_feed.py
│  │  │  │  ├─ test_feed.py
│  │  │  │  └─ upsert_supplier_feed.py
│  │  │  ├─ mappers
│  │  │  │  ├─ put_mapper.py
│  │  │  │  └─ validate_mapper.py
│  │  │  ├─ runs
│  │  │  │  └─ ingest_supplier.py
│  │  │  ├─ suppliers
│  │  │  │  ├─ create_supplier.py
│  │  │  │  ├─ delete_supplier.py
│  │  │  │  └─ update_supplier.py
│  │  │  └─ __init__.py
│  │  ├─ queries
│  │  │  ├─ feeds
│  │  │  │  └─ get_by_supplier.py
│  │  │  ├─ mappers
│  │  │  │  ├─ get_by_supplier.py
│  │  │  │  └─ get_mapper.py
│  │  │  ├─ products
│  │  │  │  ├─ list_products.py
│  │  │  │  └─ __init__.py
│  │  │  ├─ suppliers
│  │  │  │  ├─ get_supplier_detail.py
│  │  │  │  └─ list_suppliers.py
│  │  │  └─ __init__.py
│  │  └─ __init__.py
│  ├─ shared
│  │  ├─ jwt.py
│  │  └─ __init__.py
│  └─ __init__.py
├─ apps
│  ├─ api_main.py
│  └─ __init__.py
├─ Makefile
├─ NOTES.md
├─ README.md
├─ requirements.txt
└─ TODO.md

```
