# app/models/enums.py
# This module defines enumerated types for feed kinds, feed formats, and run statuses

from sqlalchemy import Enum as SQLEnum

FEED_KIND = SQLEnum("http_csv", "http_json", "api", "sftp", name="feed_kind")
FEED_FORMAT = SQLEnum("csv", "json", name="feed_format")
RUN_STATUS = SQLEnum("running", "ok", "error", "partial", name="run_status", create_type=False)
