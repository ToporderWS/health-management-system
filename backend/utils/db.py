# -*- coding: utf-8 -*-
"""数据库访问层：统一 PyMySQL 连接管理，全部使用参数化查询（防 SQL 注入）。"""
import logging
from contextlib import contextmanager

import pymysql
from pymysql.cursors import DictCursor

from config import Config

logger = logging.getLogger(__name__)


def get_connection():
    """创建一条新的数据库连接（字典游标，utf8mb4）。"""
    return pymysql.connect(
        host=Config.DB_HOST,
        port=Config.DB_PORT,
        user=Config.DB_USER,
        password=Config.DB_PASSWORD,
        database=Config.DB_NAME,
        charset=Config.DB_CHARSET,
        cursorclass=DictCursor,
        autocommit=False,
    )


@contextmanager
def db_cursor(commit=False):
    """
    数据库游标上下文管理器。
    commit=True 时正常退出自动提交，异常自动回滚。
    用法：
        with db_cursor(commit=True) as cur:
            cur.execute("INSERT INTO ...", (a, b))
    """
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            yield cur
        if commit:
            conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


# ------------------------- 常用封装 -------------------------

def query_all(sql, args=None):
    """查询多行，返回 list[dict]。"""
    with db_cursor() as cur:
        cur.execute(sql, args or ())
        return cur.fetchall()


def query_one(sql, args=None):
    """查询单行，返回 dict 或 None。"""
    with db_cursor() as cur:
        cur.execute(sql, args or ())
        return cur.fetchone()


def query_scalar(sql, args=None, default=0):
    """查询单个值（如 COUNT/SUM），无结果返回 default。"""
    row = query_one(sql, args)
    if not row:
        return default
    value = list(row.values())[0]
    return default if value is None else value


def execute(sql, args=None):
    """执行写操作（INSERT/UPDATE/DELETE），返回影响行数。"""
    with db_cursor(commit=True) as cur:
        return cur.execute(sql, args or ())


def insert(sql, args=None):
    """执行插入并返回自增主键。"""
    with db_cursor(commit=True) as cur:
        cur.execute(sql, args or ())
        return cur.lastrowid


def execute_many(sql, seq_of_args):
    """批量执行（如批量插入）。"""
    with db_cursor(commit=True) as cur:
        return cur.executemany(sql, seq_of_args)


def ping():
    """连通性检查，返回 (bool, message)。"""
    try:
        with db_cursor() as cur:
            cur.execute("SELECT 1 AS ok")
            cur.fetchone()
        return True, "数据库连接正常"
    except Exception as exc:  # noqa: BLE001
        return False, "数据库连接失败: %s" % exc
