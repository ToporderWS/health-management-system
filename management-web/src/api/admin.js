/** 管理员端接口（全部使用 admin_token） */
import { adminRequest as http, buildQuery } from './request'

const q = (params) => ({ params: buildQuery(params) })

export const adminApi = {
  login: (data) => http.post('/admin/login', data),
  logout: () => http.post('/admin/logout'),
  info: () => http.get('/admin/info'),
  dashboard: () => http.get('/admin/dashboard'),

  // ---------- 02 普通用户管理 ----------
  userList: (params) => http.get('/admin/user/list', q(params)),
  userDetail: (id) => http.get('/admin/user/detail', q({ id })),
  userHealthData: (params) => http.get('/admin/user/health_data', q(params)),
  userDoctorService: (userId) => http.get('/admin/user/doctor_service', q({ user_id: userId })),
  userCoachService: (userId) => http.get('/admin/user/coach_service', q({ user_id: userId })),

  // ---------- 03 医生管理 ----------
  doctorList: (params) => http.get('/admin/doctor/list', q(params)),
  doctorDetail: (id) => http.get('/admin/doctor/detail', q({ id })),
  doctorUpdate: (data) => http.post('/admin/doctor/update', data),
  doctorResetPwd: (data) => http.post('/admin/doctor/reset_pwd', data),
  doctorAudit: (data) => http.post('/admin/doctor/audit', data),

  // ---------- 04 健身教练管理 ----------
  coachList: (params) => http.get('/admin/coach/list', q(params)),
  coachDetail: (id) => http.get('/admin/coach/detail', q({ id })),
  coachUpdate: (data) => http.post('/admin/coach/update', data),
  coachResetPwd: (data) => http.post('/admin/coach/reset_pwd', data),
  coachAudit: (data) => http.post('/admin/coach/audit', data),

  // ---------- 05 账号审核中心 ----------
  auditOverview: () => http.get('/admin/audit/overview'),
  auditRecordList: (params) => http.get('/admin/audit/record_list', q(params)),

  // ---------- 06 角色关系管理 ----------
  doctorPatientList: (params) => http.get('/admin/doctor/patient/list', q(params)),
  bindPatient: (data) => http.post('/admin/doctor/bind_patient', data),
  unbindPatient: (data) => http.post('/admin/doctor/unbind_patient', data),
  coachStudentList: (params) => http.get('/admin/coach/student/list', q(params)),
  bindStudent: (data) => http.post('/admin/coach/bind_student', data),
  unbindStudent: (data) => http.post('/admin/coach/unbind_student', data),

  // ---------- 下拉数据源 ----------
  commonUsers: (keyword) => http.get('/admin/common/users', q({ keyword })),
  commonDoctors: () => http.get('/admin/common/doctors'),
  commonCoaches: () => http.get('/admin/common/coaches'),

  // ---------- 07 健康数据中心 ----------
  healthDataStatistics: () => http.get('/admin/health_data/statistics'),
  healthRecordList: (params) => http.get('/admin/health_record/list', q(params)),
  sleepRecordList: (params) => http.get('/admin/sleep_record/list', q(params)),
  sportRecordList: (params) => http.get('/admin/sport_record/list', q(params)),
  exportHealthRecord: (params) =>
    http.get('/admin/health_record/export', { params: buildQuery(params), responseType: 'blob' }),
  exportSleepRecord: (params) =>
    http.get('/admin/sleep_record/export', { params: buildQuery(params), responseType: 'blob' }),
  exportSportRecord: (params) =>
    http.get('/admin/sport_record/export', { params: buildQuery(params), responseType: 'blob' }),

  // ---------- 08 健康计划管理 ----------
  healthPlanList: (params) => http.get('/admin/health_plan/list', q(params)),
  healthPlanStats: () => http.get('/admin/health_plan/stats'),

  // ---------- 09 医生业务监管 ----------
  doctorAdviceList: (params) => http.get('/admin/doctor_advice/list', q(params)),
  medicalNoticeList: (params) => http.get('/admin/medical_notice/list', q(params)),
  medicalRecordList: (params) => http.get('/admin/medical_record/list', q(params)),

  // ---------- 10 健身业务监管 ----------
  sportGoalList: (params) => http.get('/admin/sport_goal/list', q(params)),
  trainingPlanList: (params) => http.get('/admin/training_plan/list', q(params)),
  fitnessAdviceList: (params) => http.get('/admin/fitness_advice/list', q(params)),

  // ---------- 11 内容运营管理 ----------
  articleList: (params) => http.get('/admin/article/list', q(params)),
  articleDetail: (id) => http.get('/admin/article/detail', q({ id })),
  articleSave: (data) => http.post('/admin/article/save', data),
  articleDel: (id) => http.post('/admin/article/del', { id }),
  uploadCover: (formData) => http.post('/admin/article/upload_cover', formData),

  noticeList: (params) => http.get('/admin/notice/list', q(params)),
  noticeDetail: (id) => http.get('/admin/notice/detail', q({ id })),
  noticeSave: (data) => http.post('/admin/notice/save', data),
  noticeDel: (id) => http.post('/admin/notice/del', { id }),

  // ---------- 12 系统管理 ----------
  operationLogList: (params) => http.get('/admin/operation_log/list', q(params)),
  operationLogTypes: () => http.get('/admin/operation_log/types'),
  systemInfo: () => http.get('/admin/system/info'),
  updatePwd: (data) => http.post('/admin/update_pwd', data),
  uploadAvatar: (formData) => http.post('/admin/upload_avatar', formData),
}
