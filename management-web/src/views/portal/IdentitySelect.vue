<template>
  <div class="portal">
    <!-- 背景层：CSS 自然风景渐变兜底（蓝天 / 山脉 / 湖泊 / 森林） -->
    <div class="portal__bg" aria-hidden="true"></div>
    <!-- 可选本地实景背景图：放入 src/assets/images/health-portal-bg.jpg 后自动生效 -->
    <img v-if="bgUrl" class="portal__bg-photo" :src="bgUrl" alt="" aria-hidden="true" />
    <!-- 提亮遮罩：保证浅色背景下文字对比度 -->
    <div class="portal__bg-veil" aria-hidden="true"></div>
    <!-- 轻动态背景装饰层（纯 CSS：云层漂移 / 阳光呼吸 / 湖面微光）；全层 pointer-events:none，不拦截点击 -->
    <div class="portal__fx" aria-hidden="true">
      <span class="portal__cloud portal__cloud--1"></span>
      <span class="portal__cloud portal__cloud--2"></span>
      <span class="portal__cloud portal__cloud--3"></span>
      <span class="portal__sun"></span>
      <span class="portal__shine"></span>
    </div>

    <header class="portal__header">
      <div class="portal__brand">
        <span class="portal__logo">
          <el-icon><FirstAidKit /></el-icon>
        </span>
        <span class="portal__brand-text">
          <strong class="portal__brand-title">个人健康管理系统</strong>
          <em class="portal__brand-sub">Personal Health Management System</em>
        </span>
      </div>

      <nav class="portal__nav" aria-label="顶部导航">
        <span class="portal__nav-item">关于我们</span>
        <span class="portal__nav-item">帮助中心</span>
        <span class="portal__nav-item">联系我们</span>
        <span class="portal__nav-badge">版本 V3.2</span>
      </nav>
    </header>

    <main class="portal__main">
      <section class="portal__hero">
        <h1 class="portal__hero-title">
          健康生活 · 从记录<span class="portal__hero-accent">开始</span>
        </h1>
        <p class="portal__hero-sub">科学记录 · 数据分析 · 目标管理 · 习惯养成</p>
        <p class="portal__hero-tip">让健康管理更简单、更专业、更持久</p>
      </section>

      <p class="portal__pick">请选择要进入的身份</p>

      <section class="portal__cards">
        <article
          v-for="item in identities"
          :key="item.role"
          class="portal__card"
          :style="{ '--card-accent': item.theme.accent, '--card-soft': item.theme.soft }"
          @click="enter(item)"
        >
          <div class="portal__card-avatar">
            <img
              v-if="item.avatar"
              class="portal__card-avatar-img"
              :src="item.avatar"
              alt=""
            />
            <el-icon v-else class="portal__card-avatar-icon">
              <component :is="item.icon" />
            </el-icon>
          </div>

          <h2 class="portal__card-name">{{ item.label }}端</h2>
          <p class="portal__card-desc">{{ item.desc }}</p>

          <button
            type="button"
            class="portal__card-btn"
            :style="{ background: item.theme.gradient }"
            @click.stop="enter(item)"
          >
            <span>进入{{ item.label }}端</span>
            <el-icon class="portal__card-btn-icon"><ArrowRight /></el-icon>
          </button>
        </article>
      </section>

      <section class="portal__features" aria-label="平台优势">
        <div v-for="f in features" :key="f.title" class="portal__feature">
          <span class="portal__feature-icon">
            <el-icon><component :is="f.icon" /></el-icon>
          </span>
          <span class="portal__feature-body">
            <strong>{{ f.title }}</strong>
            <em>{{ f.desc }}</em>
          </span>
        </div>
      </section>

      <p class="portal__note">
        普通用户请使用微信小程序端记录健康数据 · 管理员账号由系统初始化，不提供注册
      </p>
    </main>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router'
import { ROLE, ROLE_META } from '@/utils/config'

