# -*- coding: utf-8 -*-
"""
真机 UI BUGFIX 补丁脚本（锚点式，逐条断言命中恰 1 次；任一未命中 ⇒ 整个文件不改）

目标文件：
  - miniapp/pages/report/index.vue   数据报告页（图表卡片高度 / 单序列图例 / 空数据守卫 / null 过滤）
  - miniapp/pages/index/index.vue    首页（HTML 实体显示「更多 >」→「更多 ›」/ Hero 间距收紧）

默认 dry-run；--apply 才写盘。
"""
import io
import os
import sys

BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
APPLY = '--apply' in sys.argv

REPORT = os.path.join(BASE, 'miniapp', 'pages', 'report', 'index.vue')
INDEX = os.path.join(BASE, 'miniapp', 'pages', 'index', 'index.vue')

report_patches = []


def R(old, new, tag):
    report_patches.append((old, new, tag))


# ---------- 1) 体重趋势：高度 420→380，单序列隐藏图例 ----------
R(
    '          :chart-data="weightData"\n          :height="420"\n          :opts="{ yAxis: { data: [{ min: weightMin }] } }"\n',
    '          :chart-data="weightData"\n          :height="380"\n          :opts="{ legend: { show: false }, yAxis: { data: [{ min: weightMin }] } }"\n',
    'weight-card',
)

# ---------- 2) 血压趋势：高度 440→380（两条序列保留图例） ----------
R(
    '          chart-id="ucBp"\n          type="line"\n          unit="mmHg"\n          :chart-data="bpData"\n          :height="440"\n',
    '          chart-id="ucBp"\n          type="line"\n          unit="mmHg"\n          :chart-data="bpData"\n          :height="380"\n',
    'bp-card',
)

# ---------- 3) 运动时长：高度 420→380，单序列隐藏图例 ----------
R(
    '          chart-id="ucSport"\n          type="column"\n          unit="分钟"\n          :chart-data="sportData"\n          :height="420"\n',
    '          chart-id="ucSport"\n          type="column"\n          unit="分钟"\n          :chart-data="sportData"\n          :height="380"\n          :opts="{ legend: { show: false } }"\n',
    'sport-card',
)

# ---------- 4) 运动类型分布 ring：高度 460→420 ----------
R(
    '          chart-id="ucSportType"\n          type="ring"\n          unit="分钟"\n          :chart-data="sportTypeData"\n          :height="460"\n',
    '          chart-id="ucSportType"\n          type="ring"\n          unit="分钟"\n          :chart-data="sportTypeData"\n          :height="420"\n',
    'sporttype-card',
)

# ---------- 5) 睡眠质量占比 ring：高度 460→420 ----------
R(
    '          chart-id="ucSleepQuality"\n          type="ring"\n          unit="次"\n          :chart-data="sleepQualityData"\n          :height="460"\n',
    '          chart-id="ucSleepQuality"\n          type="ring"\n          unit="次"\n          :chart-data="sleepQualityData"\n          :height="420"\n',
    'sleepquality-card',
)

# ---------- 6) 睡眠时长趋势 area：高度 420→380，单序列隐藏图例 ----------
R(
    '          chart-id="ucSleepTrend"\n          type="area"\n          unit="分钟"\n          :chart-data="sleepTrendData"\n          :height="420"\n',
    '          chart-id="ucSleepTrend"\n          type="area"\n          unit="分钟"\n          :chart-data="sleepTrendData"\n          :height="380"\n          :opts="{ legend: { show: false } }"\n',
    'sleeptrend-card',
)

# ---------- 7) 新增 pick() 辅助函数（放在 shortDate 之后） ----------
R(
    "/** 月份日期缩略显示，避免 X 轴标签拥挤 */\nfunction shortDate(dateStr) {\n  return String(dateStr || '').slice(5)\n}\n",
    "/** 月份日期缩略显示，避免 X 轴标签拥挤 */\nfunction shortDate(dateStr) {\n  return String(dateStr || '').slice(5)\n}\n\n"
    "/**\n"
    " * 只保留某字段确实带数值的记录：\n"
    " * null / undefined / '' / NaN 一律剔除，避免被 Number() 折成 0 混进真实数据。\n"
    " * 这样 0 条 → 空状态、1 条 → 单点、2 条以上 → 正常趋势，三种情况都走自然分支。\n"
    " */\n"
    "function pick(list, key) {\n"
    "  return (list || []).filter(\n"
    "    (x) => x && x[key] !== null && x[key] !== undefined && x[key] !== '' && !Number.isNaN(Number(x[key]))\n"
    "  )\n"
    "}\n",
    'pick-helper',
)

