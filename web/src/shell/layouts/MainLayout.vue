<script setup lang="ts">
/**
 * 门户主布局：顶栏 + 侧栏导航 + 内容区。
 *
 * 导航项来自模块注册中心，新增模块后菜单自动出现，无需改本文件。
 */

import { Dark, Notify } from 'quasar'
import { computed, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { SITE_NAME } from '@/shared/config'
import type { ModuleDescriptor } from '@/shell/types'

import { useAuthStore } from '../auth'
import { useModules } from '../useModules'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()
const { visibleModules } = useModules()

const drawer = ref(false)

const currentTitle = computed(() => (route.meta.title as string | undefined) ?? '')
const initial = computed(() => (auth.displayName || '?').charAt(0).toUpperCase())
const isDark = computed(() => Dark.isActive)

function toggleDark(): void {
  Dark.toggle()
}

function onSelect(item: ModuleDescriptor): void {
  if (item.kind === 'external') {
    window.open(item.path, '_blank', 'noopener,noreferrer')
  }
}

async function onLogout(): Promise<void> {
  await auth.logout()
  Notify.create({ type: 'positive', message: '已退出登录', position: 'top' })
  await router.replace({ name: 'login' })
}
</script>

<template>
  <q-layout view="hHh Lpr lFf">
    <q-header elevated class="bg-primary text-white">
      <q-toolbar>
        <q-btn flat dense round icon="menu" aria-label="菜单" @click="drawer = !drawer" />

        <q-toolbar-title class="text-subtitle1">
          {{ SITE_NAME }}
          <span v-if="currentTitle" class="text-caption q-ml-sm" style="opacity: 0.7">
            {{ currentTitle }}
          </span>
        </q-toolbar-title>

        <q-btn
          flat
          dense
          round
          :icon="isDark ? 'light_mode' : 'dark_mode'"
          aria-label="切换主题"
          @click="toggleDark"
        />

        <q-btn flat dense no-caps class="q-ml-sm">
          <q-avatar size="28px" color="white" text-color="primary" class="q-mr-sm">
            {{ initial }}
          </q-avatar>
          <span class="gt-xs">{{ auth.displayName }}</span>
          <q-icon name="arrow_drop_down" class="q-ml-xs" />

          <q-menu>
            <q-list style="min-width: 200px">
              <q-item>
                <q-item-section>
                  <q-item-label>{{ auth.displayName }}</q-item-label>
                  <q-item-label caption>{{ auth.roleLabel }}</q-item-label>
                </q-item-section>
              </q-item>
              <q-separator />
              <q-item v-close-popup clickable :to="{ name: 'account' }">
                <q-item-section avatar><q-icon name="manage_accounts" /></q-item-section>
                <q-item-section>个人设置</q-item-section>
              </q-item>
              <q-separator />
              <q-item v-close-popup clickable @click="onLogout">
                <q-item-section avatar><q-icon name="logout" /></q-item-section>
                <q-item-section>退出登录</q-item-section>
              </q-item>
            </q-list>
          </q-menu>
        </q-btn>
      </q-toolbar>
    </q-header>

    <q-drawer v-model="drawer" show-if-above bordered :width="218">
      <q-list padding class="q-mt-sm">
        <q-item
          v-for="item in visibleModules"
          :key="item.key"
          v-ripple
          clickable
          :to="item.kind === 'internal' ? { path: item.path } : undefined"
          :exact="item.kind === 'internal'"
          @click="onSelect(item)"
        >
          <q-item-section avatar>
            <q-icon :name="item.icon" />
          </q-item-section>
          <q-item-section>{{ item.title }}</q-item-section>
          <q-item-section v-if="item.kind === 'external'" side>
            <q-icon name="open_in_new" size="14px" />
          </q-item-section>
        </q-item>
      </q-list>
    </q-drawer>

    <q-page-container>
      <router-view />
    </q-page-container>
  </q-layout>
</template>
