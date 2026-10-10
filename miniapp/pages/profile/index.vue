<template>
  <view class="hm-page profile">
    <!-- 未登录 -->
    <view v-if="!logged" class="hm-card profile__login">
      <view class="profile__login-tip">登录后可记录并查看你的健康数据</view>
      <view class="hm-btn" @tap="goLogin">立即登录</view>
      <view class="hm-btn hm-btn--plain" @tap="goRegister">注册新账号</view>
    </view>

    <template v-else>
      <!-- 个人信息卡 -->
      <view class="profile__head hm-gradient">
        <image
          class="profile__avatar"
          :src="avatarUrl"
          mode="aspectFill"
          @tap="chooseAvatar"
        />
        <view class="profile__head-info">
          <text class="profile__nickname">{{ info.nickname || '未设置昵称' }}</text>
          <text class="profile__phone">{{ info.phone }}</text>
        </view>
        <text class="profile__edit" @tap="openEdit">编辑</text>
      </view>

      <view class="hm-tip profile__avatar-tip">点击头像可更换（jpg / jpeg / png / webp）</view>

      <!-- 基础资料 -->
      <view class="hm-card">
        <view class="hm-card__title">
          <text class="hm-title-text">基础资料</text>
          <text class="profile__link" @tap="openEdit">修改</text>
        </view>
        <view class="hm-field">
          <text class="hm-field__label">昵称</text>
          <text class="hm-field__value">{{ info.nickname || '--' }}</text>
        </view>
        <view class="hm-field">
          <text class="hm-field__label">手机号</text>
          <text class="hm-field__value">{{ info.phone || '--' }}</text>
        </view>
        <view class="hm-field">
          <text class="hm-field__label">性别</text>
          <text class="hm-field__value">{{ info.gender || '--' }}</text>
        </view>
        <view class="hm-field">
          <text class="hm-field__label">年龄</text>
          <text class="hm-field__value">{{ info.age ?? '--' }}</text>
        </view>
        <view class="hm-field">
          <text class="hm-field__label">身高</text>
          <text class="hm-field__value">{{ info.height ?? '--' }} cm</text>
        </view>
        <view class="hm-field">
          <text class="hm-field__label">注册时间</text>
          <text class="hm-field__value">{{ info.created_at || '--' }}</text>
        </view>
      </view>

      <!-- 功能入口 -->
      <view class="hm-card">
        <view class="hm-card__title"><text class="hm-title-text">我的服务</text></view>
        <view v-for="m in menus" :key="m.key" class="hm-field profile__menu" @tap="go(m.url)">
          <text class="hm-field__label">{{ m.label }}</text>
          <text class="profile__arrow">›</text>
        </view>
      </view>

      <!-- 操作 -->
      <view class="hm-card">
        <view class="hm-field profile__menu" @tap="openPwd">
          <text class="hm-field__label">修改密码</text>
          <text class="profile__arrow">›</text>
        </view>
        <view class="hm-field profile__menu" @tap="logout">
          <text class="hm-field__label profile__danger">退出登录</text>
          <text class="profile__arrow">›</text>
        </view>
      </view>
    </template>

    <!-- 编辑资料弹层 -->
    <view v-if="editVisible" class="profile__mask" @tap="editVisible = false">
      <view class="profile__dialog" @tap.stop>
        <view class="profile__dialog-title">修改资料</view>
        <view class="hm-field">
          <text class="hm-field__label">昵称</text>
          <input class="hm-field__input" :value="form.nickname" maxlength="50" placeholder="请输入昵称"
            placeholder-class="ph" @input="form.nickname = $event.detail.value" />
        </view>
        <view class="hm-field">
          <text class="hm-field__label">性别</text>
          <view class="profile__opts">
            <text
              v-for="g in genders"
              :key="g"
              class="profile__opt"
              :class="{ 'profile__opt--active': form.gender === g }"
              @tap="form.gender = g"
            >{{ g }}</text>
          </view>
        </view>
        <view class="hm-field">
          <text class="hm-field__label">年龄</text>
          <input class="hm-field__input" type="number" :value="form.age" placeholder="1~120"
            placeholder-class="ph" @input="form.age = $event.detail.value" />
        </view>
        <view class="hm-field">
          <text class="hm-field__label">身高(cm)</text>
          <input class="hm-field__input" type="digit" :value="form.height" placeholder="50~250"
            placeholder-class="ph" @input="form.height = $event.detail.value" />
        </view>
        <view class="hm-btn" @tap="saveInfo">保存</view>
        <view class="hm-btn hm-btn--plain" @tap="editVisible = false">取消</view>
      </view>
    </view>

    <!-- 修改密码弹层 -->
    <view v-if="pwdVisible" class="profile__mask" @tap="pwdVisible = false">
      <view class="profile__dialog" @tap.stop>
        <view class="profile__dialog-title">修改密码</view>
        <view class="hm-field">
          <text class="hm-field__label">原密码</text>
          <input class="hm-field__input" password :value="pwd.old_password" placeholder="请输入原密码"
            placeholder-class="ph" @input="pwd.old_password = $event.detail.value" />
        </view>
        <view class="hm-field">
          <text class="hm-field__label">新密码</text>
          <input class="hm-field__input" password :value="pwd.new_password" placeholder="不少于 6 位"
            placeholder-class="ph" @input="pwd.new_password = $event.detail.value" />
        </view>
        <view class="hm-field">
          <text class="hm-field__label">确认新密码</text>
          <input class="hm-field__input" password :value="pwd.confirm_password" placeholder="请再次输入"
            placeholder-class="ph" @input="pwd.confirm_password = $event.detail.value" />
        </view>
        <view class="hm-btn" @tap="savePwd">确认修改</view>
        <view class="hm-btn hm-btn--plain" @tap="pwdVisible = false">取消</view>
      </view>
    </view>
  </view>
