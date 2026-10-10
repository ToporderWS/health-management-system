<template>
  <BaseLayout
    :role="ROLE.COACH"
    :menus="coachMenus"
    profile-path="/coach/profile"
  />
</template>

<script setup>
import BaseLayout from '@/components/BaseLayout.vue'
import { coachMenus } from '@/router/coach'
import { ROLE } from '@/utils/config'
</script>
