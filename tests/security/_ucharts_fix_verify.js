/*
 * uCharts 饼/环图 series 结构回归验证（Node 无头 harness，不依赖微信开发者工具）。
 *
 * 目的：
 *  1) 复现真机 Report 页的运行时错误：MiniProgramError: Cannot create property 'formatter' on number
 *     —— 触发帧 fixPieSeries ← drawCharts ← new uCharts
 *  2) 证明修复后（series[0].data 改为 [{name, value}] 对象数组）不再抛出
 *  3) 证明 line / column / area 三种既有结构未受影响
 *
 * 做法：把 u-charts.js 原样转成 CJS（仅改最后一行 export 语句），
 *       用 mock canvas context 直接 new uCharts(opts)，捕获异常。
 *       —— 不修改第三方库源码。
 */
'use strict';

const fs = require('fs');
const os = require('os');
const path = require('path');

const BASE = 'C:/Users/Toporder-WS/Desktop/项目/个人健康管理系统小程序/health-management-system';
const SRC = path.join(BASE, 'miniapp', 'components', 'u-charts', 'u-charts.js');
const OUT = path.join(BASE, 'tests', 'security', '_out');
fs.mkdirSync(OUT, { recursive: true });

// ---------- 1. u-charts.js -> CJS（只在临时副本上改 export 一行） ----------
let src = fs.readFileSync(SRC, 'utf8').replace(/^\uFEFF/, '');
const before = src.length;
src = src.replace(/export default uCharts;\s*$/, 'module.exports = uCharts;\n');
if (src.length === before) throw new Error('未找到 export default uCharts; 语句，转换失败');
const CJS = path.join(OUT, '_ucharts_cjs_tmp.js');
fs.writeFileSync(CJS, src, 'utf8');
const uCharts = require(CJS);

// ---------- 2. mock canvas context ----------
function makeCtx() {
  const t = {
    measureText: (s) => ({ width: String(s).length * 6 }),
    draw: () => {},
    setFontSize: () => {},
    setFillStyle: () => {},
    setStrokeStyle: () => {},
    setLineWidth: () => {},
    setLineCap: () => {},
    setTextAlign: () => {},
    setTextBaseline: () => {},
    setShadow: () => {},
    setLineDash: () => {},
    createCircularGradient: () => ({ addColorStop: () => {} }),
    createRadialGradient: () => ({ addColorStop: () => {} }),
    createLinearGradient: () => ({ addColorStop: () => {} }),
  };
  return new Proxy(t, {
    get: (o, k) => (k in o ? o[k] : () => {}),
    set: (o, k, v) => { o[k] = v; return true; },
  });
}

// ---------- 3. 复刻 miniapp/components/u-charts/u-charts.vue 的 baseOptions() ----------
const PALETTE = ['#2E7D32', '#66BB6A', '#43A047', '#81C784', '#A5D6A7', '#1B5E20', '#C8E6C9', '#FFB300'];

function baseOptions(type, w, h) {
  const isPie = type === 'pie' || type === 'ring';
  return {
    $this: {},
    canvasId: 'ucTest',
    type,
    context: makeCtx(),
    width: w,
    height: h,
    pixelRatio: 2,
    fontSize: 11,
    fontColor: '#4A5A6A',
    background: '#FFFFFF',
    animation: false,
    timing: 'easeOut',
    duration: 600,
    color: PALETTE,
    padding: isPie ? [5, 5, 5, 5] : [16, 14, 4, 6],
    rotate: false,
    errorMessage: '暂无数据',
    dataLabel: false,
    dataPointShape: true,
    enableScroll: false,
    legend: { show: true, position: 'bottom', float: 'center', fontSize: 11, lineHeight: 22, itemGap: 14, padding: 4 },
    xAxis: { disableGrid: true, fontSize: 10, fontColor: '#8A99A8', itemCount: 6, scrollShow: false, axisLine: false, axisLineColor: '#DCE6DC', labelCount: 6 },
    yAxis: { gridType: 'dash', dashLength: 3, gridColor: '#E6F0E7', splitNumber: 4, fontSize: 10, fontColor: '#8A99A8', data: [{ min: 0 }] },
    extra: {
      line: { type: 'curve', width: 2, activeType: 'hollow' },
      area: { type: 'curve', opacity: 0.22, addLine: true, width: 2 },
      column: { type: 'group', width: 24, barBorderCircle: true, seriesGap: 2, barBorderWidth: 0 },
      pie: { activeOpacity: 0.6, activeRadius: 8, offsetAngle: 0, labelWidth: 14, border: true, borderWidth: 2, borderColor: '#FFFFFF', ringWidth: 34 },
      tooltip: { showBox: true, bgColor: '#1F2D3D', bgOpacity: 0.86, fontSize: 11, fontColor: '#FFFFFF' },
    },
  };
}

function draw(type, chartData, w, h) {
  const opts = baseOptions(type, (w || 650) * 2, (h || 420) * 2);
  opts.categories = chartData.categories;
  opts.series = chartData.series;
  return new uCharts(opts);
}

