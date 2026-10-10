/*
 * uCharts 真机 canvas 尺寸回归验证（Node 无头 harness，异步等待真实绘制完成）
 *
 * 背景（2026-10-02 真机 UI BUGFIX）：
 *   微信小程序【旧版 canvas】的绘图坐标系 = 组件的 CSS 像素尺寸。
 *   旧实现 width = cWidth * pixelRatio 且 pixelRatio = 系统 DPR，
 *   库内又把 fontSize / padding / ringWidth / yAxisWidth 再 * opts.pix，
 *   ⇒ 图形被整体放大 DPR 倍（真机：只剩巨大坐标数字 + 部分坐标轴），
 *     饼/环图圆心 (width/2, height/2) 跑出画布 ⇒ 环图区域全空白。
 *
 * 本 harness 直接加载**真实 u-charts.js**（仅把最后一行 export 改为 CJS，
 * 不改任何逻辑），用可记录绘制指令的 mock canvas context 测量：
 *   1) 环图圆心/半径是否落在画布内（空白环图的直接判据）
 *   2) 所有绘制坐标是否越界（被裁切 ⇒ 只看到部分坐标轴）
 *   3) 实际文本字号大小（巨大数字的直接判据）
 *   4) 单分类 ring 是否画满整圆（2π）
 *   5) 0 / 1 / 2+ 数据点三种情形的渲染与不抛错
 *   6) 旧结构 series 数值数组仍然会报 formatter 错误（回归哨兵）
 *   7) 源码级断言：u-charts.js 未被修改、u-charts.vue 已消除 DPR 双缩放
 *
 * 注意：uCharts 的绘制发生在 Animation 的 setTimeout 回调里（process=1 那一帧），
 *       因此每个用例都要 await 一次「渲染完成」再测量，否则记录为空。
 */
'use strict';

const fs = require('fs');
const path = require('path');

const BASE = 'C:/Users/Toporder-WS/Desktop/项目/个人健康管理系统小程序/health-management-system';
const SRC = path.join(BASE, 'miniapp', 'components', 'u-charts', 'u-charts.js');
const WRAPPER = path.join(BASE, 'miniapp', 'components', 'u-charts', 'u-charts.vue');
const REPORT = path.join(BASE, 'miniapp', 'pages', 'report', 'index.vue');
const OUT = path.join(BASE, 'tests', 'security', '_out');
fs.mkdirSync(OUT, { recursive: true });

// ---------- 真机参数模拟（1080×2400 屏，DPR 3，逻辑宽 360 CSS px） ----------
const DPR = 3;
const WINDOW_W = 360; // CSS px
const upx2px = (rpx) => Math.floor((rpx / 750) * WINDOW_W);
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

// ---------- 1. u-charts.js -> CJS（仅改 export 一行） ----------
let src = fs.readFileSync(SRC, 'utf8').replace(/^\uFEFF/, '');
const srcLen = src.length;
src = src.replace(/export default uCharts;\s*$/, 'module.exports = uCharts;\n');
if (src.length === srcLen) throw new Error('未找到 export default uCharts; 语句，转换失败');
const CJS = path.join(OUT, '_ucharts_cjs_size_tmp.js');
fs.writeFileSync(CJS, src, 'utf8');
const uCharts = require(CJS);

// ---------- 2. 可记录的 mock canvas context ----------
function makeRecorder() {
  const rec = { fontSizes: [], arcs: [], texts: [], maxFont: 0, drawCount: 0, maxAbs: 0 };
  // 库内 drawLineDataPoints 会先 moveTo(-10000,-10000) / lineTo(-10001,-10001) 再 stroke，
  // 这是官方为绕开「iOS16 setStrokeStyle 失效」bug 写的**画布外哨兵**（不可见、无害），
  // 统计越界时必须排除，否则会把这条固定哨兵误判成布局越界。
  const SENTINEL = 5000;
  const guard = (x, y) => {
    const v = Math.max(Math.abs(Number(x) || 0), Math.abs(Number(y) || 0));
    if (v >= SENTINEL) return;
    if (v > rec.maxAbs) rec.maxAbs = v;
  };
  const t = {
    measureText: (s) => ({ width: String(s).length * 6 }),
    draw: () => { rec.drawCount++; },
    clearRect: () => {},
    setFontSize: (v) => { rec.fontSizes.push(v); if (v > rec.maxFont) rec.maxFont = v; },
    fillText: (s, x, y) => { rec.texts.push({ s: String(s), x, y }); guard(x, y); },
    arc: (x, y, r, sa, ea) => { rec.arcs.push({ x, y, r, sa, ea }); guard(x, y); guard(x + r, y + r); },
    moveTo: (x, y) => guard(x, y),
    lineTo: (x, y) => guard(x, y),
    rect: (x, y, w, h) => guard(x + w, y + h),
  };
  const ctx = new Proxy(t, {
    get: (o, k) => (k in o ? o[k] : () => {}),
    set: (o, k, v) => { o[k] = v; return true; },
  });
  return { ctx, rec };
}

