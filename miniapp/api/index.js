/** 小程序端全部接口定义（普通用户，使用 user_token） */
import { get, post, upload } from '@/common/request'

export const api = {
  // ---------------- 用户 ----------------
  register: (data) => post('/user/register', data, { withToken: false }),
  login: (data) => post('/user/login', data, { withToken: false }),
  userInfo: () => get('/user/info'),
  updateInfo: (data) => post('/user/update_info', data),
  updatePwd: (data) => post('/user/update_pwd', data),
  uploadAvatar: (filePath) => upload('/user/upload_avatar', filePath),
  logout: () => post('/user/logout'),

  // ---------------- 健康指标 ----------------
  addHealthRecord: (data) => post('/health_record/add', data),
  healthRecordList: (params) => get('/health_record/my_list', params),

  // ---------------- 睡眠 ----------------
  addSleepRecord: (data) => post('/sleep_record/add', data),
  sleepRecordList: (params) => get('/sleep_record/my_list', params),

  // ---------------- 运动 ----------------
  addSportRecord: (data) => post('/sport_record/add', data),
  sportRecordList: (params) => get('/sport_record/my_list', params),

  // ---------------- 健康计划 ----------------
  addHealthPlan: (data) => post('/health_plan/add', data),
  healthPlanList: (params) => get('/health_plan/my_list', params),
  updatePlanStatus: (data) => post('/health_plan/update_status', data),

  // ---------------- 数据报告 ----------------
  reportStatistics: (days = 30) => get('/report/statistics', { days }),

  // ---------------- 健康科普 / 公告（无需登录） ----------------
  articleList: (params) => get('/article/list', params, { withToken: false }),
  articleDetail: (id) => get('/article/detail', { id }, { withToken: false }),
  noticeList: (params) => get('/notice/list', params, { withToken: false }),
  noticeDetail: (id) => get('/notice/detail', { id }, { withToken: false }),

  // ---------------- 医生服务（只读本人） ----------------
  doctorAdvice: () => get('/user/doctor_advice'),
  medicalNotice: () => get('/user/medical_notice'),
  medicalRecord: () => get('/user/medical_record'),

  // ---------------- 健身服务（只读本人） ----------------
  sportGoal: () => get('/user/sport_goal'),
  trainingPlan: () => get('/user/training_plan'),
  fitnessAdvice: () => get('/user/fitness_advice'),
}
