/**
 * 小程序统一配置：全项目唯一 API 地址来源，禁止在页面中硬编码 IP。
 * 修改后端地址只需要改这里一处。
 */
export const API_BASE_URL = 'http://192.168.2.219:8080/api'

/** 静态资源（图片）访问地址前缀，数据库仅保存文件名 */
export const STATIC_BASE_URL = 'http://192.168.2.219:8080/static/upload/'

/** 主题色（需求约定） */
export const THEME = {
  primary: '#2E7D32',
  secondary: '#66BB6A',
  background: '#F4FAF5',
  text: '#1F2D3D',
  subText: '#7A8B9A',
  border: '#E6F0E7',
}

/** 睡眠质量可选项（后端同样强校验） */
export const SLEEP_QUALITY_OPTIONS = ['很好', '一般', '较差']

/** 运动类型可选项 */
export const SPORT_TYPES = ['跑步', '快走', '骑行', '游泳', '瑜伽', '力量训练', '球类', '其他']

/** 健康计划状态 */
export const PLAN_STATUS_TEXT = { 0: '进行中', 1: '已完成', 2: '已放弃' }

/** 运动目标 / 训练计划状态 */
export const SPORT_STATUS_TEXT = { 0: '进行中', 1: '已完成', 2: '已结束' }

/** 由文件名拼出完整图片地址 */
export function resolveFileUrl(filename) {
  if (!filename) return ''
  if (/^https?:\/\//i.test(filename)) return filename
  return STATIC_BASE_URL + filename
}
