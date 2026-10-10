import { createApp } from 'vue'
import ElementPlus from 'element-plus'
import zhCn from 'element-plus/es/locale/lang/zh-cn'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'

import 'element-plus/dist/index.css'
import '@/assets/styles.css'

import App from './App.vue'
import router from './router'
import { restoreAuth } from '@/utils/auth'

// 应用启动即恢复三角色登录态
restoreAuth()

const app = createApp(App)

// 全局注册 Element Plus 图标（侧边菜单按名称动态渲染）
Object.entries(ElementPlusIconsVue).forEach(([key, component]) => {
  app.component(key, component)
})

app.use(ElementPlus, { locale: zhCn })
app.use(router)
app.mount('#app')