/**
 * 可选本地静态资源：文件不存在时不会导致构建失败，放入后自动生效，无需改代码。
 *   src/assets/images/health-portal-bg.(jpg|jpeg|png|webp)  页面自然风景背景
 *   src/assets/images/portal-doctor.(jpg|jpeg|png|webp)     医生卡片人物图
 *   src/assets/images/portal-coach.(jpg|jpeg|png|webp)      健身教练卡片人物图
 *   src/assets/images/portal-admin.(jpg|jpeg|png|webp)      管理员卡片人物图
 * 未提供时：背景回退为 CSS 风景渐变，人物图回退为角色图标。
 */
const assetModules = import.meta.glob('../../assets/images/*.{jpg,jpeg,png,webp}', {
  eager: true,
  query: '?url',
  import: 'default',
})

function pickAsset(baseName) {
  const hit = Object.keys(assetModules).find((path) => {
    const file = path.split('/').pop().toLowerCase()
    return file.replace(/\.[a-z0-9]+$/, '') === baseName
  })
  return hit ? assetModules[hit] : ''
}

const bgUrl = pickAsset('health-portal-bg')

const identities = [
  {
    ...ROLE_META[ROLE.DOCTOR],
    role: ROLE.DOCTOR,
    icon: 'FirstAidKit',
    avatar: pickAsset('portal-doctor'),
    desc: '管理患者信息，查看健康数据\n制定健康建议与随访计划',
    theme: {
      accent: '#0FA98E',
      soft: '#DCF5EF',
      gradient: 'linear-gradient(135deg, #16C79A 0%, #0F9D8C 100%)',
    },
  },
  {
    ...ROLE_META[ROLE.COACH],
    role: ROLE.COACH,
    icon: 'Basketball',
    avatar: pickAsset('portal-coach'),
    desc: '管理学员数据，制定训练计划\n跟踪运动目标与训练进度',
    theme: {
      accent: '#1E6FFF',
      soft: '#DEEAFF',
      gradient: 'linear-gradient(135deg, #3B82F6 0%, #1E6FFF 100%)',
    },
  },
  {
    ...ROLE_META[ROLE.ADMIN],
    role: ROLE.ADMIN,
    icon: 'Setting',
    avatar: pickAsset('portal-admin'),
    desc: '账号审核，系统管理\n数据统计与内容运营',
    theme: {
      accent: '#6D4AE0',
      soft: '#EAE3FF',
      gradient: 'linear-gradient(135deg, #8B5CF6 0%, #6D4AE0 100%)',
    },
  },
]

const features = [
  { icon: 'Lock', title: '数据安全', desc: '多重加密保护' },
  { icon: 'Histogram', title: '专业分析', desc: '可视化数据图表' },
  { icon: 'Monitor', title: '多端支持', desc: '小程序 + PC 端' },
  { icon: 'Sunny', title: '助力健康', desc: '让改变看得见' },
]

const router = useRouter()

function enter(item) {
  router.push(ROLE_META[item.role].loginPath)
}
</script>

<style scoped>
.portal {
  position: relative;
  width: 100%;
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  /* 同时裁剪横纵两轴：背景装饰层（尤其 scale 呼吸层）的变换溢出不得计入文档可滚动区，
     否则会出现"垂直滚动条随动画周期出现/消失 -> 内容整体横移半个滚动条宽"的抖动。
     本页内容高度自适应（.portal 高度随内容增长），故纵轴裁剪不会吞掉任何内容。 */
  overflow: clip;
  isolation: isolate;
  font-family: 'PingFang SC', 'Microsoft YaHei', 'Helvetica Neue', Helvetica, Arial, sans-serif;
}

