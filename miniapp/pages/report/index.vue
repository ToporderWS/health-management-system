<template>
  <view class="hm-page report">
    <!-- 汇总概览 -->
    <view class="report__summary hm-gradient">
      <view class="report__summary-title">最近 {{ days }} 天数据概览</view>
      <view class="report__summary-grid">
        <view class="report__summary-cell">
          <text class="report__summary-value">{{ summary.avg_weight ?? '--' }}</text>
          <text class="report__summary-label">平均体重(kg)</text>
        </view>
        <view class="report__summary-cell">
          <text class="report__summary-value">{{ summary.total_sport_minutes ?? 0 }}</text>
          <text class="report__summary-label">运动总时长(分)</text>
        </view>
        <view class="report__summary-cell">
          <text class="report__summary-value">{{ avgSleepHours }}</text>
          <text class="report__summary-label">平均睡眠(小时)</text>
        </view>
        <view class="report__summary-cell">
          <text class="report__summary-value">{{ summary.total_calorie ?? 0 }}</text>
          <text class="report__summary-label">累计消耗(kcal)</text>
        </view>
      </view>
    </view>

    <!-- 登录校验 -->
    <view v-if="!logged" class="hm-card">
      <view class="hm-empty">登录后可查看你的真实健康数据报告</view>
      <view class="hm-btn" @tap="goLogin">前往登录</view>
    </view>

    <template v-else>
      <!-- 体重趋势 -->
      <view class="hm-card">
        <view class="hm-card__title">
          <text class="hm-title-text">最近 {{ days }} 天体重趋势</text>
          <text class="report__unit">kg</text>
        </view>
        <u-charts
          v-if="weightData.categories.length"
          chart-id="ucWeight"
          type="line"
          unit="kg"
          :chart-data="weightData"
          :height="380"
          :opts="{ legend: { show: false }, yAxis: { data: [{ min: weightMin }] } }"
        />
        <view v-else class="hm-empty">暂无体重记录</view>
      </view>

      <!-- 血压趋势 -->
      <view class="hm-card">
        <view class="hm-card__title">
          <text class="hm-title-text">最近 {{ days }} 天血压趋势</text>
          <text class="report__unit">mmHg</text>
        </view>
        <u-charts
          v-if="bpData.categories.length"
          chart-id="ucBp"
          type="line"
          unit="mmHg"
          :chart-data="bpData"
          :height="380"
        />
        <view v-else class="hm-empty">暂无血压记录</view>
      </view>

      <!-- 月度运动时长 -->
      <view class="hm-card">
        <view class="hm-card__title">
          <text class="hm-title-text">运动时长（按天）</text>
          <text class="report__unit">分钟</text>
        </view>
        <u-charts
          v-if="sportData.categories.length"
          chart-id="ucSport"
          type="column"
          unit="分钟"
          :chart-data="sportData"
          :height="380"
          :opts="{ legend: { show: false } }"
        />
        <view v-else class="hm-empty">暂无运动记录</view>
      </view>

      <!-- 运动类型分布 -->
      <view class="hm-card">
        <view class="hm-card__title">
          <text class="hm-title-text">运动类型分布</text>
          <text class="report__unit">分钟</text>
        </view>
        <u-charts
          v-if="sportTypeData.categories.length"
          chart-id="ucSportType"
          type="ring"
          unit="分钟"
          :chart-data="sportTypeData"
          :height="420"
        />
        <view v-else class="hm-empty">暂无运动记录</view>
      </view>

      <!-- 睡眠质量占比 -->
      <view class="hm-card">
        <view class="hm-card__title">
          <text class="hm-title-text">睡眠质量占比</text>
          <text class="report__unit">次</text>
        </view>
        <u-charts
          v-if="sleepQualityData.categories.length"
          chart-id="ucSleepQuality"
          type="ring"
          unit="次"
          :chart-data="sleepQualityData"
          :height="420"
        />
        <view v-else class="hm-empty">暂无睡眠记录</view>
      </view>

      <!-- 睡眠时长趋势 -->
      <view class="hm-card">
        <view class="hm-card__title">
          <text class="hm-title-text">睡眠时长趋势</text>
          <text class="report__unit">分钟</text>
        </view>
        <u-charts
          v-if="sleepTrendData.categories.length"
          chart-id="ucSleepTrend"
          type="area"
          unit="分钟"
          :chart-data="sleepTrendData"
          :height="380"
          :opts="{ legend: { show: false } }"
        />
        <view v-else class="hm-empty">暂无睡眠记录</view>
      </view>

      <!-- 健康计划列表 -->
      <view class="hm-card">
        <view class="hm-card__title">
          <text class="hm-title-text">我的健康计划</text>
          <text class="report__unit">{{ planList.length }} 条</text>
        </view>
        <view v-if="!planList.length" class="hm-empty">暂无健康计划</view>
        <view v-for="p in planList" :key="p.id" class="hm-item">
          <view class="hm-item__row">
            <text class="hm-item__title">{{ p.plan_title }}</text>
            <text
              class="hm-tag"
              :class="{ 'hm-tag--gray': p.plan_status !== 0, 'hm-tag--orange': p.plan_status === 2 }"
            >{{ p.plan_status_text }}</text>
          </view>
          <view class="hm-item__row">
            <text class="hm-item__meta">{{ p.plan_start }} ~ {{ p.plan_end }}</text>
          </view>
          <view class="hm-item__content">{{ p.plan_content }}</view>
        </view>
      </view>
    </template>

    <view class="hm-tip report__foot">
      以上图表数据全部来自数据库真实记录；系统仅做趋势展示与健康提醒，不提供任何诊断结论。
    </view>
  </view>
</template>

