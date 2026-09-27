<script setup lang="ts">
/** 无权访问。 */
</script>

<template>
  <q-page class="column flex-center" style="min-height: 60vh">
    <q-icon name="block" size="56px" color="orange-6" />
    <div class="text-h6 q-mt-md">你没有访问该页面的权限</div>
    <div class="text-caption text-grey-6 q-mt-sm">
      如果这是误判，请联系管理员为你的账号分配对应权限。
    </div>
    <q-btn label="返回工作台" color="primary" unelevated class="q-mt-lg" to="/" />
  </q-page>
</template>