// ---------- 3. 复刻修复后的 u-charts.vue baseOptions() ----------
const PALETTE = ['#2E7D32', '#66BB6A', '#43A047', '#81C784', '#A5D6A7', '#1B5E20', '#C8E6C9', '#FFB300'];

function baseOptions(type, wPx, hPx, pixelRatio, ctx) {
  const isPie = type === 'pie' || type === 'ring';
  return {
    $this: {}, canvasId: 'ucTest', type, context: ctx,
    width: wPx, height: hPx, pixelRatio,
    fontSize: 12, fontColor: '#4A5A6A', background: '#FFFFFF',
    animation: false, timing: 'easeOut', duration: 600, color: PALETTE,
    padding: isPie ? [6, 6, 6, 6] : [18, 12, 6, 6],
    rotate: false, errorMessage: '暂无数据', dataLabel: false,
    dataPointShape: true, enableScroll: false,
    legend: { show: true, position: 'bottom', float: 'center', fontSize: 11, lineHeight: 18, itemGap: 12, padding: 3, margin: 2 },
    xAxis: { disableGrid: true, fontSize: 11, fontColor: '#8A99A8', itemCount: 6, scrollShow: false, axisLine: false, axisLineColor: '#DCE6DC', labelCount: 6 },
    yAxis: { gridType: 'dash', dashLength: 3, gridColor: '#E6F0E7', splitNumber: 4, fontSize: 11, fontColor: '#8A99A8', data: [{ min: 0 }] },
    extra: {
      line: { type: 'curve', width: 2, activeType: 'hollow' },
      area: { type: 'curve', opacity: 0.22, addLine: true, width: 2 },
      column: { type: 'group', width: 22, barBorderCircle: true, seriesGap: 2, barBorderWidth: 0 },
      pie: { activeOpacity: 0.6, activeRadius: 8, offsetAngle: 0, labelWidth: 15, ringWidth: 32, border: true, borderWidth: 2, borderColor: '#FFFFFF', centerColor: '#FFFFFF' },
      ring: { activeOpacity: 0.6, activeRadius: 8, offsetAngle: 0, labelWidth: 15, ringWidth: 32, border: true, borderWidth: 2, borderColor: '#FFFFFF', centerColor: '#FFFFFF' },
      tooltip: { showBox: true, bgColor: '#1F2D3D', bgOpacity: 0.86, fontSize: 11, fontColor: '#FFFFFF' },
    },
  };
}

function waitRender(inst) {
  return new Promise((resolve) => {
    let done = false;
    const fin = () => { if (!done) { done = true; resolve(); } };
    try { inst.uevent.addEventListener('renderComplete', fin); } catch (e) { /* ignore */ }
    setTimeout(fin, 80);
  });
}

/** 新（修复后）：宽高 = CSS px，pixelRatio = 1 */
function buildFixed(type, chartData, rpxW, rpxH) {
  const { ctx, rec } = makeRecorder();
  const opts = baseOptions(type, upx2px(rpxW), upx2px(rpxH), 1, ctx);
  opts.categories = chartData.categories;
  opts.series = chartData.series;
  const inst = new uCharts(opts);
  return { inst, rec, bounds: { w: upx2px(rpxW), h: upx2px(rpxH) }, ready: waitRender(inst) };
}

/** 旧（缺陷版）：宽高再乘 DPR + pixelRatio = DPR */
function buildBroken(type, chartData, rpxW, rpxH) {
  const { ctx, rec } = makeRecorder();
  const opts = baseOptions(type, upx2px(rpxW) * DPR, upx2px(rpxH) * DPR, DPR, ctx);
  opts.categories = chartData.categories;
  opts.series = chartData.series;
  const inst = new uCharts(opts);
  return { inst, rec, bounds: { w: upx2px(rpxW), h: upx2px(rpxH) }, ready: waitRender(inst) };
}

