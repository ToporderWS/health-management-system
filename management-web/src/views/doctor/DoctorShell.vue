<template>
  <BaseLayout
    :role="ROLE.DOCTOR"
    :menus="doctorMenus"
    profile-path="/doctor/profile"
  />
</template>

<script setup>
import BaseLayout from '@/components/BaseLayout.vue'
import { doctorMenus } from '@/router/doctor'
import { ROLE } from '@/utils/config'
</script>
