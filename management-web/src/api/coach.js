/** 健身教练端接口（全部使用 coach_token） */
import { buildQuery, coachRequest as http } from './request'

export const coachApi = {
  register: (data) => http.post('/coach/register', data),
  login: (data) => http.post('/coach/login', data),
  logout: () => http.post('/coach/logout'),
  info: () => http.get('/coach/info'),
  dashboard: () => http.get('/coach/dashboard'),

  // 学员
  studentList: (params) => http.get('/coach/student/list', { params: buildQuery(params) }),
  studentDetail: (userId) => http.get('/coach/student/detail', { params: { user_id: userId } }),
  studentSportData: (params) =>
    http.get('/coach/student/sport_data', { params: buildQuery(params) }),
  studentStatistics: (userId, days = 30) =>
    http.get('/coach/student/statistics', { params: { user_id: userId, days } }),

  // 运动目标
  goalList: (params) => http.get('/coach/sport_goal/list', { params: buildQuery(params) }),
  goalSave: (data) => http.post('/coach/sport_goal/save', data),
  goalUpdateStatus: (data) => http.post('/coach/sport_goal/update_status', data),

  // 训练计划
  planList: (params) => http.get('/coach/training_plan/list', { params: buildQuery(params) }),
  planSave: (data) => http.post('/coach/training_plan/save', data),
  planUpdateStatus: (data) => http.post('/coach/training_plan/update_status', data),

  // 健身建议
  adviceList: (params) => http.get('/coach/fitness_advice/list', { params: buildQuery(params) }),
  adviceSave: (data) => http.post('/coach/fitness_advice/save', data),

  // 个人中心
  updatePwd: (data) => http.post('/coach/update_pwd', data),
  uploadAvatar: (formData) => http.post('/coach/upload_avatar', formData),
}
