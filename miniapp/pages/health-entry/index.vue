<template>
  <view class="hm-page entry">
    <!-- 录入类型切换 -->
    <view class="entry__tabs">
      <view
        v-for="t in tabs"
        :key="t.key"
        class="entry__tab"
        :class="{ 'entry__tab--active': activeTab === t.key }"
        @tap="switchTab(t.key)"
      >
        {{ t.label }}
      </view>
    </view>

    <!-- ============ 健康指标 ============ -->
    <view v-if="activeTab === 'health'" class="hm-card">
      <view class="hm-card__title"><text class="hm-title-text">健康指标录入</text></view>

      <picker mode="date" :value="health.record_date" @change="health.record_date = $event.detail.value">
        <view class="hm-field">
          <text class="hm-field__label">记录日期</text>
          <text class="hm-field__input">{{ health.record_date }}</text>
        </view>
      </picker>

      <view class="hm-field">
        <text class="hm-field__label">体重</text>
        <input class="hm-field__input" type="digit" placeholder="如 62.5" placeholder-class="ph"
          :value="health.weight" @input="health.weight = $event.detail.value" />
        <text class="hm-field__unit">kg</text>
      </view>
      <view class="hm-field">
        <text class="hm-field__label">收缩压(高压)</text>
        <input class="hm-field__input" type="number" placeholder="如 120" placeholder-class="ph"
          :value="health.blood_pressure_high" @input="health.blood_pressure_high = $event.detail.value" />
        <text class="hm-field__unit">mmHg</text>
      </view>
      <view class="hm-field">
        <text class="hm-field__label">舒张压(低压)</text>
        <input class="hm-field__input" type="number" placeholder="如 80" placeholder-class="ph"
          :value="health.blood_pressure_low" @input="health.blood_pressure_low = $event.detail.value" />
        <text class="hm-field__unit">mmHg</text>
      </view>
      <view class="hm-field">
        <text class="hm-field__label">心率</text>
        <input class="hm-field__input" type="number" placeholder="如 72" placeholder-class="ph"
          :value="health.heart_rate" @input="health.heart_rate = $event.detail.value" />
        <text class="hm-field__unit">次/分</text>
      </view>
      <view class="hm-field">
        <text class="hm-field__label">血糖</text>
        <input class="hm-field__input" type="digit" placeholder="如 5.2" placeholder-class="ph"
          :value="health.blood_sugar" @input="health.blood_sugar = $event.detail.value" />
        <text class="hm-field__unit">mmol/L</text>
      </view>

      <view class="hm-btn" :class="{ 'hm-btn--disabled': submitting }" @tap="submitHealth">
        {{ submitting ? '提交中...' : '保存健康指标' }}
      </view>
    </view>

    <!-- ============ 睡眠 ============ -->
    <view v-if="activeTab === 'sleep'" class="hm-card">
      <view class="hm-card__title"><text class="hm-title-text">睡眠记录录入</text></view>

      <picker mode="date" :value="sleep.sleep_date" @change="sleep.sleep_date = $event.detail.value">
        <view class="hm-field">
          <text class="hm-field__label">睡眠日期</text>
          <text class="hm-field__input">{{ sleep.sleep_date }}</text>
        </view>
      </picker>

      <picker mode="date" :value="sleep.startDate" @change="sleep.startDate = $event.detail.value">
        <view class="hm-field">
          <text class="hm-field__label">入睡日期</text>
          <text class="hm-field__input">{{ sleep.startDate }}</text>
        </view>
      </picker>
      <picker mode="time" :value="sleep.startTime" @change="sleep.startTime = $event.detail.value">
        <view class="hm-field">
          <text class="hm-field__label">入睡时间</text>
          <text class="hm-field__input">{{ sleep.startTime }}</text>
        </view>
      </picker>
      <picker mode="date" :value="sleep.endDate" @change="sleep.endDate = $event.detail.value">
        <view class="hm-field">
          <text class="hm-field__label">起床日期</text>
          <text class="hm-field__input">{{ sleep.endDate }}</text>
        </view>
      </picker>
      <picker mode="time" :value="sleep.endTime" @change="sleep.endTime = $event.detail.value">
        <view class="hm-field">
          <text class="hm-field__label">起床时间</text>
          <text class="hm-field__input">{{ sleep.endTime }}</text>
        </view>
      </picker>

      <view class="hm-field">
        <text class="hm-field__label">睡眠质量</text>
        <view class="entry__opts">
          <text
            v-for="q in qualityOptions"
            :key="q"
            class="entry__opt"
            :class="{ 'entry__opt--active': sleep.sleep_quality === q }"
            @tap="sleep.sleep_quality = q"
          >{{ q }}</text>
        </view>
      </view>

      <view class="hm-tip entry__hint">
        睡眠时长由后端根据「起床时间 - 入睡时间」自动计算，无需手动填写。
      </view>

      <view class="hm-btn" :class="{ 'hm-btn--disabled': submitting }" @tap="submitSleep">
        {{ submitting ? '提交中...' : '保存睡眠记录' }}
      </view>
    </view>

    <!-- ============ 运动 ============ -->
    <view v-if="activeTab === 'sport'" class="hm-card">
      <view class="hm-card__title"><text class="hm-title-text">运动记录录入</text></view>

      <picker mode="date" :value="sport.sport_date" @change="sport.sport_date = $event.detail.value">
        <view class="hm-field">
          <text class="hm-field__label">运动日期</text>
          <text class="hm-field__input">{{ sport.sport_date }}</text>
        </view>
      </picker>

      <view class="hm-field">
        <text class="hm-field__label">运动类型</text>
        <picker class="entry__picker" :range="sportTypes" :value="sportTypeIndex" @change="onSportTypeChange">
          <text class="hm-field__input">{{ sport.sport_type || '请选择' }}</text>
        </picker>
      </view>

      <view class="hm-field">
        <text class="hm-field__label">运动时长</text>
        <input class="hm-field__input" type="number" placeholder="如 45" placeholder-class="ph"
          :value="sport.sport_duration" @input="sport.sport_duration = $event.detail.value" />
        <text class="hm-field__unit">分钟</text>
      </view>
      <view class="hm-field">
        <text class="hm-field__label">消耗卡路里</text>
        <input class="hm-field__input" type="number" placeholder="如 320" placeholder-class="ph"
          :value="sport.calorie" @input="sport.calorie = $event.detail.value" />
        <text class="hm-field__unit">kcal</text>
      </view>
      <view class="hm-field">
        <text class="hm-field__label">备注</text>
        <input class="hm-field__input" placeholder="选填，最多200字" placeholder-class="ph" maxlength="200"
          :value="sport.remark" @input="sport.remark = $event.detail.value" />
      </view>

      <view class="hm-btn" :class="{ 'hm-btn--disabled': submitting }" @tap="submitSport">
        {{ submitting ? '提交中...' : '保存运动记录' }}
      </view>
    </view>

    <!-- ============ 健康计划 ============ -->
    <view v-if="activeTab === 'plan'" class="hm-card">
      <view class="hm-card__title"><text class="hm-title-text">健康计划创建</text></view>

      <view class="hm-field">
        <text class="hm-field__label">计划标题</text>
        <input class="hm-field__input" placeholder="如 每日减脂计划" placeholder-class="ph" maxlength="100"
          :value="plan.plan_title" @input="plan.plan_title = $event.detail.value" />
      </view>
      <picker mode="date" :value="plan.plan_start" @change="plan.plan_start = $event.detail.value">
        <view class="hm-field">
          <text class="hm-field__label">开始日期</text>
          <text class="hm-field__input">{{ plan.plan_start }}</text>
        </view>
      </picker>
      <picker mode="date" :value="plan.plan_end" @change="plan.plan_end = $event.detail.value">
        <view class="hm-field">
          <text class="hm-field__label">结束日期</text>
          <text class="hm-field__input">{{ plan.plan_end }}</text>
        </view>
      </picker>
      <view class="entry__textarea-wrap">
        <text class="entry__textarea-label">计划内容</text>
        <textarea class="entry__textarea" placeholder="请填写计划的具体内容" placeholder-class="ph" maxlength="1000"
          :value="plan.plan_content" @input="plan.plan_content = $event.detail.value" />
      </view>

      <view class="hm-btn" :class="{ 'hm-btn--disabled': submitting }" @tap="submitPlan">
        {{ submitting ? '提交中...' : '创建健康计划' }}
      </view>
    </view>

    <!-- ============ 最近记录（真实数据库数据） ============ -->
    <view class="hm-card">
      <view class="hm-card__title">
        <text class="hm-title-text">最近记录</text>
        <text class="entry__refresh" @tap="loadRecords">刷新</text>
      </view>

      <view v-if="loading" class="hm-empty">加载中...</view>
      <view v-else-if="!records.length" class="hm-empty">暂无记录，先在上方录入一条吧</view>
      <view v-else>
        <view v-for="(item, idx) in records" :key="idx" class="hm-item">
          <view class="hm-item__row">
            <text class="hm-item__title">{{ item.title }}</text>
            <text class="hm-item__meta">{{ item.date }}</text>
          </view>
          <view class="hm-item__content">{{ item.content }}</view>
        </view>
      </view>
    </view>

    <view class="hm-tip entry__foot">
      提示：以上数据将实时写入数据库，本地缓存不作为业务数据存储。
    </view>
  </view>