</template>

<script setup>
import { computed, reactive, ref } from 'vue'
import { onShow } from '@dcloudio/uni-app'

import { api } from '@/api/index'
import { clearAuth, getToken, getUserInfo, isLogin, setToken, setUserInfo } from '@/common/auth'
import { imgSrc } from '@/common/image'

const logged = ref(false)
const info = ref({})
const editVisible = ref(false)
const pwdVisible = ref(false)
const genders = ['男', '女', '保密']

const form = reactive({ nickname: '', gender: '保密', age: '', height: '' })
const pwd = reactive({ old_password: '', new_password: '', confirm_password: '' })

const avatarUrl = computed(() => imgSrc(info.value.avatar) || '/static/tabbar/profile-active.png')

const menus = [
  { key: 'advice', label: '医生健康建议', url: '/pages/doctor-advice/index' },
  { key: 'notice', label: '体检通知', url: '/pages/medical-notice/index' },
  { key: 'record', label: '医疗记录', url: '/pages/medical-record/index' },
  { key: 'goal', label: '运动目标', url: '/pages/sport-goal/index' },
  { key: 'training', label: '训练计划', url: '/pages/training-plan/index' },
  { key: 'fitness', label: '健身建议', url: '/pages/fitness-advice/index' },
  { key: 'plan', label: '健康计划', url: '/pages/plan/index' },
  { key: 'article', label: '健康科普', url: '/pages/article/index' },
]

function goLogin() {
  uni.navigateTo({ url: '/pages/login/index' })
}

function goRegister() {
  uni.navigateTo({ url: '/pages/register/index' })
}

function go(url) {
  uni.navigateTo({ url })
}

async function load() {
  logged.value = isLogin()
  if (!logged.value) {
    info.value = {}
    return
  }
  info.value = getUserInfo() || {}
  try {
    const res = await api.userInfo()
    info.value = res.data || {}
    setUserInfo(info.value)
  } catch (e) {
    /* 401 由请求层统一处理 */
  }
}

function openEdit() {
  form.nickname = info.value.nickname || ''
  form.gender = info.value.gender || '保密'
  form.age = info.value.age ?? ''
  form.height = info.value.height ?? ''
  editVisible.value = true
}

function openPwd() {
  pwd.old_password = ''
  pwd.new_password = ''
  pwd.confirm_password = ''
  pwdVisible.value = true
}

async function saveInfo() {
  if (!form.nickname || !form.nickname.trim()) {
    return uni.showToast({ title: '昵称不能为空', icon: 'none' })
  }
  if (form.age !== '' && (Number(form.age) < 1 || Number(form.age) > 120)) {
    return uni.showToast({ title: '年龄需在 1~120 之间', icon: 'none' })
  }
  if (form.height !== '' && (Number(form.height) < 50 || Number(form.height) > 250)) {
    return uni.showToast({ title: '身高需在 50~250cm 之间', icon: 'none' })
  }
  try {
    const res = await api.updateInfo({
      nickname: form.nickname.trim(),
      gender: form.gender,
      age: form.age === '' ? undefined : Number(form.age),
      height: form.height === '' ? undefined : Number(form.height),
    })
    info.value = res.data || info.value
    setUserInfo(info.value)
    editVisible.value = false
    uni.showToast({ title: res.msg || '资料更新成功', icon: 'success' })
  } catch (e) {
    /* 忽略 */
  }
}

