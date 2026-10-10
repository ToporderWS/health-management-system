/**
 * 管理员端路由（固定 12 个一级模块，不新增一级菜单）
 * meta.role = 'admin'
 */
import { ROLE } from '@/utils/config'

export const adminMenus = [
  { path: '/admin/dashboard', title: '01 系统首页', icon: 'HomeFilled' },
  { path: '/admin/users', title: '02 普通用户管理', icon: 'User' },
  { path: '/admin/doctors', title: '03 医生管理', icon: 'FirstAidKit' },
  { path: '/admin/coaches', title: '04 健身教练管理', icon: 'Basketball' },
  { path: '/admin/audit', title: '05 账号审核中心', icon: 'Checked' },
  { path: '/admin/relations', title: '06 角色关系管理', icon: 'Connection' },
  { path: '/admin/health-data', title: '07 健康数据中心', icon: 'DataLine' },
  { path: '/admin/plans', title: '08 健康计划管理', icon: 'List' },
  { path: '/admin/doctor-business', title: '09 医生业务监管', icon: 'Notebook' },
  { path: '/admin/coach-business', title: '10 健身业务监管', icon: 'Stopwatch' },
  { path: '/admin/content', title: '11 内容运营管理', icon: 'Document' },
  { path: '/admin/system', title: '12 系统管理', icon: 'Setting' },
]

export default [
  {
    path: '/admin/login',
    name: 'admin-login',
    component: () => import('@/views/admin/Login.vue'),
    meta: { role: ROLE.ADMIN, public: true, title: '管理员登录' },
  },
  {
    path: '/admin',
    component: () => import('@/views/admin/AdminShell.vue'),
    redirect: '/admin/dashboard',
    meta: { role: ROLE.ADMIN },
    children: [
      {
        path: 'dashboard',
        name: 'admin-dashboard',
        component: () => import('@/views/admin/Dashboard.vue'),
        meta: { role: ROLE.ADMIN, title: '01 系统首页' },
      },
      {
        path: 'users',
        name: 'admin-users',
        component: () => import('@/views/admin/Users.vue'),
        meta: { role: ROLE.ADMIN, title: '02 普通用户管理' },
      },
      {
        path: 'doctors',
        name: 'admin-doctors',
        component: () => import('@/views/admin/Doctors.vue'),
        meta: { role: ROLE.ADMIN, title: '03 医生管理' },
      },
      {
        path: 'coaches',
        name: 'admin-coaches',
        component: () => import('@/views/admin/Coaches.vue'),
        meta: { role: ROLE.ADMIN, title: '04 健身教练管理' },
      },
      {
        path: 'audit',
        name: 'admin-audit',
        component: () => import('@/views/admin/Audit.vue'),
        meta: { role: ROLE.ADMIN, title: '05 账号审核中心' },
      },
      {
        path: 'relations',
        name: 'admin-relations',
        component: () => import('@/views/admin/Relations.vue'),
        meta: { role: ROLE.ADMIN, title: '06 角色关系管理' },
      },
      {
        path: 'health-data',
        name: 'admin-health-data',
        component: () => import('@/views/admin/HealthData.vue'),
        meta: { role: ROLE.ADMIN, title: '07 健康数据中心' },
      },
      {
        path: 'plans',
        name: 'admin-plans',
        component: () => import('@/views/admin/Plans.vue'),
        meta: { role: ROLE.ADMIN, title: '08 健康计划管理' },
      },
      {
        path: 'doctor-business',
        name: 'admin-doctor-business',
        component: () => import('@/views/admin/DoctorBusiness.vue'),
        meta: { role: ROLE.ADMIN, title: '09 医生业务监管' },
      },
      {
        path: 'coach-business',
        name: 'admin-coach-business',
        component: () => import('@/views/admin/CoachBusiness.vue'),
        meta: { role: ROLE.ADMIN, title: '10 健身业务监管' },
      },
      {
        path: 'content',
        name: 'admin-content',
        component: () => import('@/views/admin/Content.vue'),
        meta: { role: ROLE.ADMIN, title: '11 内容运营管理' },
      },
      {
        path: 'system',
        name: 'admin-system',
        component: () => import('@/views/admin/System.vue'),
        meta: { role: ROLE.ADMIN, title: '12 系统管理' },
      },
    ],
  },
]
