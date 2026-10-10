/**
 * Axios 统一封装：
 * - 按角色注入对应 Token（医生 / 教练 / 管理员互不串用）
 * - 统一解析后端 {code,msg,data} 契约
 * - 401 统一清除该角色 Token 并跳回其登录页
 */
import axios from 'axios'
import { ElMessage } from 'element-plus'

import { API_BASE_URL, ROLE_META } from '@/utils/config'
import { clearAuth, getToken } from '@/utils/auth'

/** 由路由层注册的 401 处理器，避免 request <-> router 循环依赖 */
let unauthorizedHandler = null
export function setUnauthorizedHandler(fn) {
  unauthorizedHandler = fn
}

function handleUnauthorized(role) {
  clearAuth(role)
  if (typeof unauthorizedHandler === 'function') {
    unauthorizedHandler(role)
  } else {
    window.location.href = ROLE_META[role].loginPath
  }
}

/** 允许携带完整响应（文件流等）的请求标记 */
const RAW_RESPONSE = ['arraybuffer', 'blob', 'text']

export function createRequest(role) {
  const instance = axios.create({
    baseURL: API_BASE_URL,
    timeout: 20000,
  })

  instance.interceptors.request.use((config) => {
    // 每次请求都实时读取 Token，避免登录/退出后缓存不一致
    const token = getToken(role)
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  })

  instance.interceptors.response.use(
    (response) => {
      // 文件流直接返回
      if (RAW_RESPONSE.includes(response.config.responseType)) {
        return response
      }
      const body = response.data
      if (!body || typeof body !== 'object') {
        ElMessage.error('服务端返回格式异常')
        return Promise.reject(new Error('服务端返回格式异常'))
      }
      if (body.code !== 200) {
        if (body.code === 401) {
          ElMessage.error(body.msg || '登录状态已失效，请重新登录')
          handleUnauthorized(role)
        } else {
          ElMessage.error(body.msg || '操作失败')
        }
        return Promise.reject(Object.assign(new Error(body.msg || '操作失败'), { body }))
      }
      // 成功：resolve 出 data 与 msg，业务代码只关心 data
      return { data: body.data, msg: body.msg }
    },
    (error) => {
      const status = error?.response?.status
      const body = error?.response?.data
      if (status === 401) {
        ElMessage.error((body && body.msg) || '登录状态已失效，请重新登录')
        handleUnauthorized(role)
      } else if (status === 400) {
        ElMessage.error((body && body.msg) || '请求参数错误')
      } else if (error.code === 'ECONNABORTED') {
        ElMessage.error('请求超时，请检查后端服务是否已启动')
      } else {
        ElMessage.error((body && body.msg) || '网络异常，请检查后端服务与网络连接')
      }
      return Promise.reject(error)
    }
  )

  return instance
}

/** 三个角色的请求实例（各自独立 Token） */
export const doctorRequest = createRequest('doctor')
export const coachRequest = createRequest('coach')
export const adminRequest = createRequest('admin')

/** 统一分页参数对象 */
export function buildQuery(params = {}) {
  const query = {}
  Object.keys(params).forEach((key) => {
    const value = params[key]
    if (value !== undefined && value !== null && value !== '') {
      query[key] = value
    }
  })
  return query
}
