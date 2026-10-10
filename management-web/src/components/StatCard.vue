<template>
  <div class="hms-stat">
    <div class="hms-stat__icon" :style="{ background: gradient }">
      <el-icon><component :is="icon" /></el-icon>
    </div>
    <div class="hms-stat__body">
      <div class="hms-stat__value">
        {{ displayValue }}<span v-if="suffix" class="hms-stat__suffix">{{ suffix }}</span>
      </div>
      <div class="hms-stat__label">{{ label }}</div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  label: { type: String, default: '' },
  value: { type: [Number, String], default: 0 },
  icon: { type: String, default: 'DataLine' },
  gradient: { type: String, default: 'linear-gradient(135deg, #1b3a6b 0%, #2f5da8 100%)' },
  suffix: { type: String, default: '' },
})

const displayValue = computed(() => {
  const v = props.value
  if (typeof v === 'number') return v.toLocaleString('zh-CN')
  return v
})
</script>

<style scoped>
.hms-stat__suffix {
  font-size: 13px;
  font-weight: 500;
  color: var(--hms-text-sub);
  margin-left: 4px;
}
</style>
