<template>
  <el-select
    :model-value="modelValue"
    :placeholder="placeholder"
    clearable
    filterable
    style="width: 100%"
    @update:model-value="(v) => emit('update:modelValue', v)"
  >
    <el-option
      v-for="item in options"
      :key="item.id"
      :label="`${item.nickname}（${item.phone || '无手机号'}）`"
      :value="item.id"
    />
  </el-select>
</template>

<script setup>
import { onMounted, ref } from 'vue'

import { coachApi } from '@/api/coach'
import { doctorApi } from '@/api/doctor'

const props = defineProps({
  modelValue: { type: [Number, String], default: '' },
  // doctor -> 患者列表；coach -> 学员列表
  role: { type: String, default: 'doctor' },
  placeholder: { type: String, default: '请选择' },
})

const emit = defineEmits(['update:modelValue'])

const options = ref([])

async function load() {
  try {
    const api = props.role === 'coach' ? coachApi : doctorApi
    const fn = props.role === 'coach' ? api.studentList : api.patientList
    // 一次性拉取足够多的选项用于选择（后端已按关系过滤，只能看到自己的）
    const { data } = await fn({ page: 1, page_size: 200 })
    options.value = data.list || []
  } catch (e) {
    options.value = []
  }
}

onMounted(load)
defineExpose({ load })
</script>
