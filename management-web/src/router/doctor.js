/**
 * 医生端路由（独立 Dashboard / 菜单 / 页面 / 权限）
 * meta.role = 'doctor'，meta.public = true 表示无需登录
 */
import { ROLE } from '@/utils/config'

export const doctorMenus = [
  { path: '/doctor/dashboard', title: '医生首页', icon: 'HomeFilled' },
  { path: '/doctor/patients', title: '患者管理', icon: 'User' },
  { path: '/doctor/health', title: '患者健康数据', icon: 'DataLine' },
  { path: '/doctor/trends', title: '健康趋势', icon: 'TrendCharts' },
  { path: '/doctor/advice', title: '健康建议', icon: 'ChatDotRound' },
  { path: '/doctor/notices', title: '体检通知', icon: 'Bell' },
  { path: '/doctor/records', title: '医疗记录', icon: 'Notebook' },
  { path: '/doctor/profile', title: '个人中心', icon: 'Setting' },
]

export default [
  {
    path: '/doctor/login',
    name: 'doctor-login',
    component: () => import('@/views/doctor/Login.vue'),
    meta: { role: ROLE.DOCTOR, public: true, title: '医生登录' },
  },
  {
    path: '/doctor/register',
    name: 'doctor-register',
    component: () => import('@/views/doctor/Register.vue'),
    meta: { role: ROLE.DOCTOR, public: true, title: '医生注册申请' },
  },
  {
    path: '/doctor',
    component: () => import('@/views/doctor/DoctorShell.vue'),
    redirect: '/doctor/dashboard',
    meta: { role: ROLE.DOCTOR },
    children: [
      {
        path: 'dashboard',
        name: 'doctor-dashboard',
        component: () => import('@/views/doctor/Dashboard.vue'),
        meta: { role: ROLE.DOCTOR, title: '医生首页' },
      },
      {
        path: 'patients',
        name: 'doctor-patients',
        component: () => import('@/views/doctor/Patients.vue'),
        meta: { role: ROLE.DOCTOR, title: '患者管理' },
      },
      {
        path: 'health',
        name: 'doctor-health',
        component: () => import('@/views/doctor/Health.vue'),
        meta: { role: ROLE.DOCTOR, title: '患者健康数据' },
      },
      {
        path: 'trends',
        name: 'doctor-trends',
        component: () => import('@/views/doctor/Trends.vue'),
        meta: { role: ROLE.DOCTOR, title: '健康趋势' },
      },
      {
        path: 'advice',
        name: 'doctor-advice',
        component: () => import('@/views/doctor/Advice.vue'),
        meta: { role: ROLE.DOCTOR, title: '健康建议' },
      },
      {
        path: 'notices',
        name: 'doctor-notices',
        component: () => import('@/views/doctor/Notices.vue'),
        meta: { role: ROLE.DOCTOR, title: '体检通知' },
      },
      {
        path: 'records',
        name: 'doctor-records',
        component: () => import('@/views/doctor/Records.vue'),
        meta: { role: ROLE.DOCTOR, title: '医疗记录' },
      },
      {
        path: 'profile',
        name: 'doctor-profile',
        component: () => import('@/views/doctor/Profile.vue'),
        meta: { role: ROLE.DOCTOR, title: '个人中心' },
      },
    ],
  },
]
