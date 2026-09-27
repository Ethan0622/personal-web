<script setup lang="ts">
/** 工作台：问候、模块入口、外链快捷访问。 */

import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'

import { fetchExternalLinks } from '@/shared/api/portal'
import type { ExternalLink, Paginated } from '@/shared/types'
import { useAuthStore } from '@/shell/auth'
import { useModules } from '@/shell/useModules'
import type { ModuleDescriptor } from '@/shell/types'

const router = useRouter()
const auth = useAuthStore()
const { dashboardCards, externalModules } = useModules()

const links = ref<ExternalLink[]>([])
const loadingLinks = ref(false)

const greeting = computed(() => {
  const hour = new Date().getHours()
  if (hour < 6) return '夜深了'
  if (hour < 12) return '早上好'
  if (hour < 14) return '中午好'
  if (hour < 18) return '下午好'
  return '晚上好'
})

const today = computed(() =>
  new Date().toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    weekday: 'long',
  }),
)

/** 工作台只展示前 6 个外链，其余在「外链入口」页查看 */
const topLinks = computed(() => links.value.slice(0, 6))

function openModule(item: ModuleDescriptor): void {
  if (item.kind === 'external') {
    window.open(item.path, '_blank', 'noopener,noreferrer')
  } else {
    void router.push({ path: item.path })
  }
}

function openLink(item: ExternalLink): void {
  if (item.open_in_new_tab) {
    window.open(item.url, '_blank', 'noopener,noreferrer')
  } else {
    window.location.href = item.url
  }
}

onMounted(async () => {
  loadingLinks.value = true
  try {
    const data: Paginated<ExternalLink> = await fetchExternalLinks()
    links.value = data.results
  } catch {
    // 无外链或接口未开放时静默处理，不影响工作台其他内容
  } finally {
    loadingLinks.value = false
  }
})
</script>

<template>
  <q-page padding>
    <!-- 问候 -->
    <q-card flat bordered class="q-mb-md welcome-card">
      <q-card-section class="row items-center no-wrap">
        <div class="col">
          <div class="text-h6">{{ greeting }}，{{ auth.displayName }}</div>
          <div class="text-caption text-grey-6 q-mt-xs">{{ today }}</div>
        </div>
        <q-icon name="hub" size="42px" color="primary" style="opacity: 0.28" />
      </q-card-section>
    </q-card>

    <!-- 模块入口 -->
    <div class="section-title">
      <q-icon name="apps" size="18px" />
      <span>功能模块</span>
    </div>

    <div class="row q-col-gutter-md">
      <div v-for="item in dashboardCards" :key="item.key" class="col-12 col-sm-6 col-md-4">
        <q-card flat bordered clickable class="module-card" @click="openModule(item)">
          <q-card-section>
            <div class="row items-center no-wrap">
              <q-icon :name="item.icon" size="28px" color="primary" />
              <div class="q-ml-md col">
                <div class="text-subtitle2">{{ item.title }}</div>
                <div class="text-caption text-grey-6">{{ item.description || '—' }}</div>
              </div>
              <q-icon name="chevron_right" color="grey-5" />
            </div>
          </q-card-section>
        </q-card>
      </div>

      <!-- 代码中登记的第三方平台 -->
      <div v-for="item in externalModules" :key="item.key" class="col-12 col-sm-6 col-md-4">
        <q-card flat bordered clickable class="module-card" @click="openModule(item)">
          <q-card-section>
            <div class="row items-center no-wrap">
              <q-icon :name="item.icon" size="28px" color="teal" />
              <div class="q-ml-md col">
                <div class="text-subtitle2">{{ item.title }}</div>
                <div class="text-caption text-grey-6">外部平台</div>
              </div>
              <q-icon name="open_in_new" size="16px" color="grey-5" />
            </div>
          </q-card-section>
        </q-card>
      </div>

      <div
        v-if="!dashboardCards.length && !externalModules.length"
        class="col-12"
      >
        <q-card flat bordered>
          <q-card-section class="text-center text-grey-6">
            暂无可用模块。新模块会随着开发逐步出现在这里。
          </q-card-section>
        </q-card>
      </div>
    </div>

    <!-- 外链快捷入口 -->
    <div v-if="topLinks.length" class="section-title q-mt-lg">
      <q-icon name="link" size="18px" />
      <span>快捷入口</span>
      <q-space />
      <q-btn flat dense no-caps size="sm" label="全部" to="/links" />
    </div>

    <div v-if="topLinks.length" class="row q-col-gutter-sm">
      <div v-for="item in topLinks" :key="item.id" class="col-auto">
        <q-chip
          clickable
          outline
          color="primary"
          :icon="item.icon || 'link'"
          @click="openLink(item)"
        >
          {{ item.title }}
        </q-chip>
      </div>
    </div>

    <div v-else-if="loadingLinks" class="row justify-center q-mt-lg">
      <q-spinner-dots color="primary" size="28px" />
    </div>
  </q-page>
</template>

<style scoped>
.welcome-card {
  border-left: 3px solid var(--q-primary);
}

.section-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  font-weight: 600;
  color: #44506b;
  margin-bottom: 11px;
}

.body--dark .section-title {
  color: #b6c2d9;
}

.module-card {
  transition: transform 0.16s ease, box-shadow 0.16s ease;
}

.module-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 18px rgba(16, 42, 80, 0.09);
}
</style>
