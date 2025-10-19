# app/core/normalize.py
# Funções utilitárias para normalização de dados comuns em e-commerce:
# app/core/normalize.py
from __future__ import annotations
import re, html, json
from decimal import Decimal, InvalidOperation
from typing import Any, Iterable, Optional, List

_WS_RE = re.compile(r"\s+")
_TAG_RE = re.compile(r"<[^>]+>")

def as_str(x: Any) -> Optional[str]:
    if x is None: return None
    if isinstance(x, (bytes, bytearray)):
        try: return x.decode("utf-8", errors="ignore")
        except Exception: return str(x)
    return str(x)

def clean_text(x: Any) -> Optional[str]:
    s = as_str(x)
    if s is None: return None
    s = s.replace("\xa0", " ")
    s = html.unescape(s).strip()
    s = _WS_RE.sub(" ", s)
    return s or None

def strip_html(x: Any) -> Optional[str]:
    s = clean_text(x)
    if not s: return s
    return _TAG_RE.sub("", s).strip() or None

def _normalize_decimal_string(txt: str) -> str:
    s = txt.lower().strip()
    for sym in ("€","eur","euro","eur.","€.","usd","$"):
        s = s.replace(sym, "")
    s = s.replace(" ", "").replace("\t", "")
    if "," in s and "." in s:
        if s.rfind(",") > s.rfind("."):
            s = s.replace(".", "").replace(",", ".")
        else:
            s = s.replace(",", "")
    else:
        s = s.replace(",", ".")
    s = re.sub(r"[^0-9\.-]", "", s).replace("--", "-")
    return s

def to_decimal(x: Any) -> Optional[Decimal]:
    if x is None or x == "": return None
    s = clean_text(x)
    if not s: return None
    s = _normalize_decimal_string(s)
    if s in {"", ".", "-", "-.", ".-"}: return None
    try: return Decimal(s)
    except InvalidOperation: return None

def to_decimal_str(x: Any, places: Optional[int] = None) -> Optional[str]:
    d = to_decimal(x)
    if d is None: return None
    if places is not None:
        q = Decimal(1).scaleb(-places)
        try: d = d.quantize(q)
        except Exception: pass
    return format(d, "f")

def to_int(x: Any) -> Optional[int]:
    if x is None or x == "": return None
    if isinstance(x, int): return x
    if isinstance(x, float):
        try:
            from decimal import Decimal as D
            d = D(str(x))
            return int(d) if d == d.to_integral_value() else None
        except Exception:
            return int(x)
    d = to_decimal(x)
    if d is None: return None
    return int(d) if d == d.to_integral_value() else None

def to_bool(x: Any) -> Optional[bool]:
    if x is None: return None
    if isinstance(x, bool): return x
    s = (clean_text(x) or "").lower()
    if not s: return None
    if s in {"1","true","yes","sim","y","on"}: return True
    if s in {"0","false","no","nao","não","n","off"}: return False
    return None

# imagens
_SEP_RE = re.compile(r"[,\|\s]+")
def _coerce_list(val: Any) -> List[str]:
    if val is None: return []
    if isinstance(val, (list, tuple)): return [str(x) for x in val if x is not None]
    if isinstance(val, str):
        s = val.strip()
        if not s: return []
        if s.startswith("[") and s.endswith("]"):
            try:
                arr = json.loads(s)
                if isinstance(arr, list): return [str(x) for x in arr if x is not None]
            except Exception:
                pass
        return [p for p in _SEP_RE.split(s) if p]
    return [str(val)]

def _unique_preserve_order(items: Iterable[str]) -> List[str]:
    seen, out = set(), []
    for u in items:
        if u not in seen: seen.add(u); out.append(u)
    return out

def normalize_images(mapped: dict[str, Any]) -> dict[str, Any]:
    """
    Aceita 'image_urls'/'images'/'image_url' (string, lista, csv) e normaliza:
      - image_urls: lista única preservando ordem
      - image_url:  primeira da lista ou None
    """
    def _coerce_list(val: Any) -> List[str]:
        if val is None: return []
        if isinstance(val, (list, tuple)):
            return [str(x) for x in val if x is not None]
        if isinstance(val, str):
            s = val.strip()
            if not s: return []
            # tenta json list
            if s.startswith("[") and s.endswith("]"):
                try:
                    arr = json.loads(s)
                    if isinstance(arr, list):
                        return [str(x) for x in arr if x is not None]
                except Exception:
                    pass
            # split por , ; | espaços
            import re
            parts = re.split(r"[,\|\s]+", s)
            return [p for p in parts if p]
        return [str(val)]

    def _unique_preserve_order(items: List[str]) -> List[str]:
        seen, out = set(), []
        for u in items:
            if u not in seen:
                seen.add(u); out.append(u)
        return out

    out = dict(mapped)
    raw = out.get("image_urls") or out.get("images") or out.get("image_url")
    urls = _unique_preserve_order(_coerce_list(raw))
    out["image_urls"] = urls or None
    out["image_url"] = urls[0] if urls else None
    return out

def coerce_mapped_for_preview(m: dict) -> dict:
    out = dict(m)
    if "gtin"  in out: out["gtin"]  = clean_text(out.get("gtin"))
    if "price" in out: out["price"] = to_decimal_str(out.get("price"))
    if "stock" in out:
        i = to_int(out.get("stock"))
        out["stock"] = i if i is not None else out.get("stock")
    for k in ("name","partnumber","brand","category","image_url","description","weight"):
        if k in out:
            out[k] = to_decimal_str(out.get(k)) if k == "weight" else clean_text(out.get(k))
    return out