</template>

<script setup>
import { computed, reactive, ref } from 'vue'
import { onShow } from '@dcloudio/uni-app'

import { api } from '@/api/index'
import { ensureLogin, isLogin } from '@/common/auth'
import { SLEEP_QUALITY_OPTIONS, SPORT_TYPES } from '@/common/config'

const tabs = [
  { key: 'health', label: '健康指标' },
  { key: 'sleep', label: '睡眠' },
  { key: 'sport', label: '运动' },
  { key: 'plan', label: '健康计划' },
]

const activeTab = ref('health')
const submitting = ref(false)
const loading = ref(false)
const records = ref([])

const qualityOptions = SLEEP_QUALITY_OPTIONS
const sportTypes = SPORT_TYPES
const sportTypeIndex = computed(() => Math.max(0, sportTypes.indexOf(sport.sport_type)))

function today() {
  const d = new Date()
  const p = (n) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())}`
}

const health = reactive({
  record_date: today(),
  weight: '',
  blood_pressure_high: '',
  blood_pressure_low: '',
  heart_rate: '',
  blood_sugar: '',
})

const nowTime = () => {
  const d = new Date()
  const p = (n) => String(n).padStart(2, '0')
  return `${p(d.getHours())}:${p(d.getMinutes())}`
}

const sleep = reactive({
  sleep_date: today(),
  startDate: today(),
  startTime: '23:00',
  endDate: today(),
  endTime: nowTime(),
  sleep_quality: '一般',
})

const sport = reactive({
  sport_date: today(),
  sport_type: '',
  sport_duration: '',
  calorie: '',
  remark: '',
})

const plan = reactive({
  plan_title: '',
  plan_content: '',
  plan_start: today(),
  plan_end: today(),
})

function onSportTypeChange(e) {
  sport.sport_type = sportTypes[e.detail.value]
}

function switchTab(key) {
  activeTab.value = key
  loadRecords()
}

/* ---------------- 提交 ---------------- */
function requireNum(value, label, { min, max } = {}) {
  if (value === '' || value === null || value === undefined) return `${label}不能为空`
  const num = Number(value)
  if (Number.isNaN(num)) return `${label}格式不正确`
  if (min !== undefined && num < min) return `${label}不能小于 ${min}`
  if (max !== undefined && num > max) return `${label}不能大于 ${max}`
  return ''
}

async function submitHealth() {
  if (submitting.value) return
  const checks = [
    requireNum(health.weight, '体重', { min: 1, max: 500 }),
    requireNum(health.blood_pressure_high, '收缩压', { min: 30, max: 300 }),
    requireNum(health.blood_pressure_low, '舒张压', { min: 20, max: 200 }),
    requireNum(health.heart_rate, '心率', { min: 20, max: 250 }),
    requireNum(health.blood_sugar, '血糖', { min: 0.1, max: 40 }),
  ].filter(Boolean)
  if (checks.length) return uni.showToast({ title: checks[0], icon: 'none' })
  if (!ensureLogin()) return

  submitting.value = true
  try {
    const res = await api.addHealthRecord({ ...health })
    uni.showToast({ title: res.msg || '健康指标记录成功', icon: 'success' })
    health.weight = ''
    health.blood_pressure_high = ''
    health.blood_pressure_low = ''
    health.heart_rate = ''
    health.blood_sugar = ''
    loadRecords()
  } catch (e) {
    /* 错误提示由请求层统一处理 */
  } finally {
    submitting.value = false
  }
}

async function submitSleep() {
  if (submitting.value) return
  const start = `${sleep.startDate} ${sleep.startTime}:00`
  const end = `${sleep.endDate} ${sleep.endTime}:00`
  if (new Date(end.replace(/-/g, '/')) <= new Date(start.replace(/-/g, '/'))) {
    return uni.showToast({ title: '起床时间必须晚于入睡时间', icon: 'none' })
  }
  if (!ensureLogin()) return

  submitting.value = true
  try {
    const res = await api.addSleepRecord({
      sleep_date: sleep.sleep_date,
      sleep_start: start,
      sleep_end: end,
      sleep_quality: sleep.sleep_quality,
    })
    const minutes = res.data && res.data.sleep_duration
    uni.showToast({ title: `睡眠记录成功（${minutes} 分钟）`, icon: 'none' })
    loadRecords()
  } catch (e) {
    /* 忽略 */
  } finally {
    submitting.value = false
  }
}

async function submitSport() {
  if (submitting.value) return
  if (!sport.sport_type) return uni.showToast({ title: '请选择运动类型', icon: 'none' })
  const checks = [
    requireNum(sport.sport_duration, '运动时长', { min: 1, max: 1440 }),
    requireNum(sport.calorie, '消耗卡路里', { min: 0 }),
  ].filter(Boolean)
  if (checks.length) return uni.showToast({ title: checks[0], icon: 'none' })
  if (!ensureLogin()) return

  submitting.value = true
  try {
    const res = await api.addSportRecord({ ...sport })
    uni.showToast({ title: res.msg || '运动记录成功', icon: 'success' })
    sport.sport_duration = ''
    sport.calorie = ''
    sport.remark = ''
    loadRecords()
  } catch (e) {
    /* 忽略 */
  } finally {
    submitting.value = false
  }
}

async function submitPlan() {
  if (submitting.value) return
  if (!plan.plan_title.trim()) return uni.showToast({ title: '请填写计划标题', icon: 'none' })
  if (!plan.plan_content.trim()) return uni.showToast({ title: '请填写计划内容', icon: 'none' })
  if (plan.plan_end < plan.plan_start) {
    return uni.showToast({ title: '结束日期不能早于开始日期', icon: 'none' })
  }
  if (!ensureLogin()) return

  submitting.value = true
  try {
    const res = await api.addHealthPlan({ ...plan })
    uni.showToast({ title: res.msg || '健康计划创建成功', icon: 'success' })
    plan.plan_title = ''
    plan.plan_content = ''
    loadRecords()
  } catch (e) {
    /* 忽略 */
  } finally {
    submitting.value = false
  }
}

/* ---------------- 最近记录 ---------------- */
async function loadRecords() {
  // 未登录时不请求私有接口，直接展示空态
  if (!isLogin()) {
    records.value = []
    return
  }
  loading.value = true
  try {
    if (activeTab.value === 'health') {
      const res = await api.healthRecordList({ page: 1, page_size: 5 })
      records.value = (res.data.list || []).map((r) => ({
        title: `${r.record_date} 健康指标`,
        date: r.created_at || '',
        content: `体重 ${r.weight ?? '--'}kg · 血压 ${r.blood_pressure_high ?? '--'}/${r.blood_pressure_low ?? '--'}mmHg · 心率 ${r.heart_rate ?? '--'} 次/分 · 血糖 ${r.blood_sugar ?? '--'}mmol/L`,
      }))
    } else if (activeTab.value === 'sleep') {
      const res = await api.sleepRecordList({ page: 1, page_size: 5 })
      records.value = (res.data.list || []).map((r) => ({
        title: `${r.sleep_date} 睡眠记录`,
        date: r.created_at || '',
        content: `${r.sleep_start} → ${r.sleep_end} · 时长 ${r.sleep_duration} 分钟 · 质量 ${r.sleep_quality}`,
      }))
    } else if (activeTab.value === 'sport') {
      const res = await api.sportRecordList({ page: 1, page_size: 5 })
      records.value = (res.data.list || []).map((r) => ({
        title: `${r.sport_date} ${r.sport_type}`,
        date: r.created_at || '',
        content: `时长 ${r.sport_duration} 分钟 · 消耗 ${r.calorie} kcal${r.remark ? ' · ' + r.remark : ''}`,
      }))
    } else {
      const res = await api.healthPlanList({ page: 1, page_size: 5 })
      records.value = (res.data.list || []).map((r) => ({
        title: r.plan_title,
        date: r.plan_status_text || '',
        content: `${r.plan_start} ~ ${r.plan_end}\n${r.plan_content}`,
      }))
    }
  } catch (e) {
    records.value = []
  } finally {
    loading.value = false
  }
}

onShow(() => {
  // 首页快捷入口通过 switchTab 跳转时，用本地标记传递目标 Tab（tabBar 页面无法带参）
  const want = uni.getStorageSync('health_entry_tab')
  if (want && tabs.some((t) => t.key === want)) {
    activeTab.value = want
    uni.removeStorageSync('health_entry_tab')
  }
  if (!isLogin()) {
    records.value = []
    return
  }
  loadRecords()
})
</script>

<style scoped>
.entry__tabs {
  display: flex;
  background: #ffffff;
  border-radius: 44rpx;
  padding: 8rpx;
  margin-bottom: 24rpx;
  box-shadow: 0 4rpx 16rpx rgba(46, 125, 50, 0.06);
}

.entry__tab {
  flex: 1;
  text-align: center;
  padding: 18rpx 0;
  font-size: 27rpx;
  color: #7a8b9a;
  border-radius: 36rpx;
}

.entry__tab--active {
  background: linear-gradient(135deg, #2e7d32 0%, #66bb6a 100%);
  color: #ffffff;
  font-weight: 600;
  box-shadow: 0 6rpx 14rpx rgba(46, 125, 50, 0.22);
}

.entry__opts {
  flex: 1;
  display: flex;
  justify-content: flex-end;
}

.entry__opt {
  padding: 8rpx 22rpx;
  margin-left: 12rpx;
  border-radius: 30rpx;
  font-size: 25rpx;
  color: #7a8b9a;
  background: #f1f6f1;
}

.entry__opt--active {
  background: #2e7d32;
  color: #ffffff;
}

.entry__picker {
  flex: 1;
  text-align: right;
}

.entry__textarea-wrap {
  padding: 22rpx 0 0;
}

.entry__textarea-label {
  display: block;
  color: #5c6b7a;
  font-size: 28rpx;
  margin-bottom: 14rpx;
}

.entry__textarea {
  width: 100%;
  min-height: 200rpx;
  background: #f7fbf7;
  border-radius: 16rpx;
  padding: 20rpx;
  box-sizing: border-box;
  font-size: 27rpx;
  color: #1f2d3d;
}

.entry__hint {
  margin-top: 18rpx;
}

.entry__refresh {
  font-size: 24rpx;
  color: #2e7d32;
  font-weight: 400;
}

.entry__foot {
  padding: 0 8rpx 20rpx;
}

.ph {
  color: #b6c2cd;
}
</style>
