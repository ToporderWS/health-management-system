# -*- coding: utf-8 -*-
"""内容运营：健康科普文章 / 系统公告。"""
import datetime

from utils import db
from utils.helpers import fmt_datetime, to_int, to_str

# =========================== 健康科普 ===========================


def list_article(page=1, page_size=10, keyword=None, is_show=None, admin=False):
    """
    文章列表。
    :param admin: True 时返回全部（含隐藏）；False 时仅返回 is_show=1（小程序端）
    """
    where, args = [], []
    if not admin:
        where.append("a.is_show=1")
    elif is_show not in (None, ""):
        where.append("a.is_show=%s")
        args.append(to_int(is_show))
    if keyword:
        where.append("(a.title LIKE %s OR a.author LIKE %s)")
        like = "%" + keyword + "%"
        args.extend([like, like])
    cond = (" WHERE " + " AND ".join(where)) if where else ""

    total = db.query_scalar("SELECT COUNT(*) AS c FROM health_article a" + cond, tuple(args))
    rows = db.query_all(
        "SELECT a.* FROM health_article a" + cond +
        " ORDER BY a.publish_time DESC, a.id DESC LIMIT %s OFFSET %s",
        tuple(args) + (page_size, (page - 1) * page_size),
    )
    for r in rows:
        r["publish_time"] = fmt_datetime(r["publish_time"])
        r["created_at"] = fmt_datetime(r["created_at"])
    return total, rows


def article_detail(article_id, admin=False):
    if admin:
        row = db.query_one("SELECT * FROM health_article WHERE id=%s", (article_id,))
    else:
        row = db.query_one(
            "SELECT * FROM health_article WHERE id=%s AND is_show=1", (article_id,)
        )
    if not row:
        return None
    row["publish_time"] = fmt_datetime(row["publish_time"])
    row["created_at"] = fmt_datetime(row["created_at"])
    return row


def save_article(data):
    """新增或编辑文章。data 含 id 时为编辑。"""
    article_id = to_int(data.get("id"))
    title = to_str(data.get("title"))
    cover = to_str(data.get("cover_img"))
    content = to_str(data.get("content"))
    author = to_str(data.get("author")) or "健康编辑部"
    is_show = to_int(data.get("is_show"), 1)
    publish_time = data.get("publish_time")
    from utils.helpers import parse_datetime
    publish_time = parse_datetime(publish_time) if publish_time else datetime.datetime.now()

    if not title:
        return False, "文章标题不能为空", None
    if len(title) > 200:
        return False, "文章标题不能超过 200 字", None
    if not content:
        return False, "文章正文不能为空", None
    if is_show not in (0, 1):
        return False, "显示状态取值不合法", None

    if article_id:
        exists = db.query_one("SELECT id FROM health_article WHERE id=%s", (article_id,))
        if not exists:
            return False, "文章不存在", None
        db.execute(
            """UPDATE health_article
               SET title=%s, cover_img=%s, content=%s, author=%s, is_show=%s, publish_time=%s
               WHERE id=%s""",
            (title, cover, content, author, is_show, publish_time, article_id),
        )
        return True, "文章更新成功", {"id": article_id}

    new_id = db.insert(
        """INSERT INTO health_article
           (title, cover_img, content, author, is_show, publish_time, created_at)
           VALUES (%s, %s, %s, %s, %s, %s, NOW())""",
        (title, cover, content, author, is_show, publish_time),
    )
    return True, "文章新增成功", {"id": new_id}


def delete_article(article_id):
    exists = db.query_one("SELECT id, title FROM health_article WHERE id=%s", (article_id,))
    if not exists:
        return False, "文章不存在", None
    db.execute("DELETE FROM health_article WHERE id=%s", (article_id,))
    return True, "文章删除成功", {"title": exists["title"]}


# =========================== 系统公告 ===========================


def list_notice(page=1, page_size=10, keyword=None, is_show=None, admin=False):
    where, args = [], []
    if not admin:
        where.append("is_show=1")
    elif is_show not in (None, ""):
        where.append("is_show=%s")
        args.append(to_int(is_show))
    if keyword:
        where.append("(title LIKE %s OR content LIKE %s)")
        like = "%" + keyword + "%"
        args.extend([like, like])
    cond = (" WHERE " + " AND ".join(where)) if where else ""

    total = db.query_scalar("SELECT COUNT(*) AS c FROM notice" + cond, tuple(args))
    rows = db.query_all(
        "SELECT * FROM notice" + cond +
        " ORDER BY publish_time DESC, id DESC LIMIT %s OFFSET %s",
        tuple(args) + (page_size, (page - 1) * page_size),
    )
    for r in rows:
        r["publish_time"] = fmt_datetime(r["publish_time"])
        r["created_at"] = fmt_datetime(r["created_at"])
    return total, rows


def notice_detail(notice_id, admin=False):
    if admin:
        row = db.query_one("SELECT * FROM notice WHERE id=%s", (notice_id,))
    else:
        row = db.query_one("SELECT * FROM notice WHERE id=%s AND is_show=1", (notice_id,))
    if not row:
        return None
    row["publish_time"] = fmt_datetime(row["publish_time"])
    row["created_at"] = fmt_datetime(row["created_at"])
    return row


def save_notice(data):
    notice_id = to_int(data.get("id"))
    title = to_str(data.get("title"))
    content = to_str(data.get("content"))
    is_show = to_int(data.get("is_show"), 1)
    publish_time = data.get("publish_time")
    from utils.helpers import parse_datetime
    publish_time = parse_datetime(publish_time) if publish_time else datetime.datetime.now()

    if not title:
        return False, "公告标题不能为空", None
    if len(title) > 200:
        return False, "公告标题不能超过 200 字", None
    if not content:
        return False, "公告内容不能为空", None
    if is_show not in (0, 1):
        return False, "显示状态取值不合法", None

    if notice_id:
        exists = db.query_one("SELECT id FROM notice WHERE id=%s", (notice_id,))
        if not exists:
            return False, "公告不存在", None
        db.execute(
            """UPDATE notice SET title=%s, content=%s, is_show=%s, publish_time=%s
               WHERE id=%s""",
            (title, content, is_show, publish_time, notice_id),
        )
        return True, "公告更新成功", {"id": notice_id}

    new_id = db.insert(
        """INSERT INTO notice (title, content, publish_time, is_show, created_at)
           VALUES (%s, %s, %s, %s, NOW())""",
        (title, content, publish_time, is_show),
    )
    return True, "公告新增成功", {"id": new_id}


def delete_notice(notice_id):
    exists = db.query_one("SELECT id, title FROM notice WHERE id=%s", (notice_id,))
    if not exists:
        return False, "公告不存在", None
    db.execute("DELETE FROM notice WHERE id=%s", (notice_id,))
    return True, "公告删除成功", {"title": exists["title"]}
