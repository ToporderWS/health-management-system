# -*- coding: utf-8 -*-
"""管理员操作日志写入。

禁止写入：明文密码 / 密码哈希 / Token / JWT Secret / 数据库密码。
写入前统一经过 mask_sensitive 脱敏。
"""
import logging

from utils import db
from utils.helpers import mask_sensitive

logger = logging.getLogger(__name__)


def write_admin_log(admin_id, operation_type, operation_content,
                    target_type=None, target_id=None):
    """
    写入管理员操作日志；日志写入失败不得影响主业务，仅记录警告。

    :param admin_id: 管理员 ID
    :param operation_type: 操作类型，如 '医生审核通过'
    :param operation_content: 操作内容（自动脱敏 + 截断 500 字符）
    :param target_type: 目标类型，如 'doctor'
    :param target_id: 目标 ID
    """
    try:
        db.execute(
            """INSERT INTO admin_operation_log
               (admin_id, operation_type, operation_content, target_type, target_id, created_at)
               VALUES (%s, %s, %s, %s, %s, NOW())""",
            (
                int(admin_id),
                str(operation_type)[:50],
                mask_sensitive(operation_content, 500),
                (str(target_type)[:50] if target_type else None),
                (int(target_id) if target_id not in (None, "") else None),
            ),
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning("写管理员操作日志失败: %s", exc)