/* ================= 背景 ================= */
/* 兜底：自然风景渐变（远山天空 → 林间湖泊 → 森林），明亮自然光 */
.portal__bg {
  position: absolute;
  inset: 0;
  z-index: 0;
  overflow: hidden;
  background:
    /* 阳光光晕 */
    radial-gradient(58% 40% at 76% 4%, rgba(255, 252, 232, 0.9) 0%, rgba(255, 252, 232, 0) 64%),
    /* 湖面反光带 */
    linear-gradient(
      180deg,
      rgba(255, 255, 255, 0) 50%,
      rgba(219, 242, 253, 0.78) 65%,
      rgba(176, 221, 240, 0.55) 76%,
      rgba(255, 255, 255, 0) 90%
    ),
    /* 天空 → 林间 → 森林 */
    linear-gradient(
      180deg,
      #74c2f4 0%,
      #a3d9f9 16%,
      #cae9fb 32%,
      #e3f3e9 48%,
      #c2e6ce 64%,
      #98d2ac 81%,
      #74bd90 100%
    );
}

/* 远山剪影 */
.portal__bg::before {
  content: '';
  position: absolute;
  left: 0;
  right: 0;
  bottom: 30%;
  height: 36%;
  background: linear-gradient(180deg, rgba(108, 152, 188, 0.8), rgba(72, 118, 158, 0.46));
  clip-path: polygon(
    0% 100%, 7% 64%, 15% 79%, 26% 42%, 37% 71%, 47% 53%,
    58% 77%, 70% 45%, 82% 73%, 91% 57%, 100% 83%, 100% 100%
  );
  opacity: 0.55;
}

/* 近山林线剪影 */
.portal__bg::after {
  content: '';
  position: absolute;
  left: 0;
  right: 0;
  bottom: 14%;
  height: 30%;
  background: linear-gradient(180deg, rgba(50, 108, 86, 0.72), rgba(28, 74, 56, 0.5));
  clip-path: polygon(
    0% 100%, 10% 71%, 22% 87%, 34% 57%, 46% 83%, 60% 63%,
    74% 85%, 86% 67%, 100% 89%, 100% 100%
  );
  opacity: 0.5;
}

.portal__bg-photo {
  position: absolute;
  inset: 0;
  z-index: 1;
  width: 100%;
  height: 100%;
  object-fit: cover;
  object-position: center 42%;
  display: block;
}

.portal__bg-veil {
  position: absolute;
  inset: 0;
  z-index: 2;
  pointer-events: none;
  background:
    linear-gradient(
      180deg,
      rgba(255, 255, 255, 0.4) 0%,
      rgba(255, 255, 255, 0.1) 26%,
      rgba(255, 255, 255, 0.04) 54%,
      rgba(255, 255, 255, 0.34) 100%
    ),
    radial-gradient(78% 44% at 50% 2%, rgba(255, 255, 255, 0.38), rgba(255, 255, 255, 0) 66%);
}

/* ================= 轻动态背景（纯 CSS 合成层动画，无 JS / 无第三方库） =================
   层级契约（自下而上，越靠后越上）：
     .portal__bg(0) < .portal__bg-photo(1) < .portal__bg-veil(2) < .portal__fx(2，DOM 在 veil 之后) < 内容(3)
     装饰层全部 pointer-events:none，绝不拦截身份卡片与三个入口按钮的点击；
     内容层（header / main）不参与任何动画，动画前后位置完全一致。
   实现原则：只动 transform / opacity（合成层完成，不触发重排重绘），不新增 DOM 动画库、不用 JS。
   强度约 2~3 分（满 10 分）：第一眼先看到标题与三个身份入口，观察数秒后才察觉背景在动。 */

/* ---- 装饰层容器 ---- */
.portal__fx {
  position: absolute;
  inset: 0;
  z-index: 2;
  overflow: hidden;
  pointer-events: none;
}

/* ---- ① 云层缓慢漂移：3 层半透明浮云，58s / 76s / 67s，linear infinite ----
   每层元素宽 200% + background-repeat:repeat-x 平铺；位移量恰好等于一个平铺周期
   （background-size-x × 200%），所以循环点完全无缝，不会出现"跳一下"。 */
