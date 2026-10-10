# -*- coding: utf-8 -*-
"""个人健康管理系统 · Flask 统一后端入口。

启动：python app.py
监听：0.0.0.0:8080（固定，禁止 5000 / 5001）
"""
import logging
import os
import sys

from flask import Flask, jsonify, request
from flask_cors import CORS
from werkzeug.exceptions import HTTPException

# 保证任意工作目录下均可 `python app.py` 正常导入
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import Config  # noqa: E402
from routes import register_blueprints  # noqa: E402
from utils import db  # noqa: E402
from utils.upload import ensure_upload_dir  # noqa: E402

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("health-backend")


def create_app():
    app = Flask(__name__, static_folder="static", static_url_path="/static")

    # 中文 JSON 直接输出，不转义为 \uXXXX
    app.json.ensure_ascii = False
    app.config["MAX_CONTENT_LENGTH"] = Config.MAX_CONTENT_LENGTH
    app.config["JSON_SORT_KEYS"] = False

    # 前后端分离：允许所有来源跨域（含 Authorization 头）
    CORS(app, resources={r"/*": {"origins": "*"}},
         supports_credentials=True,
         allow_headers=["Content-Type", "Authorization"],
         expose_headers=["Content-Disposition"])

    ensure_upload_dir()
    register_blueprints(app)
    _register_error_handlers(app)
    _register_common_routes(app)

    logger.info("已注册路由数量: %d", len(list(app.url_map.iter_rules())))
    return app


def _register_common_routes(app):
    @app.get("/")
    def index():
        return jsonify({
            "code": 200,
            "msg": "个人健康管理系统后端服务运行中",
            "data": {
                "system": Config.SYSTEM_NAME,
                "version": Config.SYSTEM_VERSION,
                "api_base": Config.API_BASE_URL,
                "port": Config.PORT,
            },
        }), 200

    @app.get("/api/health")
    def health():
        """健康检查：同时验证数据库连通性。"""
        ok, msg = db.ping()
        return jsonify({
            "code": 200 if ok else 500,
            "msg": msg,
            "data": {
                "service": "ok",
                "database": "ok" if ok else "error",
                "version": Config.SYSTEM_VERSION,
            },
        }), (200 if ok else 500)


def _register_error_handlers(app):
    """全局异常统一返回 {code,msg,data} 契约，避免前端拿到 HTML 错误页。"""

    @app.errorhandler(HTTPException)
    def handle_http_error(exc):
        code = exc.code or 500
        if code == 401:
            body = {"code": 401, "msg": "未登录或登录已失效", "data": {}}
        elif code == 404:
            body = {"code": 400, "msg": "接口不存在：%s" % request.path, "data": {}}
        elif code == 405:
            body = {"code": 400, "msg": "请求方法不被允许：%s" % request.method, "data": {}}
        elif code == 413:
            body = {"code": 400, "msg": "上传文件过大", "data": {}}
        else:
            body = {"code": 500, "msg": exc.description or "服务器异常", "data": {}}
        return jsonify(body), (400 if code in (404, 405, 413) else code)

    @app.errorhandler(Exception)
    def handle_exception(exc):
        logger.exception("未捕获异常: %s", exc)
        return jsonify({"code": 500, "msg": "服务器异常，请稍后重试", "data": {}}), 500


app = create_app()


if __name__ == "__main__":
    ok, msg = db.ping()
    logger.info("数据库自检: %s", msg)
    if not ok:
        logger.warning("数据库不可用，请检查 backend/.env 中 DB_* 配置并确保已导入 database/health_management.sql")

    logger.info("服务启动于 http://%s:%d", Config.HOST, Config.PORT)
    app.run(host=Config.HOST, port=Config.PORT, debug=Config.DEBUG, threaded=True)
