# -*- coding: utf-8 -*-
"""健康科普路由（无需登录，只返回 is_show=1 的文章）。"""
from flask import Blueprint

from services import content_service
from utils.helpers import get_arg, get_page, page_result, to_int
from utils.response import param_error, success

article_bp = Blueprint("article", __name__, url_prefix="/api/article")


@article_bp.get("/list")
def article_list():
    page, size, _ = get_page()
    total, rows = content_service.list_article(
        page=page, page_size=size, keyword=get_arg("keyword"), admin=False)
    return success(page_result(rows, total, page, size), "操作成功")


@article_bp.get("/detail")
def article_detail():
    article_id = to_int(get_arg("id"))
    if not article_id:
        return param_error("缺少文章 id")
    row = content_service.article_detail(article_id, admin=False)
    if not row:
        return param_error("文章不存在或已下架")
    return success(row, "操作成功")
