/** 医生端接口（全部使用 doctor_token） */
import { buildQuery, doctorRequest as http } from './request'

export const doctorApi = {
  register: (data) => http.post('/doctor/register', data),
  login: (data) => http.post('/doctor/login', data),
  logout: () => http.post('/doctor/logout'),
  info: () => http.get('/doctor/info'),
  dashboard: () => http.get('/doctor/dashboard'),

  // 患者
  patientList: (params) => http.get('/doctor/patient/list', { params: buildQuery(params) }),
  patientDetail: (userId) => http.get('/doctor/patient/detail', { params: { user_id: userId } }),
  patientHealthData: (params) =>
    http.get('/doctor/patient/health_data', { params: buildQuery(params) }),
  patientSleepData: (params) =>
    http.get('/doctor/patient/sleep_data', { params: buildQuery(params) }),
  patientSportData: (params) =>
    http.get('/doctor/patient/sport_data', { params: buildQuery(params) }),
  patientPlanData: (params) =>
    http.get('/doctor/patient/plan_data', { params: buildQuery(params) }),
  patientTrend: (userId, days = 30) =>
    http.get('/doctor/patient/trend', { params: { user_id: userId, days } }),

  // 健康建议
  adviceList: (params) => http.get('/doctor/advice/list', { params: buildQuery(params) }),
  adviceSave: (data) => http.post('/doctor/advice/save', data),

  // 体检通知
  noticeList: (params) => http.get('/doctor/medical_notice/list', { params: buildQuery(params) }),
  noticeSave: (data) => http.post('/doctor/medical_notice/save', data),

  // 医疗记录
  recordList: (params) => http.get('/doctor/medical_record/list', { params: buildQuery(params) }),
  recordSave: (data) => http.post('/doctor/medical_record/save', data),

  // 个人中心
  updatePwd: (data) => http.post('/doctor/update_pwd', data),
  uploadAvatar: (formData) => http.post('/doctor/upload_avatar', formData),
}