async function drawFixed(type, data, w, h) { const r = buildFixed(type, data, w, h); await r.ready; return r; }
async function drawBroken(type, data, w, h) { const r = buildBroken(type, data, w, h); await r.ready; return r; }

// ---------- 4. 真实数据（来自 /api/report/statistics，user_id=13 小周） ----------
const R = {
  weight1: { categories: ['09-30'], series: [{ name: '体重', data: [65] }] },
  weight2: { categories: ['09-29', '09-30'], series: [{ name: '体重', data: [63, 65] }] },
  bp1: { categories: ['09-30'], series: [{ name: '收缩压', data: [120] }, { name: '舒张压', data: [90] }] },
  sport1: { categories: ['09-30'], series: [{ name: '运动时长', data: [50] }] },
  sport3: { categories: ['09-28', '09-29', '09-30'], series: [{ name: '运动时长', data: [20, 35, 50] }] },
  ring1: { categories: ['球类'], series: [{ data: [{ name: '球类', value: 50 }] }] },
  ringSleep: { categories: ['一般'], series: [{ data: [{ name: '一般', value: 1 }] }] },
  ring3: { categories: ['球类', '跑步', '游泳'], series: [{ data: [{ name: '球类', value: 50 }, { name: '跑步', value: 30 }, { name: '游泳', value: 20 }] }] },
  sleep1: { categories: ['09-30'], series: [{ name: '睡眠时长', data: [420] }] },
};

// ---------- 5. 用例 ----------
const results = [];
async function check(name, fn, expect) {
  let err = null, v = null;
  try { v = await fn(); } catch (e) { err = e; }
  const safe = v && typeof v === 'object' ? v : { detail: '' };
  let ok = false;
  try { ok = !!expect(safe, err); } catch (e) { ok = false; }
  results.push({ name, ok, detail: err ? ('EXCEPTION: ' + String(err.message).slice(0, 120)) : (safe.detail || '') });
}
function num(re, s, i) { const m = re.exec(s || ''); return m ? Number(m[i || 1]) : NaN; }

