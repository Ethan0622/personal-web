<script setup lang="ts">
/** 个人设置：修改资料、改密码、查看自己持有的权限。 */

import type { AxiosError } from 'axios'
import { Notify } from 'quasar'
import { computed, reactive, ref } from 'vue'

import type { ApiErrorBody } from '@/shared/types'
import { useAuthStore } from '@/shell/auth'
import { useModules } from '@/shell/useModules'

const auth = useAuthStore()
const { visibleModules } = useModules()

const profile = reactive({
  real_name: auth.user?.real_name ?? '',
  email: auth.user?.email ?? '',
  phone: auth.user?.phone ?? '',
})
const savingProfile = ref(false)

const passwordForm = reactive({ old_password: '', new_password: '', confirm: '' })
const savingPassword = ref(false)

const isSuperadmin = computed(() => auth.hasPerm('*'))

async function saveProfile(): Promise<void> {
  savingProfile.value = true
  try {
    await auth.updateProfile({ ...profile })
    Notify.create({ type: 'positive', message: '资料已更新', position: 'top' })
  } catch {
    // 错误提示已由 http 层统一处理
  } finally {
    savingProfile.value = false
  }
}

async function savePassword(): Promise<void> {
  if (passwordForm.new_password !== passwordForm.confirm) {
    Notify.create({ type: 'warning', message: '两次输入的新密码不一致', position: 'top' })
    return
  }
  savingPassword.value = true
  try {
    await auth.changePassword(passwordForm.old_password, passwordForm.new_password)
    Notify.create({
      type: 'positive',
      message: '密码已更新，请重新登录',
      position: 'top',
    })
    passwordForm.old_password = ''
    passwordForm.new_password = ''
    passwordForm.confirm = ''
    await auth.logout()
    window.location.href = '/login'
  } catch (error) {
    const axiosError = error as AxiosError<ApiErrorBody>
    const detail = axiosError.response?.data?.message
    if (detail) {
      Notify.create({ type: 'negative', message: detail, position: 'top' })
    }
  } finally {
    savingPassword.value = false
  }
}
</script>

<template>
  <q-page padding>
    <div class="page-head">
      <div class="text-h6">个人设置</div>
      <div class="text-caption text-grey-6">修改个人资料与登录密码</div>
    </div>

    <div class="row q-col-gutter-md">
      <div class="col-12 col-md-6">
        <q-card flat bordered>
          <q-card-section>
            <div class="text-subtitle2">基本资料</div>
          </q-card-section>
          <q-separator />
          <q-card-section>
            <q-input :model-value="auth.user?.username" label="账号" outlined dense disable />
            <q-input
              v-model="profile.real_name"
              label="姓名"
              outlined
              dense
              class="q-mt-md"
              maxlength="64"
            />
            <q-input
              v-model="profile.email"
              label="邮箱"
              type="email"
              outlined
              dense
              class="q-mt-md"
              maxlength="254"
            />
            <q-input
              v-model="profile.phone"
              label="手机号"
              outlined
              dense
              class="q-mt-md"
              maxlength="20"
            />
            <q-btn
              label="保存资料"
              color="primary"
              unelevated
              class="q-mt-lg"
              :loading="savingProfile"
              @click="saveProfile"
            />
          </q-card-section>
        </q-card>
      </div>

      <div class="col-12 col-md-6">
        <q-card flat bordered>
          <q-card-section>
            <div class="text-subtitle2">修改密码</div>
          </q-card-section>
          <q-separator />
          <q-card-section>
            <q-input
              v-model="passwordForm.old_password"
              label="当前密码"
              type="password"
              outlined
              dense
            />
            <q-input
              v-model="passwordForm.new_password"
              label="新密码（至少 8 位）"
              type="password"
              outlined
              dense
              class="q-mt-md"
            />
            <q-input
              v-model="passwordForm.confirm"
              label="确认新密码"
              type="password"
              outlined
              dense
              class="q-mt-md"
            />
            <q-btn
              label="修改密码"
              color="primary"
              unelevated
              class="q-mt-lg"
              :loading="savingPassword"
              :disable="!passwordForm.old_password || passwordForm.new_password.length < 8"
              @click="savePassword"
            />
          </q-card-section>
        </q-card>

        <q-card flat bordered class="q-mt-md">
          <q-card-section>
            <div class="text-subtitle2">
              我的权限
              <q-badge v-if="isSuperadmin" color="deep-orange" class="q-ml-sm">超级管理员</q-badge>
            </div>
            <div class="text-caption text-grey-6 q-mt-xs">
              可访问的模块由权限决定，未授权的模块不会出现在菜单中。
            </div>
          </q-card-section>
          <q-separator />
          <q-card-section>
            <div class="row q-col-gutter-xs">
              <div v-for="code in auth.user?.perms ?? []" :key="code" class="col-auto">
                <q-chip dense square color="blue-1" text-color="blue-9">{{ code }}</q-chip>
              </div>
            </div>
            <div class="q-mt-md text-caption text-grey-6">
              当前可见模块：{{ visibleModules.map((m) => m.title).join(' / ') || '无' }}
            </div>
          </q-card-section>
        </q-card>
      </div>
    </div>
  </q-page>
</template>

<style scoped>
.page-head {
  margin-bottom: 18px;
}
</style>
