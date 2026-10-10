# -*- coding: utf-8 -*-
"""追加本轮「管理员审核链路澄清」到工作记忆，并校验关键串各命中 1 次。"""
import io
import os

P = r'C:\Users\Toporder-WS\Desktop\项目\个人健康管理系统小程序\.workbuddy\memory\2026-10-01.md'

BLOCK = """
## 管理员审核链路澄清（医生 / 教练账号审核）

- 用户问「医生管理页怎么审核通过 / 拒绝」——根因结论：**审核入口不在「03 医生管理」(views/admin/Doctors.vue)，而在独立的「05 账号审核中心」(/admin/audit，views/admin/Audit.vue)**。Doctors.vue 操作列只有 详情 / 编辑 / 重置密码，本身不含审核。
- 审核链路：Audit.vue 三个 Tab（医生审核 / 健身教练审核 / 审核记录）→ 操作列「通过 / 拒绝」→ ElMessageBox 二次确认 → POST /api/admin/{doctor|coach}/audit {id, audit_status:1|2} → services/admin_service.py 的 doctor_audit / coach_audit。「查看」抽屉底部另有同效的「审核通过 / 审核拒绝」。
- 关键约束：① 前端「通过 / 拒绝」按钮 :disabled = (row.audit_status !== 0)，只有「待审核」可点；② 后端再拦一次，非 0 时返回 HTTP 400「该申请已完成审核，无需重复操作」；③ 故审核**单向不可逆**（仅 0→1 或 0→2），误拒后只能删号重注册或直接改库。
- 登录侧判定（services/doctor_service.py · coach_service.py 的 login）：0 → MSG_AUDIT_PENDING「账号正在审核中，请耐心等待」；2 → MSG_AUDIT_REJECTED「账号审核未通过，请联系管理员」；1 → 签发 Token；其它 → 「账号状态异常，请联系管理员」。注册强制 audit_status=0，忽略客户端传值。管理员账号(admin_user)无 audit_status，不需审核。
- 实测现状（2026-10-01，API 只读取证）：待审核医生 3 条 —— 001/小黑(id=17)、doc_test_1001125429/接口测试医生(id=4)、doctor003/王海涛(id=3)；待审核教练 1 条 —— coach003/赵强(id=3)。今日已审核 20，累计申请 28。
- 新增只读取证脚本 management-web/_shot_audit.py：API 登录取 token → 注入 localStorage(hms_admin_token / hms_admin_info) → 打开 /admin/audit 截图 → 点开「通过」二次确认框截图后**只点右上角 × 关闭、绝不提交**，并复核 /api/admin/audit/overview 前后一致（实测 pending_doctor=3 / pending_coach=1 未变，零副作用）。
- 顺带发现（未修，待用户裁定）：审核中心的「医生账号」列 width=130px 放不下 18 字符账号（如 doc_test_1001125429），会折成两行显示。属该页自身问题，超出「只改三个登录页」的范围。
"""

CHECK = [
    '05 账号审核中心',
    'row.audit_status !== 0',
    '该申请已完成审核，无需重复操作',
    'MSG_AUDIT_REJECTED',
    'coach003/赵强(id=3)',
    '_shot_audit.py',
    'doc_test_1001125429',
]

os.makedirs(os.path.dirname(P), exist_ok=True)
old = ''
if os.path.exists(P):
    old = io.open(P, 'rb').read().decode('utf-8')
if '管理员审核链路澄清' in old:
    print('SKIP 已存在该章节，未重复追加')
else:
    with io.open(P, 'a', encoding='utf-8', newline='') as f:
        f.write(BLOCK)

new = io.open(P, 'rb').read().decode('utf-8')
print('bytes %d -> %d' % (len(old.encode('utf-8')), len(new.encode('utf-8'))))
for c in CHECK:
    print('  hit=%-3d %s' % (new.count(c), c))