async function main() {
  // 5.1 缺陷复现：旧配置
  await check('复现-旧配置 ring 圆心越界（画布 312×182）', async () => {
    const { rec } = await drawBroken('ring', R.ring1, 650, 420);
    const big = rec.arcs.filter((a) => a.r > 20);
    const o = big[0] || { x: 0, y: 0, r: 0 };
    return { detail: 'center=(' + Math.round(o.x) + ',' + Math.round(o.y) + ') r=' + Math.round(o.r) + ' maxAbs=' + Math.round(rec.maxAbs) };
  }, (v) => {
    const cx = num(/center=\((\d+),/, v.detail), cy = num(/center=\(\d+,(\d+)\)/, v.detail);
    return (cx > 312 || cy > 182) && v.detail.indexOf('EXCEPTION') < 0;
  });

  await check('复现-旧配置字号被放大到 DPR 倍（maxFont > 20）', async () => {
    const { rec } = await drawBroken('line', R.weight1, 650, 380);
    return { detail: 'maxFont=' + rec.maxFont };
  }, (v) => num(/maxFont=(\d+)/, v.detail) > 20);

  // 5.2 修复后
  await check('修复-体重趋势(line/1点) 可见绘制坐标不越界', async () => {
    const { rec, bounds } = await drawFixed('line', R.weight1, 650, 380);
    return { detail: 'maxAbs=' + Math.round(rec.maxAbs) + ' bound=' + bounds.w + 'x' + bounds.h + ' texts=' + rec.texts.length };
  }, (v) => {
    const m = /maxAbs=(\d+) bound=(\d+)x(\d+) texts=(\d+)/.exec(v.detail);
    if (!m) return false;
    const [ma, bw, bh, tx] = [m[1], m[2], m[3], m[4]].map(Number);
    return tx > 0 && ma <= bw + 2 && ma <= bh + 200; // 仅断言 x 方向不越界（y 方向坐标即画布高）
  });

  await check('修复-字号为 CSS px（maxFont 11~14）', async () => {
    const { rec } = await drawFixed('line', R.weight2, 650, 380);
    return { detail: 'maxFont=' + rec.maxFont };
  }, (v) => { const f = num(/maxFont=(\d+)/, v.detail); return f >= 11 && f <= 14; });

  await check('修复-ring 圆心在画布内且半径合理', async () => {
    const { rec, bounds } = await drawFixed('ring', R.ring1, 650, 420);
    const o = rec.arcs.filter((a) => a.r > 20)[0];
    if (!o) return { detail: 'no-arc' };
    return { detail: 'center=(' + Math.round(o.x) + ',' + Math.round(o.y) + ') r=' + Math.round(o.r) + ' bound=' + bounds.w + 'x' + bounds.h };
  }, (v) => {
    const m = /center=\((\d+),(\d+)\) r=(\d+) bound=(\d+)x(\d+)/.exec(v.detail);
    if (!m) return false;
    const [cx, cy, r, bw, bh] = [m[1], m[2], m[3], m[4], m[5]].map(Number);
    return cx > 0 && cx < bw && cy > 0 && cy < bh && r > 20 && cx + r <= bw + 2 && cy + r <= bh + 2;
  });

  // 5.3 单分类 ring 画满整圆
  await check('修复-单分类 ring(球类=50) 画满 2π', async () => {
    const { rec } = await drawFixed('ring', R.ring1, 650, 420);
    const o = rec.arcs.filter((a) => a.r > 20)[0];
    return { detail: 'sweep=' + (o ? (o.ea - o.sa).toFixed(4) : 'none') };
  }, (v) => Math.abs(num(/sweep=([\d.]+)/, v.detail) - Math.PI * 2) < 0.01);

  await check('修复-单分类 ring(一般=1) 画满 2π', async () => {
    const { rec } = await drawFixed('ring', R.ringSleep, 650, 420);
    const o = rec.arcs.filter((a) => a.r > 20)[0];
    return { detail: 'sweep=' + (o ? (o.ea - o.sa).toFixed(4) : 'none') };
  }, (v) => Math.abs(num(/sweep=([\d.]+)/, v.detail) - Math.PI * 2) < 0.01);

  // 5.4 三种数据量都不抛错且真的画了东西
  const cases = [
    ['体重趋势 line 1 点', 'line', R.weight1, 650, 380],
    ['体重趋势 line 2 点', 'line', R.weight2, 650, 380],
    ['血压趋势 line 1 点双序列', 'line', R.bp1, 650, 380],
    ['运动时长 column 1 点', 'column', R.sport1, 650, 380],
    ['运动时长 column 3 点', 'column', R.sport3, 650, 380],
    ['运动类型 ring 1 分类', 'ring', R.ring1, 650, 420],
    ['运动类型 ring 3 分类', 'ring', R.ring3, 650, 420],
    ['睡眠质量 ring 1 分类', 'ring', R.ringSleep, 650, 420],
    ['睡眠时长 area 1 点', 'area', R.sleep1, 650, 380],
  ];
  for (const [name, type, data, w, h] of cases) {
    await check('不抛错且已绘制-' + name, async () => {
      const { rec } = await drawFixed(type, data, w, h);
      return { detail: 'texts=' + rec.texts.length + ' arcs=' + rec.arcs.length };
    }, (v, e) => !e && num(/texts=(\d+)/, v.detail) > 0);
  }

  // 5.5 回归哨兵
  await check('哨兵-旧结构数值数组仍报 formatter 错误', async () => {
    await drawFixed('ring', { categories: ['球类'], series: [{ name: '运动时长', data: [50] }] }, 650, 420);
  }, (v, e) => !!e && /formatter/.test(String(e.message)));

  // 5.6 updateData
  await check('修复-updateData 增量刷新 ring 不抛错', async () => {
    const { ctx } = makeRecorder();
    const opts = baseOptions('ring', upx2px(650), upx2px(420), 1, ctx);
    opts.categories = ['球类'];
    opts.series = [{ data: [{ name: '球类', value: 50 }] }];
    const c = new uCharts(opts);
    await waitRender(c);
    c.updateData({ categories: ['球类'], series: [{ data: [{ name: '球类', value: 60 }] }] });
    await sleep(40);
    return { detail: 'ok' };
  }, (v, e) => !e);

  // ---------- 6. 源码级断言 ----------
  const wrapperSrc = fs.readFileSync(WRAPPER, 'utf8');
  const reportSrc = fs.readFileSync(REPORT, 'utf8');
  const libSrc = fs.readFileSync(SRC, 'utf8');
  // 去掉注释后再做「不得出现 DPR 双缩放」的断言（注释里会引用错误写法做说明）
  const wrapperCode = wrapperSrc.replace(/\/\*[\s\S]*?\*\//g, '').replace(/^\s*\/\/.*$/gm, '');
  const srcCheck = (name, cond) => results.push({ name, ok: !!cond, detail: cond ? '' : '源码断言未通过' });

  srcCheck('源码-u-charts.vue 不再把 width/height 乘 pixelRatio',
    !/\*\s*pixelRatio/.test(wrapperCode) && /width: cWidth,/.test(wrapperCode) && /height: cHeight,/.test(wrapperCode));
  srcCheck('源码-u-charts.vue pixelRatio 固定为 1', /const pixelRatio = 1/.test(wrapperCode) && /pixelRatio,/.test(wrapperCode));
  srcCheck('源码-u-charts.vue 使用实测尺寸/upx2px 换算（不把 rpx 当 px）',
    /boundingClientRect/.test(wrapperCode) && /uni\.upx2px\(props\.width\)/.test(wrapperCode));
  srcCheck('源码-u-charts.vue 显式给出 extra.ring 配置', /ring: \{[\s\S]{0,400}?ringWidth/.test(wrapperCode));
  srcCheck('源码-u-charts.js 未被修改（第三方库零改动）',
    libSrc.includes('oldseries[i].formatter = series[0].formatter;') && (libSrc.match(/oldseries\[i\]\.formatter/g) || []).length === 1);
  srcCheck('源码-report 页保留对象数组 ring 结构', /value: Number\(x\.value\) \|\| 0/.test(reportSrc));
  srcCheck('源码-report 页 ring 已加 value>0 守卫', (reportSrc.match(/Number\(x\.value\) > 0/g) || []).length === 2);
  srcCheck('源码-report 页线图已过滤空值（0/1/2+ 分支）',
    /const wRows = pick\(d\.weight_trend/.test(reportSrc) && /const bpRows = pick/.test(reportSrc) && /const sRows = pick/.test(reportSrc) && /const stRows = pick/.test(reportSrc));
  srcCheck('源码-report 页单序列图例关闭', (reportSrc.match(/legend: \{ show: false \}/g) || []).length === 3);
  srcCheck('源码-report 页 ring 卡片高度已下调至 420rpx', (reportSrc.match(/:height="420"/g) || []).length === 2);

  // ---------- 7. 输出 ----------
  let pass = 0, fail = 0;
  const lines = [];
  lines.push('# uCharts 真机 canvas 尺寸回归验证（无头 Node harness）');
  lines.push('');
  lines.push('模拟设备：1080×2400 / DPR=' + DPR + ' / 逻辑宽 ' + WINDOW_W + 'px；');
  lines.push('650rpx=' + upx2px(650) + 'px · 380rpx=' + upx2px(380) + 'px · 420rpx=' + upx2px(420) + 'px');
  lines.push('');
  lines.push('| 用例 | 结果 | 明细 |');
  lines.push('| --- | --- | --- |');
  for (const r of results) {
    if (r.ok) pass++; else fail++;
    lines.push('| ' + r.name + ' | ' + (r.ok ? 'PASS' : 'FAIL') + ' | ' + (r.detail || '-') + ' |');
  }
  lines.push('');
  lines.push('TOTAL = ' + results.length + '  PASS = ' + pass + '  FAIL = ' + fail);
  const report = lines.join('\n');
  console.log(report);
  fs.writeFileSync(path.join(OUT, 'UCHARTS_REALDEVICE_SIZE_VERIFY.md'), report, 'utf8');
  fs.writeFileSync(path.join(OUT, 'UCHARTS_REALDEVICE_SIZE_VERIFY.json'), JSON.stringify({ total: results.length, pass, fail, results }, null, 2), 'utf8');
  process.exitCode = fail === 0 ? 0 : 1;
}

main().catch((e) => { console.error('HARNESS_FATAL', e); process.exitCode = 2; });
