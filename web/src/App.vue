<script setup lang="ts">
import { Dark } from 'quasar'
import { onMounted } from 'vue'

// 主题跟随系统偏好（顶栏也提供了手动切换）
onMounted(() => {
  Dark.set('auto')
})
</script>

<template>
  <router-view />
</template>
