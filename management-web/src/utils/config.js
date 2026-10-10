/**
 * 统一前端配置：全项目唯一 API 地址与静态资源地址来源。
 * 禁止在各页面重复硬编码 IP。
 */
export const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || '/api'

export const STATIC_BASE_URL =
  import.meta.env.VITE_STATIC_BASE_URL || '/static/upload/'

/** 三种 PC 角色 */
export const ROLE = {
  DOCTOR: 'doctor',
  COACH: 'coach',
  ADMIN: 'admin',
}

/** 角色中文名与主题色（统一品牌设计） */
export const ROLE_META = {
  [ROLE.DOCTOR]: {
    label: '医生',
    portalTitle: '个人健康管理系统 · 医生工作台',
    primary: '#0F9D8C',
    primaryDark: '#0B7A6D',
    gradient: 'linear-gradient(135deg, #0F9D8C 0%, #2BC4AE 100%)',
    loginPath: '/doctor/login',
    homePath: '/doctor/dashboard',
  },
  [ROLE.COACH]: {
    label: '健身教练',
    portalTitle: '个人健康管理系统 · 健身教练工作台',
    primary: '#1E6FFF',
    primaryDark: '#1450C4',
    gradient: 'linear-gradient(135deg, #1E6FFF 0%, #4FA3FF 100%)',
    loginPath: '/coach/login',
    homePath: '/coach/dashboard',
  },
  [ROLE.ADMIN]: {
    label: '管理员',
    portalTitle: '个人健康管理系统 · 管理后台',
    primary: '#1B3A6B',
    primaryDark: '#12294C',
    gradient: 'linear-gradient(135deg, #1B3A6B 0%, #2F5DA8 100%)',
    loginPath: '/admin/login',
    homePath: '/admin/dashboard',
  },
}

/** 由数据库保存的文件名拼出可访问地址（数据库只存文件名） */
export function resolveFileUrl(filename) {
  if (!filename) return ''
  if (/^https?:\/\//i.test(filename)) return filename
  return STATIC_BASE_URL + filename
}
