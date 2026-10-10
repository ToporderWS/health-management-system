# -*- coding: utf-8 -*-
"""通用工具：分页、参数校验、日期解析、脱敏。"""
import datetime
import re

from flask import request


# ---------------- 分页 ----------------
def get_page(default_size=10, max_size=100):
    """
    读取分页参数（兼容 request.args 与 request.form/json）。
    返回 (page, page_size, offset)
    """
    def _read(name, default):
        value = request.args.get(name)
        if value in (None, ""):
            body = request.get_json(silent=True) or {}
            value = body.get(name)
        try:
            return int(value)
        except (TypeError, ValueError):
            return default

    page = _read("page", 1)
    page_size = _read("page_size", default_size)
    page = max(page, 1)
    page_size = min(max(page_size, 1), max_size)
    return page, page_size, (page - 1) * page_size


def page_result(items, total, page, page_size):
    """构造统一分页返回结构。"""
    return {
        "list": items,
        "total": int(total),
        "page": page,
        "page_size": page_size,
        "pages": (int(total) + page_size - 1) // page_size if page_size else 0,
    }


def get_arg(name, default=None):
    """按 args -> form -> json 顺序读取单个参数。"""
    if name in request.args:
        return request.args.get(name)
    if name in request.form:
        return request.form.get(name)
    body = request.get_json(silent=True)
    if isinstance(body, dict) and name in body:
        return body.get(name)
    return default


def get_json():
    """安全读取 JSON body，非 JSON 时返回 {}。"""
    return request.get_json(silent=True) or {}


def to_int(value, default=None):
    """安全转 int。"""
    try:
        if value in (None, ""):
            return default
        return int(value)
    except (TypeError, ValueError):
        return default


def to_float(value, default=None):
    """安全转 float。"""
    try:
        if value in (None, ""):
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def to_str(value, default=None, strip=True):
    """安全转字符串，空串视为 None。"""
    if value is None:
        return default
    text = str(value)
    if strip:
        text = text.strip()
    return text if text != "" else default


# ---------------- 日期 ----------------
DATE_FMT = "%Y-%m-%d"
DATETIME_FMT = "%Y-%m-%d %H:%M:%S"


def parse_date(value):
    """解析 YYYY-MM-DD，兼容 'YYYY-MM-DD HH:mm:ss' 与 'YYYY/MM/DD'。"""
    if not value:
        return None
    if isinstance(value, (datetime.date, datetime.datetime)):
        return value if isinstance(value, datetime.date) else value.date()
    text = str(value).strip().replace("/", "-")
    text = text.replace("T", " ")[:10]
    try:
        return datetime.datetime.strptime(text, DATE_FMT).date()
    except ValueError:
        return None


def parse_datetime(value):
    """解析 DATETIME，接受 'YYYY-MM-DD' 与 'YYYY-MM-DD HH:mm' / 带秒。"""
    if not value:
        return None
    if isinstance(value, datetime.datetime):
        return value
    if isinstance(value, datetime.date):
        return datetime.datetime.combine(value, datetime.time())
    text = str(value).strip().replace("/", "-").replace("T", " ")
    for fmt in (DATETIME_FMT, "%Y-%m-%d %H:%M", DATE_FMT):
        try:
            return datetime.datetime.strptime(text, fmt)
        except ValueError:
            continue
    return None


def fmt_date(value):
    """输出统一 DATE 格式。"""
    if not value:
        return None
    if isinstance(value, datetime.datetime):
        return value.strftime(DATE_FMT)
    if isinstance(value, datetime.date):
        return value.strftime(DATE_FMT)
    return str(value)[:10]


def fmt_datetime(value):
    """输出统一 DATETIME 格式。"""
    if not value:
        return None
    if isinstance(value, (datetime.datetime, datetime.date)):
        return value.strftime(DATETIME_FMT)
    return str(value)


def now_str():
    return datetime.datetime.now().strftime(DATETIME_FMT)


def days_ago(n):
    """返回 n 天前的日期对象。"""
    return (datetime.date.today() - datetime.timedelta(days=n))


# ---------------- 校验 ----------------
PHONE_RE = re.compile(r"^1[3-9]\d{9}$")


def is_valid_phone(phone):
    """中国大陆手机号简单校验。"""
    return bool(phone and PHONE_RE.match(str(phone)))


# ---------------- 脱敏（写入操作日志前调用） ----------------
_SENSITIVE_KEYS = ("password", "pwd", "passwd", "token", "secret", "jwt", "hash")


def mask_sensitive(text, max_len=500):
    """
    操作日志脱敏：剔除可能携带的密码/Token 片段，并截断到字段长度上限。
    禁止把明文密码、密码哈希、Token、JWT Secret、数据库密码写入日志。
    """
    if text is None:
        return ""
    result = str(text)
    for key in _SENSITIVE_KEYS:
        # 形如 password=xxx / "pwd":"xxx" 的片段统一替换为 ***
        result = re.sub(
            r"(%s\s*[\"']?\s*[:=]\s*[\"']?)([^,;\"'}\s]+)" % key,
            r"\1***",
            result,
            flags=re.IGNORECASE,
        )
    if len(result) > max_len:
        result = result[: max_len - 3] + "..."
    return result
