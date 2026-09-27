<script setup lang="ts">
/** 登录页。仅账号密码登录（按需求，暂不做验证码/扫码）。 */

import type { AxiosError } from 'axios'
import { Notify } from 'quasar'
import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { SITE_NAME } from '@/shared/config'
import type { ApiErrorBody } from '@/shared/types'
import { useAuthStore } from '@/shell/auth'

const router = useRouter()
const route = useRoute()
const auth = useAuthStore()

const username = ref('')
const password = ref('')
const showPassword = ref(false)
const submitting = ref(false)
const errorMessage = ref('')

async function onSubmit(): Promise<void> {
  errorMessage.value = ''
  submitting.value = true
  try {
    await auth.login(username.value.trim(), password.value)
    Notify.create({
      type: 'positive',
      message: `欢迎回来，${auth.displayName}`,
      position: 'top',
    })
    const redirect = route.query.redirect
    await router.replace(typeof redirect === 'string' && redirect ? redirect : '/')
  } catch (error) {
    const axiosError = error as AxiosError<ApiErrorBody>
    errorMessage.value = axiosError.response?.data?.message ?? '登录失败，请稍后重试'
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <div class="login-page">
    <div class="login-card">
      <div class="text-center q-mb-lg">
        <q-icon name="hub" size="48px" color="primary" />
        <div class="text-h5 text-weight-medium q-mt-sm">{{ SITE_NAME }}</div>
        <div class="text-caption text-grey-6 q-mt-xs">请使用账号密码登录</div>
      </div>

      <q-form greedy @submit.prevent="onSubmit">
        <q-input
          v-model="username"
          label="账号"
          outlined
          dense
          autofocus
          :disable="submitting"
          :rules="[(val) => Boolean(val && val.trim()) || '请输入账号']"
          lazy-rules
        >
          <template #prepend><q-icon name="person" /></template>
        </q-input>

        <q-input
          v-model="password"
          label="密码"
          outlined
          dense
          class="q-mt-md"
          :type="showPassword ? 'text' : 'password'"
          :disable="submitting"
          :rules="[(val) => Boolean(val) || '请输入密码']"
          lazy-rules
          @keyup.enter="onSubmit"
        >
          <template #prepend><q-icon name="lock" /></template>
          <template #append>
            <q-icon
              :name="showPassword ? 'visibility_off' : 'visibility'"
              class="cursor-pointer"
              @click="showPassword = !showPassword"
            />
          </template>
        </q-input>

        <q-banner v-if="errorMessage" dense class="bg-red-1 text-red-8 q-mt-md" rounded>
          <template #avatar><q-icon name="error_outline" /></template>
          {{ errorMessage }}
        </q-banner>

        <q-btn
          type="submit"
          label="登录"
          color="primary"
          class="full-width q-mt-lg"
          unelevated
          :loading="submitting"
        />
      </q-form>
    </div>

    <div class="text-caption text-grey-6 q-mt-lg text-center">
      个人工作门户 · 模块化单体架构
    </div>
  </div>
</template>

<style scoped>
.login-page {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 24px;
  background: linear-gradient(150deg, #eef3fb 0%, #f7f9fc 55%, #eaf1f8 100%);
}

.body--dark .login-page {
  background: linear-gradient(150deg, #14181f 0%, #10131a 55%, #171c25 100%);
}

.login-card {
  width: 100%;
  max-width: 400px;
  padding: 32px 30px 28px;
  border-radius: 14px;
  background: #fff;
  box-shadow: 0 10px 34px rgba(16, 42, 80, 0.1);
}

.body--dark .login-card {
  background: #1c2128;
  box-shadow: 0 10px 34px rgba(0, 0, 0, 0.45);
}
</style>
