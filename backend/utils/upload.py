# -*- coding: utf-8 -*-
"""文件上传工具：校验扩展名，UUID 重命名，只返回文件名。

数据库只保存文件名（如 abc123.jpg），完整访问地址由前端拼接
STATIC_BASE_URL + 文件名，禁止把完整 URL 写库。
"""
import os
import uuid

from werkzeug.utils import secure_filename

from config import Config


def allowed_file(filename):
    """扩展名白名单校验：jpg / jpeg / png / webp。"""
    if not filename or "." not in filename:
        return False
    ext = filename.rsplit(".", 1)[1].lower()
    return ext in Config.ALLOWED_EXT


def ensure_upload_dir():
    """确保上传目录存在，并放置默认头像占位说明。"""
    os.makedirs(Config.UPLOAD_DIR, exist_ok=True)
    return Config.UPLOAD_DIR


def save_upload_file(file_storage):
    """
    保存上传文件到 static/upload/。

    :return: (filename, err_msg)
             filename 形如 '3f2a....jpg'；失败时 filename 为 None
    """
    if file_storage is None:
        return None, "未接收到上传文件"
    raw_name = getattr(file_storage, "filename", "") or ""
    if raw_name.strip() == "":
        return None, "未选择文件"
    if not allowed_file(raw_name):
        return None, "仅支持 jpg / jpeg / png / webp 格式图片"

    ext = raw_name.rsplit(".", 1)[1].lower()
    # secure_filename 兜底，最终文件名 = UUID + 原始扩展名
    if secure_filename(raw_name) == "" and raw_name.strip(".") == "":
        return None, "文件名非法"

    filename = "%s.%s" % (uuid.uuid4().hex, ext)
    ensure_upload_dir()
    save_path = os.path.join(Config.UPLOAD_DIR, filename)
    file_storage.save(save_path)

    if not os.path.exists(save_path) or os.path.getsize(save_path) == 0:
        return None, "文件保存失败"

    return filename, None


def build_static_url(filename):
    """由文件名拼出完整访问地址（仅用于接口返回，禁止写库）。"""
    if not filename:
        return ""
    if str(filename).startswith("http://") or str(filename).startswith("https://"):
        return filename
    return Config.STATIC_BASE_URL + filename