async function savePwd() {
  if (!pwd.old_password) return uni.showToast({ title: '请输入原密码', icon: 'none' })
  if (!pwd.new_password || pwd.new_password.length < 6) {
    return uni.showToast({ title: '新密码不能少于 6 位', icon: 'none' })
  }
  if (pwd.new_password !== pwd.confirm_password) {
    return uni.showToast({ title: '两次输入的新密码不一致', icon: 'none' })
  }
  try {
    const res = await api.updatePwd({
      old_password: pwd.old_password,
      new_password: pwd.new_password,
    })
    pwdVisible.value = false
    uni.showToast({ title: res.msg || '密码修改成功', icon: 'success' })
  } catch (e) {
    /* 忽略 */
  }
}

/** 选择并上传头像：后端只把文件名写入数据库 */
function chooseAvatar() {
  uni.chooseImage({
    count: 1,
    sizeType: ['compressed'],
    sourceType: ['album', 'camera'],
    success: async (res) => {
      const filePath = res.tempFilePaths[0]
      try {
        const up = await api.uploadAvatar(filePath)
        const next = Object.assign({}, info.value, { avatar: up.data && up.data.avatar })
        info.value = next
        setUserInfo(next)
        // 同步 Token：后端未改动 Token，这里仅刷新本地缓存
        setToken(getToken())
        uni.showToast({ title: '头像已更新', icon: 'success' })
      } catch (e) {
        /* 忽略 */
      }
    },
  })
}

function logout() {
  uni.showModal({
    title: '退出登录',
    content: '确认要退出当前账号吗？',
    success: async (r) => {
      if (!r.confirm) return
      try {
        await api.logout()
      } catch (e) {
        /* 即使后端返回异常也照常清除本地登录态 */
      }
      clearAuth()
      info.value = {}
      logged.value = false
      uni.showToast({ title: '已退出登录', icon: 'success' })
      setTimeout(() => uni.switchTab({ url: '/pages/index/index' }), 700)
    },
  })
}

onShow(() => {
  load()
})
</script>

<style scoped>
.profile__login {
  margin-top: 80rpx;
  padding: 48rpx 28rpx;
  text-align: center;
}

.profile__login-tip {
  font-size: 28rpx;
  color: #5c6b7a;
  margin-bottom: 32rpx;
}

.profile__head {
  display: flex;
  align-items: center;
  border-radius: 26rpx;
  padding: 32rpx 28rpx;
  margin-bottom: 16rpx;
  box-shadow: 0 10rpx 26rpx rgba(46, 125, 50, 0.22);
}

.profile__avatar {
  width: 120rpx;
  height: 120rpx;
  border-radius: 60rpx;
  border: 4rpx solid rgba(255, 255, 255, 0.7);
  background: #ffffff;
}

.profile__head-info {
  flex: 1;
  margin-left: 24rpx;
  display: flex;
  flex-direction: column;
}

.profile__nickname {
  font-size: 34rpx;
  font-weight: 700;
  color: #ffffff;
}

.profile__phone {
  font-size: 25rpx;
  color: #d7f0da;
  margin-top: 10rpx;
}

.profile__edit {
  color: #ffffff;
  font-size: 26rpx;
  border: 1rpx solid rgba(255, 255, 255, 0.7);
  border-radius: 26rpx;
  padding: 8rpx 22rpx;
}

.profile__avatar-tip {
  padding: 0 8rpx 20rpx;
}

.profile__link {
  font-size: 24rpx;
  color: #2e7d32;
  font-weight: 400;
}

.profile__menu {
  justify-content: space-between;
}

.profile__arrow {
  color: #c3cec7;
  font-size: 34rpx;
  line-height: 1;
}

.profile__danger {
  color: #d9534f;
}

.profile__mask {
  position: fixed;
  left: 0;
  right: 0;
  top: 0;
  bottom: 0;
  background: rgba(16, 32, 20, 0.45);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 99;
  padding: 0 40rpx;
}

.profile__dialog {
  width: 100%;
  background: #ffffff;
  border-radius: 26rpx;
  padding: 32rpx 28rpx 24rpx;
  box-sizing: border-box;
}

.profile__dialog-title {
  font-size: 32rpx;
  font-weight: 700;
  color: #1f2d3d;
  text-align: center;
  margin-bottom: 20rpx;
}

.hm-field__value {
  flex: 1;
  text-align: right;
  font-size: 28rpx;
  color: #1f2d3d;
}

.profile__opts {
  flex: 1;
  display: flex;
  justify-content: flex-end;
}

.profile__opt {
  padding: 8rpx 22rpx;
  margin-left: 12rpx;
  border-radius: 30rpx;
  font-size: 25rpx;
  color: #7a8b9a;
  background: #f1f6f1;
}

.profile__opt--active {
  background: #2e7d32;
  color: #ffffff;
}

.ph {
  color: #b6c2cd;
}
</style>
