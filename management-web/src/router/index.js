/**
 * 路由总装配 + 全局路由守卫。
 *
 * 守卫规则（前后端双重校验，前端不作为唯一权限依据）：
 * - 未登录访问受保护页面 -> 跳转到「该角色」的登录页
 * - 已登录访问登录/注册页 -> 直接进入对应工作台
 * - 角色不匹配（如医生访问 /admin/*）-> 无对应 Token，被拒绝并跳转管理员登录页
 * - 收到 401 -> 清除对应角色 Token 并跳回其登录页
 */
import { createRouter, createWebHistory } from 'vue-router'

import adminRoutes from './admin'
import coachRoutes from './coach'
import doctorRoutes from './doctor'
import { ROLE, ROLE_META } from '@/utils/config'
import { clearAuth, isLogin } from '@/utils/auth'
import { setUnauthorizedHandler } from '@/api/request'

const routes = [
  {
    path: '/',
    name: 'portal',
    component: () => import('@/views/portal/IdentitySelect.vue'),
    meta: { title: '身份选择' },
  },
  ...doctorRoutes,
  ...coachRoutes,
  ...adminRoutes,
  {
    path: '/:pathMatch(.*)*',
    name: 'not-found',
    component: () => import('@/views/portal/NotFound.vue'),
    meta: { title: '页面不存在' },
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior: () => ({ top: 0 }),
})

router.beforeEach((to) => {
  const role = to.meta?.role

  if (!role) {
    return true
  }

  // 登录/注册页：已登录则直接进工作台
  if (to.meta.public) {
    if (isLogin(role)) {
      return ROLE_META[role].homePath
    }
    return true
  }

  // 受保护页面：必须持有该角色自己的 Token
  if (!isLogin(role)) {
    return { path: ROLE_META[role].loginPath, query: { redirect: to.fullPath } }
  }

  return true
})

router.afterEach((to) => {
  const role = to.meta?.role
  const meta = role ? ROLE_META[role] : null
  document.title = to.meta?.title
    ? `${to.meta.title} · 个人健康管理系统`
    : meta?.portalTitle || '个人健康管理系统'
})

// 后端返回 401 时：清除对应角色登录态并跳回其登录页
setUnauthorizedHandler((role) => {
  clearAuth(role)
  const loginPath = ROLE_META[role]?.loginPath
  if (loginPath && router.currentRoute.value.path !== loginPath) {
    router.replace({ path: loginPath })
  }
})

export function forceLogout(role) {
  clearAuth(role)
  router.replace({ path: ROLE_META[role].loginPath })
}

export { ROLE }
export default router
