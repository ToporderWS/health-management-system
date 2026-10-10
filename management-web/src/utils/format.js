/** 格式化与状态映射工具（前后端统一 YYYY-MM-DD / YYYY-MM-DD HH:mm:ss） */

export function formatDate(value) {
  if (!value) return '-'
  return String(value).slice(0, 10)
}

export function formatDateTime(value) {
  if (!value) return '-'
  return String(value).slice(0, 19)
}

/** 睡眠时长（分钟 -> 小时分钟） */
export function formatDuration(minutes) {
  const m = Number(minutes || 0)
  if (!m) return '0 分钟'
  const h = Math.floor(m / 60)
  const rest = m % 60
  if (!h) return `${rest} 分钟`
  return rest ? `${h} 小时 ${rest} 分钟` : `${h} 小时`
}

export const AUDIT_STATUS = {
  0: { text: '待审核', type: 'warning' },
  1: { text: '审核通过', type: 'success' },
  2: { text: '审核拒绝', type: 'danger' },
}

/** 健康计划：0进行中 1已完成 2已放弃 */
export const HEALTH_PLAN_STATUS = {
  0: { text: '进行中', type: 'primary' },
  1: { text: '已完成', type: 'success' },
  2: { text: '已放弃', type: 'info' },
}

/** 运动目标 / 训练计划：0进行中 1已完成 2已结束 */
export const SPORT_STATUS = {
  0: { text: '进行中', type: 'primary' },
  1: { text: '已完成', type: 'success' },
  2: { text: '已结束', type: 'info' },
}

export function auditText(v) {
  return (AUDIT_STATUS[Number(v)] || {}).text || '未知'
}

export function auditType(v) {
  return (AUDIT_STATUS[Number(v)] || {}).type || 'info'
}

export function genderText(v) {
  return v || '-'
}

/** 健康指标是否超出常见参考范围（仅用于列表标注提醒，不做诊断） */
export function isAbnormal(row) {
  if (!row) return false
  const high = Number(row.blood_pressure_high || 0)
  const low = Number(row.blood_pressure_low || 0)
  const heart = Number(row.heart_rate || 0)
  const sugar = Number(row.blood_sugar || 0)
  return (
    (high && high >= 140) ||
    (low && low >= 90) ||
    (heart && (heart > 100 || heart < 60)) ||
    (sugar && (sugar >= 6.1 || sugar < 3.9))
  )
}
