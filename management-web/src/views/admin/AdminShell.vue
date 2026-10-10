<template>
  <BaseLayout
    :role="ROLE.ADMIN"
    :menus="adminMenus"
    profile-path="/admin/system?tab=profile"
  />
</template>

<script setup>
import BaseLayout from '@/components/BaseLayout.vue'
import { adminMenus } from '@/router/admin'
import { ROLE } from '@/utils/config'
</script>
