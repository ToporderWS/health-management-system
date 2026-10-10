# -*- coding: utf-8 -*-
"""路由包：按角色/业务拆分 Blueprint。"""
from routes.admin import admin_bp
from routes.article import article_bp
from routes.coach import coach_bp
from routes.doctor import doctor_bp
from routes.health import health_bp
from routes.notice import notice_bp
from routes.user import user_bp


def register_blueprints(app):
    """集中注册全部 Blueprint。"""
    app.register_blueprint(user_bp)
    app.register_blueprint(health_bp)
    app.register_blueprint(article_bp)
    app.register_blueprint(notice_bp)
    app.register_blueprint(doctor_bp)
    app.register_blueprint(coach_bp)
    app.register_blueprint(admin_bp)
