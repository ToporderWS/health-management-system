/**
 * 健身教练端路由（独立 Dashboard / 菜单 / 页面 / 权限）
 * meta.role = 'coach'
 */
import { ROLE } from '@/utils/config'

export const coachMenus = [
  { path: '/coach/dashboard', title: '教练首页', icon: 'HomeFilled' },
  { path: '/coach/students', title: '学员管理', icon: 'User' },
  { path: '/coach/sports', title: '运动数据', icon: 'Basketball' },
  { path: '/coach/goals', title: '运动目标', icon: 'Aim' },
  { path: '/coach/training', title: '训练计划', icon: 'Calendar' },
  { path: '/coach/advice', title: '健身建议', icon: 'ChatDotRound' },
  { path: '/coach/profile', title: '个人中心', icon: 'Setting' },
]

export default [
  {
    path: '/coach/login',
    name: 'coach-login',
    component: () => import('@/views/coach/Login.vue'),
    meta: { role: ROLE.COACH, public: true, title: '健身教练登录' },
  },
  {
    path: '/coach/register',
    name: 'coach-register',
    component: () => import('@/views/coach/Register.vue'),
    meta: { role: ROLE.COACH, public: true, title: '健身教练注册申请' },
  },
  {
    path: '/coach',
    component: () => import('@/views/coach/CoachShell.vue'),
    redirect: '/coach/dashboard',
    meta: { role: ROLE.COACH },
    children: [
      {
        path: 'dashboard',
        name: 'coach-dashboard',
        component: () => import('@/views/coach/Dashboard.vue'),
        meta: { role: ROLE.COACH, title: '教练首页' },
      },
      {
        path: 'students',
        name: 'coach-students',
        component: () => import('@/views/coach/Students.vue'),
        meta: { role: ROLE.COACH, title: '学员管理' },
      },
      {
        path: 'sports',
        name: 'coach-sports',
        component: () => import('@/views/coach/Sports.vue'),
        meta: { role: ROLE.COACH, title: '运动数据' },
      },
      {
        path: 'goals',
        name: 'coach-goals',
        component: () => import('@/views/coach/Goals.vue'),
        meta: { role: ROLE.COACH, title: '运动目标' },
      },
      {
        path: 'training',
        name: 'coach-training',
        component: () => import('@/views/coach/Training.vue'),
        meta: { role: ROLE.COACH, title: '训练计划' },
      },
      {
        path: 'advice',
        name: 'coach-advice',
        component: () => import('@/views/coach/Advice.vue'),
        meta: { role: ROLE.COACH, title: '健身建议' },
      },
      {
        path: 'profile',
        name: 'coach-profile',
        component: () => import('@/views/coach/Profile.vue'),
        meta: { role: ROLE.COACH, title: '个人中心' },
      },
    ],
  },
]