.portal__cloud {
  position: absolute;
  left: 0;
  width: 200%;
  pointer-events: none;
  background-repeat: repeat-x;
  will-change: transform;
}

.portal__cloud--1 {
  top: 4%;
  height: 19%;
  opacity: 0.3;
  background-size: 26% 100%;
  background-image:
    radial-gradient(closest-side at 16% 64%, rgba(255, 255, 255, 0.7), rgba(255, 255, 255, 0) 100%),
    radial-gradient(closest-side at 33% 45%, rgba(255, 255, 255, 0.76), rgba(255, 255, 255, 0) 100%),
    radial-gradient(closest-side at 50% 62%, rgba(255, 255, 255, 0.62), rgba(255, 255, 255, 0) 100%),
    radial-gradient(closest-side at 70% 74%, rgba(255, 255, 255, 0.44), rgba(255, 255, 255, 0) 100%);
  animation: portal-cloud-drift-a 58s linear infinite;
}

.portal__cloud--2 {
  top: 15%;
  height: 16%;
  opacity: 0.2;
  background-size: 34% 100%;
  background-image:
    radial-gradient(closest-side at 22% 58%, rgba(255, 255, 255, 0.6), rgba(255, 255, 255, 0) 100%),
    radial-gradient(closest-side at 45% 40%, rgba(255, 255, 255, 0.66), rgba(255, 255, 255, 0) 100%),
    radial-gradient(closest-side at 68% 66%, rgba(255, 255, 255, 0.5), rgba(255, 255, 255, 0) 100%);
  animation: portal-cloud-drift-b 76s linear infinite;
  animation-delay: -24s;
}

.portal__cloud--3 {
  top: 26%;
  height: 13%;
  opacity: 0.15;
  background-size: 20.5% 100%;
  background-image:
    radial-gradient(closest-side at 30% 52%, rgba(255, 255, 255, 0.58), rgba(255, 255, 255, 0) 100%),
    radial-gradient(closest-side at 62% 68%, rgba(255, 255, 255, 0.44), rgba(255, 255, 255, 0) 100%);
  animation: portal-cloud-drift-c 67s linear infinite;
  animation-delay: -47s;
}

@keyframes portal-cloud-drift-a {
  from { transform: translate3d(0, 0, 0); }
  to { transform: translate3d(-26%, 0, 0); }
}

@keyframes portal-cloud-drift-b {
  from { transform: translate3d(0, 0, 0); }
  to { transform: translate3d(-34%, 0, 0); }
}

@keyframes portal-cloud-drift-c {
  from { transform: translate3d(0, 0, 0); }
  to { transform: translate3d(-20.5%, 0, 0); }
}

/* ---- ② 阳光呼吸：右上自然光晕，scale 1 -> 1.03，11s（很弱，不是灯闪） ---- */
.portal__sun {
  position: absolute;
  top: 0;
  right: 0;
  width: 58%;
  height: 62%;
  pointer-events: none;
  transform-origin: 64% 20%;
  background: radial-gradient(
    closest-side at 64% 20%,
    rgba(255, 251, 228, 0.4) 0%,
    rgba(255, 249, 216, 0.19) 40%,
    rgba(255, 247, 212, 0) 76%
  );
  animation: portal-sun-breathe 11s ease-in-out infinite;
  will-change: transform, opacity;
}

@keyframes portal-sun-breathe {
  0%, 100% { transform: scale(1); opacity: 0.34; }
  50% { transform: scale(1.03); opacity: 0.5; }
}

