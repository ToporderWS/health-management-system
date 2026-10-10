<script>
export default {
  onLaunch() {
    console.log('个人健康管理系统小程序启动')
  },
  onShow() {
    console.log('小程序显示')
  },
  onHide() {
    console.log('小程序隐藏')
  },
}
</script>

<style>
/* =========================================================
   全局样式：主色 #2E7D32 / 辅助 #66BB6A / 背景 #F4FAF5
   现代 · 健康 · 简约 · 卡片化 · 圆角 · 轻阴影 · 充分留白
   ========================================================= */
page {
  background-color: #f4faf5;
  color: #1f2d3d;
  font-size: 28rpx;
  font-family: -apple-system, BlinkMacSystemFont, 'Helvetica Neue', 'PingFang SC', 'Microsoft YaHei', sans-serif;
}

.hm-page {
  min-height: 100vh;
  padding: 24rpx 24rpx 40rpx;
  box-sizing: border-box;
}

/* 卡片 */
.hm-card {
  background: #ffffff;
  border-radius: 24rpx;
  padding: 28rpx;
  margin-bottom: 24rpx;
  box-shadow: 0 6rpx 20rpx rgba(46, 125, 50, 0.07);
}

.hm-card__title {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 30rpx;
  font-weight: 600;
  color: #1f2d3d;
  margin-bottom: 22rpx;
}

.hm-card__title::before {
  content: '';
  width: 8rpx;
  height: 30rpx;
  border-radius: 4rpx;
  background: linear-gradient(180deg, #2e7d32 0%, #66bb6a 100%);
  margin-right: 14rpx;
}

.hm-title-text {
  display: flex;
  align-items: center;
  flex: 1;
}

/* 渐变主色条 */
.hm-gradient {
  background: linear-gradient(135deg, #2e7d32 0%, #66bb6a 100%);
}

/* 表单 */
.hm-field {
  display: flex;
  align-items: center;
  border-bottom: 1rpx solid #e6f0e7;
  padding: 22rpx 0;
}

.hm-field:last-child {
  border-bottom: none;
}

.hm-field__label {
  width: 190rpx;
  color: #5c6b7a;
  font-size: 28rpx;
  flex-shrink: 0;
}

.hm-field__input {
  flex: 1;
  font-size: 28rpx;
  color: #1f2d3d;
  text-align: right;
}

.hm-field__unit {
  color: #8a99a8;
  font-size: 26rpx;
  margin-left: 8rpx;
}

/* 按钮 */
.hm-btn {
  height: 88rpx;
  line-height: 88rpx;
  border-radius: 44rpx;
  background: linear-gradient(135deg, #2e7d32 0%, #66bb6a 100%);
  color: #ffffff;
  font-size: 32rpx;
  text-align: center;
  margin-top: 12rpx;
  box-shadow: 0 8rpx 20rpx rgba(46, 125, 50, 0.24);
}

.hm-btn--plain {
  background: #ffffff;
  color: #2e7d32;
  border: 2rpx solid #a5d6a7;
  box-shadow: none;
}

.hm-btn--disabled {
  opacity: 0.5;
}

/* 列表项 */
.hm-item {
  background: #ffffff;
  border-radius: 22rpx;
  padding: 26rpx;
  margin-bottom: 20rpx;
  box-shadow: 0 4rpx 16rpx rgba(46, 125, 50, 0.06);
}

.hm-item__row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12rpx;
}

.hm-item__row:last-child {
  margin-bottom: 0;
}

.hm-item__title {
  font-size: 30rpx;
  font-weight: 600;
  color: #1f2d3d;
  flex: 1;
  margin-right: 16rpx;
}

.hm-item__meta {
  font-size: 24rpx;
  color: #8a99a8;
}

.hm-item__content {
  font-size: 27rpx;
  color: #4a5a6a;
  line-height: 1.75;
  word-break: break-all;
}

/* 标签 */
.hm-tag {
  display: inline-block;
  padding: 4rpx 16rpx;
  border-radius: 20rpx;
  font-size: 22rpx;
  background: #e8f5e9;
  color: #2e7d32;
}

.hm-tag--gray {
  background: #eef1f5;
  color: #7a8b9a;
}

.hm-tag--orange {
  background: #fff4e5;
  color: #e08b1a;
}

/* 空状态 / 提示 */
.hm-empty {
  padding: 120rpx 0;
  text-align: center;
  color: #9aa8b5;
  font-size: 28rpx;
}

.hm-tip {
  font-size: 24rpx;
  color: #8a99a8;
  line-height: 1.7;
}

.hm-alert {
  background: #fff8e1;
  border-left: 8rpx solid #ffb300;
  border-radius: 12rpx;
  padding: 22rpx 24rpx;
  font-size: 25rpx;
  color: #8a6d1a;
  line-height: 1.75;
}

.hm-flex {
  display: flex;
  align-items: center;
}

.hm-flex-between {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.hm-mb {
  margin-bottom: 24rpx;
}
</style>