# ---------- 8) 三条 line/area 序列改用 pick() ----------
R(
    "    weightData.value = {\n"
    "      categories: (d.weight_trend || []).map((x) => shortDate(x.date)),\n"
    "      series: [{ name: '体重', data: (d.weight_trend || []).map((x) => x.weight) }],\n"
    "    }\n"
    "\n"
    "    bpData.value = {\n"
    "      categories: (d.blood_pressure_trend || []).map((x) => shortDate(x.date)),\n"
    "      series: [\n"
    "        { name: '收缩压', data: (d.blood_pressure_trend || []).map((x) => x.high) },\n"
    "        { name: '舒张压', data: (d.blood_pressure_trend || []).map((x) => x.low) },\n"
    "      ],\n"
    "    }\n"
    "\n"
    "    sportData.value = {\n"
    "      categories: (d.sport_daily || []).map((x) => shortDate(x.date)),\n"
    "      series: [{ name: '运动时长', data: (d.sport_daily || []).map((x) => x.duration) }],\n"
    "    }\n",
    "    const wRows = pick(d.weight_trend, 'weight')\n"
    "    weightData.value = {\n"
    "      categories: wRows.map((x) => shortDate(x.date)),\n"
    "      series: [{ name: '体重', data: wRows.map((x) => Number(x.weight)) }],\n"
    "    }\n"
    "\n"
    "    const bpRows = pick(d.blood_pressure_trend, 'high')\n"
    "    bpData.value = {\n"
    "      categories: bpRows.map((x) => shortDate(x.date)),\n"
    "      series: [\n"
    "        { name: '收缩压', data: bpRows.map((x) => Number(x.high)) },\n"
    "        { name: '舒张压', data: bpRows.map((x) => Number(x.low) || 0) },\n"
    "      ],\n"
    "    }\n"
    "\n"
    "    const sRows = pick(d.sport_daily, 'duration')\n"
    "    sportData.value = {\n"
    "      categories: sRows.map((x) => shortDate(x.date)),\n"
    "      series: [{ name: '运动时长', data: sRows.map((x) => Number(x.duration)) }],\n"
    "    }\n",
    'line-series-pick',
)

# ---------- 9) 两个 ring：value<=0 一律剔除，全空 ⇒ 置空走空状态 ----------
R(
    "    const sportTypes = d.sport_by_type || []\n"
    "    sportTypeData.value = {\n"
    "      categories: sportTypes.map((x) => x.name),\n"
    "      series: [{ data: sportTypes.map((x) => ({ name: x.name, value: Number(x.value) || 0 })) }],\n"
    "    }\n"
    "\n"
    "    const qualities = d.sleep_quality || []\n"
    "    sleepQualityData.value = {\n"
    "      categories: qualities.map((x) => x.name),\n"
    "      series: [{ data: qualities.map((x) => ({ name: x.name, value: Number(x.value) || 0 })) }],\n"
    "    }\n"
    "\n"
    "    sleepTrendData.value = {\n"
    "      categories: (d.sleep_trend || []).map((x) => shortDate(x.date)),\n"
    "      series: [{ name: '睡眠时长', data: (d.sleep_trend || []).map((x) => x.duration) }],\n"
    "    }\n",
    "    // 只保留 value > 0 的分类；全部为 0 或没有数据时直接置空 → 走「暂无数据」空状态。\n"
    "    // （若把全 0 数据交给库，库内 count===0 会按 1/series.length 兜底，画出一个并不真实的整圆）\n"
    "    const sportTypes = (d.sport_by_type || []).filter((x) => x && Number(x.value) > 0)\n"
    "    sportTypeData.value = sportTypes.length\n"
    "      ? {\n"
    "          categories: sportTypes.map((x) => x.name),\n"
    "          series: [{ data: sportTypes.map((x) => ({ name: x.name, value: Number(x.value) || 0 })) }],\n"
    "        }\n"
    "      : { categories: [], series: [] }\n"
    "\n"
    "    const qualities = (d.sleep_quality || []).filter((x) => x && Number(x.value) > 0)\n"
    "    sleepQualityData.value = qualities.length\n"
    "      ? {\n"
    "          categories: qualities.map((x) => x.name),\n"
    "          series: [{ data: qualities.map((x) => ({ name: x.name, value: Number(x.value) || 0 })) }],\n"
    "        }\n"
    "      : { categories: [], series: [] }\n"
    "\n"
    "    const stRows = pick(d.sleep_trend, 'duration')\n"
    "    sleepTrendData.value = {\n"
    "      categories: stRows.map((x) => shortDate(x.date)),\n"
    "      series: [{ name: '睡眠时长', data: stRows.map((x) => Number(x.duration)) }],\n"
    "    }\n",
    'ring-guard',
)

