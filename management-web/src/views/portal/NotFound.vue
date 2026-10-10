<template>
  <div class="nf">
    <el-result icon="warning" title="404" sub-title="页面不存在或已被移除">
      <template #extra>
        <el-button type="primary" @click="router.push('/')">返回身份选择</el-button>
      </template>
    </el-result>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router'

const router = useRouter()
</script>

<style scoped>
.nf {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--hms-bg);
}
</style>
