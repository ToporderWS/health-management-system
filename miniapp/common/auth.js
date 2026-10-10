/**
 * 小程序登录态管理：只保存 user_token 与用户缓存。
 * 注意：业务数据一律来自 MySQL，本地缓存仅用于登录态与展示加速。
 */
const TOKEN_KEY = 'user_token'
const INFO_KEY = 'user_info'

export function getToken() {
  return uni.getStorageSync(TOKEN_KEY) || ''
}

export function getUserInfo() {
  const info = uni.getStorageSync(INFO_KEY)
  return info || null
}

export function setToken(token) {
  uni.setStorageSync(TOKEN_KEY, token || '')
}

export function setUserInfo(info) {
  uni.setStorageSync(INFO_KEY, info || null)
}

export function setAuth(token, info) {
  setToken(token)
  setUserInfo(info)
}

/** 退出登录：清除 user_token 与用户缓存 */
export function clearAuth() {
  uni.removeStorageSync(TOKEN_KEY)
  uni.removeStorageSync(INFO_KEY)
}

export function isLogin() {
  return !!getToken()
}

/**
 * 已登录校验：未登录时提示并跳转登录页。
 * @returns {boolean} 是否已登录
 */
export function ensureLogin() {
  if (isLogin()) return true
  uni.showToast({ title: '请先登录', icon: 'none' })
  setTimeout(() => {
    uni.navigateTo({ url: '/pages/login/index' })
  }, 600)
  return false
}