<script setup>
import { computed, ref } from 'vue'
import { onShow, onPullDownRefresh } from '@dcloudio/uni-app'

import { api } from '@/api/index'
import { isLogin } from '@/common/auth'

const days = 30
const logged = ref(false)
const summary = ref({})
const weightData = ref({ categories: [], series: [] })
const bpData = ref({ categories: [], series: [] })
const sportData = ref({ categories: [], series: [] })
const sportTypeData = ref({ categories: [], series: [] })
const sleepQualityData = ref({ categories: [], series: [] })
const sleepTrendData = ref({ categories: [], series: [] })
const planList = ref([])

const avgSleepHours = computed(() => {
  const m = summary.value.avg_sleep_minutes
  if (!m) return '--'
  return (m / 60).toFixed(1)
})

/** 体重 Y 轴最小值：让曲线起伏更明显，但保留 5kg 余量 */
const weightMin = computed(() => {
  const list = weightData.value.series[0] ? weightData.value.series[0].data : []
  if (!list.length) return 0
  const min = Math.min(...list)
  return Math.max(0, Math.floor(min - 5))
})

function goLogin() {
  uni.navigateTo({ url: '/pages/login/index' })
}

/** 月份日期缩略显示，避免 X 轴标签拥挤 */
function shortDate(dateStr) {
  return String(dateStr || '').slice(5)
}

/**
 * 只保留某字段确实带数值的记录：
 * null / undefined / '' / NaN 一律剔除，避免被 Number() 折成 0 混进真实数据。
 * 这样 0 条 → 空状态、1 条 → 单点、2 条以上 → 正常趋势，三种情况都走自然分支。
 */
function pick(list, key) {
  return (list || []).filter(
    (x) => x && x[key] !== null && x[key] !== undefined && x[key] !== '' && !Number.isNaN(Number(x[key]))
  )
}

async function load() {
  logged.value = isLogin()
  if (!logged.value) return
  try {
    const res = await api.reportStatistics(days)
    const d = res.data || {}
    summary.value = d.summary || {}
    planList.value = d.plan_list || []

    const wRows = pick(d.weight_trend, 'weight')
    weightData.value = {
      categories: wRows.map((x) => shortDate(x.date)),
      series: [{ name: '体重', data: wRows.map((x) => Number(x.weight)) }],
    }

    const bpRows = pick(d.blood_pressure_trend, 'high')
    bpData.value = {
      categories: bpRows.map((x) => shortDate(x.date)),
      series: [
        { name: '收缩压', data: bpRows.map((x) => Number(x.high)) },
        { name: '舒张压', data: bpRows.map((x) => Number(x.low) || 0) },
      ],
    }

    const sRows = pick(d.sport_daily, 'duration')
    sportData.value = {
      categories: sRows.map((x) => shortDate(x.date)),
      series: [{ name: '运动时长', data: sRows.map((x) => Number(x.duration)) }],
    }

    // 饼/环图族：uCharts 2.5.0 要求 series[0].data 为 [{ name, value }] 对象数组
    // （等价 ECharts 饼图格式，库内 fixPieSeries 会转换为内部结构）。
    // 若把「纯数值数组」直接传给 series[0].data，fixPieSeries 会对 number 赋 formatter
    // 属性 → MiniProgramError: Cannot create property 'formatter' on number。
    // 只保留 value > 0 的分类；全部为 0 或没有数据时直接置空 → 走「暂无数据」空状态。
    // （若把全 0 数据交给库，库内 count===0 会按 1/series.length 兜底，画出一个并不真实的整圆）
    const sportTypes = (d.sport_by_type || []).filter((x) => x && Number(x.value) > 0)
    sportTypeData.value = sportTypes.length
      ? {
          categories: sportTypes.map((x) => x.name),
          series: [{ data: sportTypes.map((x) => ({ name: x.name, value: Number(x.value) || 0 })) }],
        }
      : { categories: [], series: [] }

    const qualities = (d.sleep_quality || []).filter((x) => x && Number(x.value) > 0)
    sleepQualityData.value = qualities.length
      ? {
          categories: qualities.map((x) => x.name),
          series: [{ data: qualities.map((x) => ({ name: x.name, value: Number(x.value) || 0 })) }],
        }
      : { categories: [], series: [] }

    const stRows = pick(d.sleep_trend, 'duration')
    sleepTrendData.value = {
      categories: stRows.map((x) => shortDate(x.date)),
      series: [{ name: '睡眠时长', data: stRows.map((x) => Number(x.duration)) }],
    }
  } catch (e) {
    /* 401 由请求层统一处理 */
  }
}

onShow(() => {
  load()
})

onPullDownRefresh(async () => {
  await load()
  uni.stopPullDownRefresh()
})
</script>

<style scoped>
.report__summary {
  border-radius: 26rpx;
  padding: 32rpx 28rpx;
  margin-bottom: 24rpx;
  box-shadow: 0 10rpx 26rpx rgba(46, 125, 50, 0.22);
}

.report__summary-title {
  color: #eaf7ec;
  font-size: 26rpx;
  margin-bottom: 22rpx;
}

.report__summary-grid {
  display: flex;
  flex-wrap: wrap;
}

.report__summary-cell {
  width: 50%;
  display: flex;
  flex-direction: column;
  margin-bottom: 18rpx;
}

.report__summary-value {
  color: #ffffff;
  font-size: 40rpx;
  font-weight: 700;
  line-height: 1.2;
}

.report__summary-label {
  color: #d7f0da;
  font-size: 22rpx;
  margin-top: 6rpx;
}

.report__unit {
  font-size: 23rpx;
  color: #8a99a8;
  font-weight: 400;
}

.report__foot {
  padding: 0 8rpx 20rpx;
}
</style>
