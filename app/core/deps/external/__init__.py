"""
Providers registry (public):
- get_uow: cria UoW por request.
- require_access_token: valida JWT.
- get_auth_login: Prestashop auth (callable email,password -> user dict).
- get_feed_preview: Feed preview (async callable FeedTestRequest -> FeedTestResponse).
"""