/* ---- ③ 湖面微光：中下部水面极淡反光缓慢横移，23s，上下用 mask 化开（不是波浪、不闪烁） ---- */
.portal__shine {
  position: absolute;
  left: 0;
  bottom: 22%;
  width: 200%;
  height: 22%;
  pointer-events: none;
  opacity: 0.22;
  background-repeat: repeat-x;
  background-size: 22% 100%;
  background-image:
    radial-gradient(closest-side at 24% 56%, rgba(255, 255, 255, 0.34), rgba(255, 255, 255, 0) 100%),
    radial-gradient(closest-side at 58% 42%, rgba(255, 255, 255, 0.26), rgba(255, 255, 255, 0) 100%),
    radial-gradient(closest-side at 86% 64%, rgba(255, 254, 244, 0.2), rgba(255, 254, 244, 0) 100%);
  -webkit-mask-image: linear-gradient(180deg, rgba(0, 0, 0, 0) 0%, #000 34%, #000 66%, rgba(0, 0, 0, 0) 100%);
  mask-image: linear-gradient(180deg, rgba(0, 0, 0, 0) 0%, #000 34%, #000 66%, rgba(0, 0, 0, 0) 100%);
  animation: portal-shine-flow 23s linear infinite;
  will-change: transform;
}

@keyframes portal-shine-flow {
  from { transform: translate3d(0, 0, 0); }
  to { transform: translate3d(-22%, 0, 0); }
}

/* ---- ④ 山景景深 + ⑤ 整体微呼吸 ----
   在既有 CSS 风景之上追加动画，不修改原有风光规则的任何声明。
   远山 / 近山林线的位移严格控制在 ±4px、±2px 以内；整体缩放恒 >= 1（1 -> 1.015），
   因此缩放过程中背景始终铺满视口、边缘不会露白，也不会产生横向滚动条。 */
.portal__bg {
  animation: portal-bg-breathe 42s ease-in-out infinite;
  will-change: transform;
}

.portal__bg-photo {
  animation: portal-bg-breathe 42s ease-in-out infinite;
}

.portal__bg::before {
  animation: portal-mountain-far 38s ease-in-out infinite;
  will-change: transform;
}

.portal__bg::after {
  animation: portal-mountain-near 31s ease-in-out infinite;
  will-change: transform;
}

@keyframes portal-bg-breathe {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.015); }
}

@keyframes portal-mountain-far {
  0%, 100% { transform: translate3d(-3px, 1px, 0); }
  50% { transform: translate3d(3px, -1.5px, 0); }
}

@keyframes portal-mountain-near {
  0%, 100% { transform: translate3d(-4px, -2px, 0); }
  50% { transform: translate3d(4px, 2px, 0); }
}


/* ================= 顶部 ================= */
.portal__header {
  position: relative;
  z-index: 3;
  width: 100%;
  max-width: 1240px;
  margin: 0 auto;
  padding: clamp(14px, 2.4vh, 26px) clamp(20px, 3vw, 40px) 0;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}

.portal__brand {
  display: flex;
  align-items: center;
  gap: clamp(8px, 0.9vw, 12px);
  min-width: 0;
}

.portal__logo {
  width: clamp(34px, 3.1vw, 44px);
  height: clamp(34px, 3.1vw, 44px);
  border-radius: 12px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #2bb6d6 0%, #17b98f 100%);
  color: #fff;
  font-size: clamp(18px, 1.7vw, 23px);
  box-shadow: 0 6px 16px rgba(23, 140, 150, 0.26);
  flex: none;
}

