# -*- coding: utf-8 -*-
"""系统公告路由（无需登录，只返回 is_show=1 的公告）。"""
from flask import Blueprint

from services import content_service
from utils.helpers import get_arg, get_page, page_result, to_int
from utils.response import param_error, success

notice_bp = Blueprint("notice", __name__, url_prefix="/api/notice")


@notice_bp.get("/list")
def notice_list():
    page, size, _ = get_page(default_size=20)
    total, rows = content_service.list_notice(
        page=page, page_size=size, keyword=get_arg("keyword"), admin=False)
    return success(page_result(rows, total, page, size), "操作成功")


@notice_bp.get("/detail")
def notice_detail():
    notice_id = to_int(get_arg("id"))
    if not notice_id:
        return param_error("缺少公告 id")
    row = content_service.notice_detail(notice_id, admin=False)
    if not row:
        return param_error("公告不存在或已下架")
    return success(row, "操作成功")
