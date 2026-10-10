/**
 * uni.request 统一封装：
 * - 自动拼接 API_BASE_URL
 * - 自动携带 Authorization: Bearer {user_token}
 * - 统一解析后端 {code, msg, data} 契约
 * - 401 统一清除本地登录态并跳转登录页
 */
import { API_BASE_URL } from './config'
import { clearAuth, getToken } from './auth'

let redirecting = false

function handleUnauthorized(msg) {
  clearAuth()
  if (redirecting) return
  redirecting = true
  uni.showToast({ title: msg || '请先登录', icon: 'none' })
  setTimeout(() => {
    uni.navigateTo({ url: '/pages/login/index' })
    setTimeout(() => {
      redirecting = false
    }, 800)
  }, 600)
}

export function request(options) {
  const { url, method = 'GET', data = {}, showLoading = false, withToken = true } = options

  if (showLoading) {
    uni.showLoading({ title: '加载中...', mask: true })
  }

  const header = { 'Content-Type': 'application/json' }
  if (withToken) {
    const token = getToken()
    if (token) {
      header.Authorization = `Bearer ${token}`
    }
  }

  return new Promise((resolve, reject) => {
    uni.request({
      url: API_BASE_URL + url,
      method,
      data,
      header,
      timeout: 20000,
      success: (res) => {
        const body = res.data
        if (!body || typeof body !== 'object') {
          uni.showToast({ title: '服务端返回格式异常', icon: 'none' })
          reject(new Error('服务端返回格式异常'))
          return
        }
        if (body.code === 200) {
          resolve({ data: body.data, msg: body.msg })
          return
        }
        if (body.code === 401) {
          handleUnauthorized(body.msg)
        } else {
          uni.showToast({ title: body.msg || '操作失败', icon: 'none' })
        }
        reject(Object.assign(new Error(body.msg || '操作失败'), { body }))
      },
      fail: (err) => {
        uni.showToast({ title: '网络异常，请检查后端服务是否已启动', icon: 'none' })
        reject(err)
      },
      complete: () => {
        if (showLoading) uni.hideLoading()
      },
    })
  })
}

export function get(url, data, options = {}) {
  return request({ url, method: 'GET', data, ...options })
}

export function post(url, data, options = {}) {
  return request({ url, method: 'POST', data, ...options })
}

/** 文件上传（uni.uploadFile） */
export function upload(url, filePath, name = 'file') {
  const token = getToken()
  return new Promise((resolve, reject) => {
    uni.uploadFile({
      url: API_BASE_URL + url,
      filePath,
      name,
      header: token ? { Authorization: `Bearer ${token}` } : {},
      success: (res) => {
        let body
        try {
          body = JSON.parse(res.data)
        } catch (e) {
          uni.showToast({ title: '上传响应解析失败', icon: 'none' })
          reject(new Error('上传响应解析失败'))
          return
        }
        if (body.code === 200) {
          resolve({ data: body.data, msg: body.msg })
        } else {
          if (body.code === 401) handleUnauthorized(body.msg)
          else uni.showToast({ title: body.msg || '上传失败', icon: 'none' })
          reject(new Error(body.msg || '上传失败'))
        }
      },
      fail: (err) => {
        uni.showToast({ title: '上传失败，请检查网络', icon: 'none' })
        reject(err)
      },
    })
  })
}
