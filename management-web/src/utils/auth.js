/**
 * 登录态管理：三种 PC 角色的 Token 与用户信息相互独立存储。
 * 医生 Token 不能用于教练/管理员接口，反之亦然。
 */
import { reactive } from 'vue'
import { ROLE } from './config'

const STORAGE_KEY = {
  [ROLE.DOCTOR]: 'hms_doctor_token',
  [ROLE.COACH]: 'hms_coach_token',
  [ROLE.ADMIN]: 'hms_admin_token',
}

const INFO_KEY = {
  [ROLE.DOCTOR]: 'hms_doctor_info',
  [ROLE.COACH]: 'hms_coach_info',
  [ROLE.ADMIN]: 'hms_admin_info',
}

/** 全局响应式登录态（按角色隔离） */
export const authState = reactive({
  doctor: { token: '', info: null },
  coach: { token: '', info: null },
  admin: { token: '', info: null },
})

function safeParse(text) {
  try {
    return text ? JSON.parse(text) : null
  } catch (e) {
    return null
  }
}

/** 应用启动时恢复登录态 */
export function restoreAuth() {
  Object.values(ROLE).forEach((role) => {
    authState[role].token = localStorage.getItem(STORAGE_KEY[role]) || ''
    authState[role].info = safeParse(localStorage.getItem(INFO_KEY[role]))
  })
}

export function getToken(role) {
  return authState[role]?.token || localStorage.getItem(STORAGE_KEY[role]) || ''
}

export function getUserInfo(role) {
  return authState[role]?.info || safeParse(localStorage.getItem(INFO_KEY[role]))
}

export function setAuth(role, token, info) {
  authState[role].token = token
  authState[role].info = info
  localStorage.setItem(STORAGE_KEY[role], token)
  localStorage.setItem(INFO_KEY[role], JSON.stringify(info || null))
}

export function setUserInfo(role, info) {
  authState[role].info = info
  localStorage.setItem(INFO_KEY[role], JSON.stringify(info || null))
}

/** 清除指定角色登录态（401 或主动退出时调用） */
export function clearAuth(role) {
  authState[role].token = ''
  authState[role].info = null
  localStorage.removeItem(STORAGE_KEY[role])
  localStorage.removeItem(INFO_KEY[role])
}

export function isLogin(role) {
  return !!getToken(role)
}