// ---------- 4. 真实数据（来自 /api/report/statistics，user_id=13 小周） ----------
const REAL_SPORT_BY_TYPE = [{ name: '球类', value: 50, calorie: 320 }];
const REAL_SLEEP_QUALITY = [{ name: '一般', value: 1 }];

const results = [];
function check(name, fn, expectThrow) {
  let err = null, v = null;
  try { v = fn(); } catch (e) { err = e; }
  const threw = !!err;
  const ok = expectThrow ? threw : !threw;
  results.push({ name, expectThrow, threw, ok, msg: err ? String(err.message).slice(0, 160) : '' });
}

// A. 旧结构（数值数组）—— 必须复现报错
check('旧结构 ring: series=[{name,data:[50]}]（应报 formatter 错误）',
  () => draw('ring', { categories: ['球类'], series: [{ name: '运动时长', data: [50] }] }, 650, 460), true);
check('旧结构 ring: series=[{name,data:[1]}]（应报 formatter 错误）',
  () => draw('ring', { categories: ['一般'], series: [{ name: '次数', data: [1] }] }, 650, 460), true);

// B. 新结构（ECharts 兼容对象数组）—— 必须无异常
check('新结构 ring 运动类型分布（真实数据 50）',
  () => draw('ring', { categories: REAL_SPORT_BY_TYPE.map((x) => x.name), series: [{ data: REAL_SPORT_BY_TYPE.map((x) => ({ name: x.name, value: x.value })) }] }, 650, 460), false);
check('新结构 ring 睡眠质量占比（真实数据 1）',
  () => draw('ring', { categories: REAL_SLEEP_QUALITY.map((x) => x.name), series: [{ data: REAL_SLEEP_QUALITY.map((x) => ({ name: x.name, value: x.value })) }] }, 650, 460), false);
check('新结构 ring 多分片（3 段）',
  () => draw('ring', { categories: ['球类', '跑步', '游泳'], series: [{ data: [{ name: '球类', value: 50 }, { name: '跑步', value: 30 }, { name: '游泳', value: 20 }] }] }, 650, 460), false);
check('新结构 ring 全 0 值（count=0 分支）',
  () => draw('ring', { categories: ['a', 'b'], series: [{ data: [{ name: 'a', value: 0 }, { name: 'b', value: 0 }] }] }, 650, 460), false);
check('新结构 pie 单分片',
  () => draw('pie', { categories: ['x'], series: [{ data: [{ name: 'x', value: 7 }] }] }, 650, 420), false);

// C. 非饼图结构不得回归
check('line（体重趋势）', () => draw('line', { categories: ['10-01'], series: [{ name: '体重', data: [62.5] }] }, 650, 420), false);
check('line（血压双系列）', () => draw('line', { categories: ['10-01'], series: [{ name: '收缩压', data: [120] }, { name: '舒张压', data: [80] }] }, 650, 440), false);
check('column（运动时长按天）', () => draw('column', { categories: ['10-01'], series: [{ name: '运动时长', data: [50] }] }, 650, 420), false);
check('area（睡眠时长趋势）', () => draw('area', { categories: ['10-01'], series: [{ name: '睡眠时长', data: [420] }] }, 650, 420), false);

// D. updateData 增量刷新（ECharts 结构）不得报错
check('updateData 增量刷新 ring', () => {
  const opts = baseOptions('ring', 1300, 920);
  opts.categories = ['球类'];
  opts.series = [{ data: [{ name: '球类', value: 50 }] }];
  const c = new uCharts(opts);
  c.updateData({ categories: ['球类'], series: [{ data: [{ name: '球类', value: 60 }] }] });
  return c;
}, false);

// ---------- 5. 输出 ----------
let pass = 0, fail = 0;
const lines = [];
lines.push('# uCharts 饼/环图 series 结构回归验证（无头 Node harness）');
lines.push('');
lines.push('| 用例 | 预期 | 实际 | 结果 | 异常信息 |');
lines.push('| --- | --- | --- | --- | --- |');
for (const r of results) {
  if (r.ok) pass++; else fail++;
  lines.push('| ' + r.name + ' | ' + (r.expectThrow ? '抛错' : '不抛错') + ' | ' + (r.threw ? '抛错' : '不抛错') + ' | ' + (r.ok ? 'PASS' : 'FAIL') + ' | ' + (r.msg || '-') + ' |');
}
lines.push('');
lines.push('TOTAL = ' + results.length + '  PASS = ' + pass + '  FAIL = ' + fail);

const report = lines.join('\n');
console.log(report);
fs.writeFileSync(path.join(OUT, 'UCHARTS_SERIES_VERIFY.md'), report, 'utf8');
fs.writeFileSync(path.join(OUT, 'UCHARTS_SERIES_VERIFY.json'), JSON.stringify({ total: results.length, pass, fail, results }, null, 2), 'utf8');

process.exitCode = fail === 0 ? 0 : 1;