index_patches = []


def I(old, new, tag):
    index_patches.append((old, new, tag))


# ---------- 10) 「更多 >」→「更多 ›」（避免编译器把 > 转义成 &gt; 后当纯文本显示） ----------
I(
    '<text class="hm-link" @tap="goArticleList">更多 ></text>',
    '<text class="hm-link" @tap="goArticleList">更多 \u203a</text>',
    'more-link-entity',
)

# ---------- 11) Hero 区收紧 ----------
I(
    '.home__header {\n  margin: -24rpx -24rpx 24rpx;\n  padding: 36rpx 32rpx 28rpx;',
    '.home__header {\n  margin: -24rpx -24rpx 20rpx;\n  padding: 26rpx 30rpx 22rpx;',
    'hero-spacing',
)
I('.home__hello {\n  color: #ffffff;\n  font-size: 34rpx;', '.home__hello {\n  color: #ffffff;\n  font-size: 32rpx;', 'hero-title')
I(
    '.home__user {\n  display: flex;\n  align-items: center;\n  justify-content: space-between;\n  margin-top: 18rpx;\n}',
    '.home__user {\n  display: flex;\n  align-items: center;\n  justify-content: space-between;\n  margin-top: 14rpx;\n}',
    'hero-user-gap',
)
I('.home__avatar {\n  width: 56rpx;\n  height: 56rpx;', '.home__avatar {\n  width: 52rpx;\n  height: 52rpx;', 'hero-avatar')
I(
    '.home__notice {\n  display: flex;\n  align-items: center;\n  margin-top: 22rpx;\n  background: rgba(255, 255, 255, 0.2);\n  border-radius: 18rpx;\n  padding: 14rpx 20rpx;\n  height: 64rpx;\n}',
    '.home__notice {\n  display: flex;\n  align-items: center;\n  margin-top: 16rpx;\n  background: rgba(255, 255, 255, 0.2);\n  border-radius: 18rpx;\n  padding: 12rpx 18rpx;\n  height: 58rpx;\n}',
    'hero-notice',
)
I('.overview__value {\n  font-size: 38rpx;', '.overview__value {\n  font-size: 34rpx;', 'overview-value')
I(
    '.home {\n  padding-top: 0;\n}',
    '.home {\n  padding-top: 0;\n}\n\n/* 首页卡片标题更紧凑（仅作用于首页，不改全局 .hm-card__title 规则） */\n.home .hm-card__title {\n  margin-bottom: 16rpx;\n}',
    'home-card-title',
)


def apply(path, patches, label):
    with open(path, 'rb') as f:
        raw = f.read()
    text = raw.decode('utf-8')
    crlf = '\r\n' in text
    norm = text.replace('\r\n', '\n')
    out = norm
    ok = True
    print('==== %s (%s, %d bytes, %s) ====' % (label, os.path.basename(path), len(raw), 'CRLF' if crlf else 'LF'))
    for old, new, tag in patches:
        n = out.count(old)
        status = 'OK ' if n == 1 else 'FAIL'
        if n != 1:
            ok = False
        print('  [%s] %-20s hit=%d' % (status, tag, n))
    if not ok:
        print('  => 存在未命中锚点，本文件不做任何修改')
        return False
    for old, new, tag in patches:
        out = out.replace(old, new, 1)
    if crlf:
        out = out.replace('\n', '\r\n')
    if APPLY:
        with open(path, 'wb') as f:
            f.write(out.encode('utf-8'))
        print('  => APPLIED, %d -> %d bytes' % (len(raw), len(out.encode('utf-8'))))
    else:
        print('  => DRY-RUN OK（预计 %d -> %d bytes）' % (len(raw), len(out.encode('utf-8'))))
    return True


a = apply(REPORT, report_patches, 'REPORT')
b = apply(INDEX, index_patches, 'HOME')
print()
print('MODE =', 'APPLY' if APPLY else 'DRY-RUN')
print('RESULT =', 'BOTH_OK' if (a and b) else 'HAS_FAILURE')
