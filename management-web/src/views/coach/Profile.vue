<template>
  <RoleProfile :role="ROLE.COACH" />
</template>

<script setup>
import RoleProfile from '@/components/RoleProfile.vue'
import { ROLE } from '@/utils/config'
</script>
