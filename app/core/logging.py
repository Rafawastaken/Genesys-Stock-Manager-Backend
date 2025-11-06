import logging
import os
import re
import sys
from datetime import datetime, timedelta
from logging.handlers import TimedRotatingFileHandler
from typing import Optional
from contextvars import ContextVar

# -------- request-id (mantido) ----------
_request_id_ctx: ContextVar[Optional[str]] = ContextVar("request_id", default=None)

try:
    from dotenv import load_dotenv
    load_dotenv()  # não usa override=True para não pisar variáveis já exportadas
except Exception:
    pass


class RequestIdFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        rid = _request_id_ctx.get()
        record.request_id = rid or "-"
        return True

def get_request_id() -> Optional[str]:
    """Devolve o request id atual (ou None se não houver)."""
    return _request_id_ctx.get()

def get_request_id_or(default: str = "-") -> str:
    rid = _request_id_ctx.get()
    return rid if rid else default


def set_request_id(rid: Optional[str]) -> None:
    _request_id_ctx.set(rid)


# -------- helpers ----------
_DATE_SUFFIX = "%Y-%m-%d"
_LOG_RE = re.compile(r"^(?P<base>.+)\.log\.(?P<date>\d{4}-\d{2}-\d{2})$")


def _purge_old_logs(log_dir: str, base_name: str, days: int = 30) -> int:
    """Apaga ficheiros 'base.log.YYYY-MM-DD' com mais de N dias."""
    cutoff = (datetime.now() - timedelta(days=days)).date()
    removed = 0
    for fname in os.listdir(log_dir):
        m = _LOG_RE.match(fname)
        if not m:
            continue
        if not m.group("base").endswith(base_name):
            continue
        try:
            dt = datetime.strptime(m.group("date"), _DATE_SUFFIX).date()
        except ValueError:
            continue
        if dt < cutoff:
            try:
                os.remove(os.path.join(log_dir, fname))
                removed += 1
            except OSError:
                pass
    return removed


# -------- setup ----------
def setup_logging() -> None:
    level = os.getenv("LOG_LEVEL", "INFO").upper()
    log_dir = os.getenv("LOG_DIR", os.path.join(os.getcwd(), "logs"))
    base_name = os.getenv("LOG_BASENAME", "gsm")  # ficheiro principal: gsm.log
    retention_days = int(os.getenv("LOG_RETENTION_DAYS", "30"))

    os.makedirs(log_dir, exist_ok=True)
    logfile = os.path.join(log_dir, f"{base_name}.log")

    fmt = "%(asctime)s %(levelname)s %(name)s [rid=%(request_id)s] :: %(message)s"
    formatter = logging.Formatter(fmt)

    # Console
    console = logging.StreamHandler(sys.stdout)
    console.setFormatter(formatter)
    console.addFilter(RequestIdFilter())

    # Ficheiro diário (rotação à meia-noite local)
    fileh = TimedRotatingFileHandler(
        filename=logfile,
        when="midnight",  # rotação diária
        backupCount=30,  # salvaguarda adicional por contagem
        encoding="utf-8",
        delay=True,  # só abre o ficheiro no 1º write
        utc=False,  # usa hora local
    )
    # Nome do ficheiro rodado: gsm.log.2025-09-12
    fileh.suffix = _DATE_SUFFIX
    fileh.setFormatter(formatter)
    fileh.addFilter(RequestIdFilter())

    # Root logger
    root = logging.getLogger()
    root.setLevel(level)
    root.handlers.clear()
    root.addHandler(console)
    root.addHandler(fileh)

    # Bibliotecas ruidosas
    logging.getLogger("httpx").setLevel(os.getenv("HTTPX_LOG_LEVEL", "INFO").upper())
    logging.getLogger("apscheduler").setLevel(os.getenv("APSCHED_LOG_LEVEL", "INFO").upper())

    # Purga por idade (garante “últimos 30 dias” mesmo que falte alguma rotação)
    removed = _purge_old_logs(log_dir, base_name, days=retention_days)
    if removed:
        logging.getLogger("gsm.logging").info("purged %d old log file(s)", removed)