.portal__brand-text {
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.portal__brand-title {
  font-size: clamp(15px, 1.32vw, 19px);
  font-weight: 700;
  color: #103a5c;
  letter-spacing: 0.5px;
  line-height: 1.25;
  white-space: nowrap;
}

.portal__brand-sub {
  font-style: normal;
  font-size: clamp(10px, 0.78vw, 12px);
  color: #4a6b84;
  letter-spacing: 0.3px;
  margin-top: 2px;
  white-space: nowrap;
}

.portal__nav {
  display: flex;
  align-items: center;
  gap: clamp(12px, 1.6vw, 26px);
  flex: none;
}

.portal__nav-item {
  font-size: clamp(12px, 0.95vw, 14px);
  color: #33536b;
  letter-spacing: 0.5px;
  cursor: default;
}

.portal__nav-badge {
  font-size: clamp(11px, 0.9vw, 13px);
  color: #166b7a;
  background: rgba(255, 255, 255, 0.72);
  border: 1px solid rgba(23, 140, 150, 0.26);
  padding: 4px 12px;
  border-radius: 999px;
  backdrop-filter: blur(6px);
  -webkit-backdrop-filter: blur(6px);
  white-space: nowrap;
}

/* ================= 主体 ================= */
.portal__main {
  position: relative;
  z-index: 3;
  width: 100%;
  max-width: 1240px;
  margin: 0 auto;
  padding: clamp(10px, 2vh, 26px) clamp(20px, 3vw, 40px) clamp(16px, 2.4vh, 30px);
  flex: 1 1 auto;
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.portal__hero {
  text-align: center;
  margin-bottom: clamp(12px, 2.2vh, 26px);
}

.portal__hero-title {
  margin: 0;
  font-size: clamp(30px, 2.1vw + 1.1vh, 48px);
  font-weight: 800;
  color: #103a5c;
  letter-spacing: 1px;
  line-height: 1.18;
  text-shadow: 0 2px 14px rgba(255, 255, 255, 0.75);
}

.portal__hero-accent {
  color: #12a87f;
}

.portal__hero-sub {
  margin: clamp(8px, 1.4vh, 16px) 0 0;
  font-size: clamp(13px, 1.7vh, 17px);
  color: #24507a;
  letter-spacing: 1px;
  text-shadow: 0 1px 10px rgba(255, 255, 255, 0.8);
}

.portal__hero-tip {
  margin: clamp(4px, 0.8vh, 10px) 0 0;
  font-size: clamp(12px, 1.5vh, 15px);
  color: #3d6484;
  text-shadow: 0 1px 10px rgba(255, 255, 255, 0.8);
}

.portal__pick {
  margin: 0 0 clamp(8px, 1.4vh, 16px);
  text-align: center;
  font-size: clamp(12px, 1.4vh, 14px);
  color: #3f6484;
  letter-spacing: 1px;
}

/* ================= 身份卡片 ================= */
.portal__cards {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: clamp(14px, 1.6vw, 26px);
  align-items: stretch;
}

.portal__card {
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  padding: clamp(18px, 3vh, 30px) clamp(16px, 1.6vw, 26px) clamp(16px, 2.6vh, 26px);
  border-radius: 22px;
  background: rgba(255, 255, 255, 0.82);
  border: 1px solid rgba(255, 255, 255, 0.88);
  box-shadow: 0 12px 32px rgba(20, 60, 92, 0.14), 0 2px 8px rgba(20, 60, 92, 0.06);
  backdrop-filter: blur(14px) saturate(140%);
  -webkit-backdrop-filter: blur(14px) saturate(140%);
  cursor: pointer;
  transition: transform 0.22s ease, box-shadow 0.22s ease, border-color 0.22s ease;
}

.portal__card:hover {
  transform: translateY(-6px);
  box-shadow: 0 22px 48px rgba(20, 60, 92, 0.2), 0 4px 12px rgba(20, 60, 92, 0.08);
  border-color: #ffffff;
}

.portal__card-avatar {
  width: clamp(78px, 12.5vh, 124px);
  height: clamp(78px, 12.5vh, 124px);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--card-soft, #eaf2f7);
  border: 4px solid rgba(255, 255, 255, 0.92);
  box-shadow: 0 8px 20px rgba(20, 60, 92, 0.12), inset 0 0 0 1px rgba(255, 255, 255, 0.6);
  margin-bottom: clamp(12px, 1.8vh, 20px);
  overflow: hidden;
  flex: none;
}

.portal__card-avatar-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  object-position: center 18%;
}

.portal__card-avatar-icon {
  font-size: clamp(30px, 4.8vh, 46px);
  color: var(--card-accent, #0f9d8c);
}

.portal__card-name {
  margin: 0;
  font-size: clamp(19px, 2.3vh, 25px);
  font-weight: 700;
  color: #14395b;
  letter-spacing: 0.5px;
}

.portal__card-desc {
  margin: clamp(8px, 1.2vh, 14px) 0 clamp(14px, 2vh, 22px);
  font-size: clamp(12px, 1.5vh, 14px);
  line-height: 1.75;
  color: #5a7791;
  white-space: pre-line;
  min-height: 3.5em;
  flex: 1 1 auto;
}

.portal__card-btn {
  margin-top: auto;
  width: 100%;
  border: none;
  border-radius: 999px;
  padding: clamp(10px, 1.5vh, 14px) 18px;
  color: #fff;
  font-family: inherit;
  font-size: clamp(13px, 1.6vh, 15px);
  font-weight: 600;
  letter-spacing: 0.5px;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  box-shadow: 0 8px 20px rgba(20, 60, 92, 0.22);
  transition: transform 0.18s ease, box-shadow 0.18s ease, filter 0.18s ease;
}

.portal__card-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 12px 26px rgba(20, 60, 92, 0.3);
  filter: brightness(1.05);
}

.portal__card-btn:active {
  transform: translateY(0);
  filter: brightness(0.97);
}

.portal__card-btn:focus-visible {
  outline: 3px solid rgba(18, 168, 127, 0.45);
  outline-offset: 2px;
}

.portal__card-btn-icon {
  font-size: 1em;
}

/* ================= 底部优势 ================= */
.portal__features {
  margin-top: clamp(14px, 2.4vh, 30px);
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: clamp(10px, 1.4vw, 22px);
  padding: clamp(14px, 2.2vh, 22px) clamp(16px, 2vw, 28px);
  border-radius: 20px;
  background: rgba(255, 255, 255, 0.78);
  border: 1px solid rgba(255, 255, 255, 0.88);
  box-shadow: 0 10px 28px rgba(20, 60, 92, 0.12);
  backdrop-filter: blur(14px) saturate(140%);
  -webkit-backdrop-filter: blur(14px) saturate(140%);
}

.portal__feature {
  display: flex;
  align-items: center;
  gap: clamp(8px, 0.9vw, 14px);
  min-width: 0;
}

.portal__feature-icon {
  width: clamp(34px, 4.4vh, 46px);
  height: clamp(34px, 4.4vh, 46px);
  border-radius: 12px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #e8f3ff 0%, #e4f7f0 100%);
  color: #1e6fff;
  font-size: clamp(17px, 2.2vh, 22px);
  flex: none;
}

.portal__feature-body {
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.portal__feature-body strong {
  font-size: clamp(13px, 1.6vh, 15px);
  color: #14395b;
  font-weight: 700;
}

.portal__feature-body em {
  font-style: normal;
  font-size: clamp(11px, 1.3vh, 12.5px);
  color: #6b8299;
  margin-top: 2px;
}

.portal__note {
  margin: clamp(10px, 1.6vh, 18px) 0 0;
  text-align: center;
  font-size: clamp(11px, 1.25vh, 12.5px);
  color: #2f5470;
  text-shadow: 0 1px 8px rgba(255, 255, 255, 0.85);
}

/* ================= 分辨率适配 ================= */
@media (max-width: 1100px) {
  .portal__cards {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .portal__features {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 720px) {
  .portal__nav {
    display: none;
  }

  .portal__cards,
  .portal__features {
    grid-template-columns: minmax(0, 1fr);
  }
}

/* 矮窗口回退：改为顶部对齐，保证内容可滚动可达、不被居中裁切 */
@media (max-height: 700px) {
  .portal__main {
    justify-content: flex-start;
  }
}

/* ================= 无障碍：系统开启"减少动态效果"时，停用全部背景动画（静态视觉完整保留） ================= */
@media (prefers-reduced-motion: reduce) {
  .portal__bg,
  .portal__bg-photo,
  .portal__bg::before,
  .portal__bg::after,
  .portal__cloud,
  .portal__sun,
  .portal__shine {
    animation: none !important;
    will-change: auto;
  }
}
</style>
