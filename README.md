
```
Backend
├─ .pre-commit-config.yaml
├─ app
│  ├─ api
│  │  ├─ v1
│  │  │  ├─ auth.py
│  │  │  ├─ brands.py
│  │  │  ├─ categories.py
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
│  │  ├─ errors.py
│  │  ├─ http_errors.py
│  │  ├─ logging.py
│  │  ├─ middleware.py
│  │  ├─ normalize.py
│  │  └─ __init__.py
│  ├─ domains
│  │  ├─ auth
│  │  │  ├─ ports.py
│  │  │  ├─ usecases
│  │  │  │  ├─ login.py
│  │  │  │  └─ __init__.py
│  │  │  └─ __init__.py
│  │  ├─ catalog
│  │  │  ├─ repos.py
│  │  │  ├─ usecases
│  │  │  │  ├─ brands
│  │  │  │  │  ├─ list_brands.py
│  │  │  │  │  └─ __init__.py
│  │  │  │  ├─ categories
│  │  │  │  │  ├─ list_categories.py
│  │  │  │  │  └─ __init__.py
│  │  │  │  ├─ products
│  │  │  │  │  ├─ list_products.py
│  │  │  │  │  └─ __init__.py
│  │  │  │  └─ __init__.py
│  │  │  └─ __init__.py
│  │  ├─ mapping
│  │  │  ├─ engine.py
│  │  │  └─ __init__.py
│  │  ├─ procurement
│  │  │  ├─ repos.py
│  │  │  ├─ usecases
│  │  │  │  ├─ feeds
│  │  │  │  │  ├─ delete_supplier_feed.py
│  │  │  │  │  ├─ get_by_supplier.py
│  │  │  │  │  ├─ test_feed.py
│  │  │  │  │  ├─ upsert_supplier_feed.py
│  │  │  │  │  └─ __init__.py
│  │  │  │  ├─ mappers
│  │  │  │  │  ├─ get_by_supplier.py
│  │  │  │  │  ├─ get_mapper.py
│  │  │  │  │  ├─ put_mapper.py
│  │  │  │  │  ├─ validate_mapper.py
│  │  │  │  │  └─ __init__.py
│  │  │  │  ├─ runs
│  │  │  │  │  ├─ ingest_supplier.py
│  │  │  │  │  └─ __init__.py
│  │  │  │  ├─ suppliers
│  │  │  │  │  ├─ create_supplier.py
│  │  │  │  │  ├─ delete_supplier.py
│  │  │  │  │  ├─ get_supplier_detail.py
│  │  │  │  │  ├─ list_suppliers.py
│  │  │  │  │  ├─ update_bundle.py
│  │  │  │  │  └─ __init__.py
│  │  │  │  └─ __init__.py
│  │  │  └─ __init__.py
│  │  └─ __init__.py
│  ├─ external
│  │  ├─ feed_downloader.py
│  │  ├─ prestashop_auth_provider.py
│  │  ├─ prestashop_client.py
│  │  └─ __init__.py
│  ├─ infra
│  │  ├─ base.py
│  │  ├─ bootstrap.py
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
│  │  ├─ brands.py
│  │  ├─ categories.py
│  │  ├─ feeds.py
│  │  ├─ mappers.py
│  │  ├─ products.py
│  │  ├─ suppliers.py
│  │  ├─ system.py
│  │  └─ __init__.py
│  ├─ shared
│  │  ├─ jwt.py
│  │  └─ __init__.py
│  └─ __init__.py
├─ app.zip
├─ apps
│  ├─ api_main.py
│  └─ __init__.py
├─ BUGS.md
├─ Makefile
├─ NOTES.md
├─ pyproject.toml
├─ README.md
├─ requirements.txt
└─ TODO.md

```
